from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from agents.orchestrator import Orchestrator
from config import default_config as cfg
from core.llm import LLMClient
from core.task import TaskComplexity

app = FastAPI(
    title="OrbitFlow API",
    description="Multi-Agent Software Engineering Framework",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cfg.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global orchestrator for status queries; per-request instances for task execution
_orchestrator = Orchestrator()


def _check_api_key(x_api_key: str | None = Header(None)):
    """Simple API key guard for sensitive endpoints. Skipped if no key is configured."""
    if cfg.api_key and x_api_key != cfg.api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


class RunTaskRequest(BaseModel):
    description: str
    title: str = ""
    complexity: str = Field(default="moderate", pattern="^(simple|moderate|complex|epic)$")


class LLMConfigRequest(BaseModel):
    base_url: str = ""
    api_key: str = ""
    model: str = ""


@app.get("/health")
async def health():
    return {"status": "ok", "service": "OrbitFlow"}


@app.get("/status")
async def status():
    return _orchestrator.get_status()


@app.post("/task/run")
async def run_task(req: RunTaskRequest):
    """Run a task (non-streaming). Returns the completed task."""
    if not req.description.strip():
        raise HTTPException(status_code=400, detail="Description cannot be empty")
    complexity = TaskComplexity(req.complexity)
    orch = Orchestrator()
    try:
        task = await orch.run_sync(
            req.description,
            title=req.title,
            complexity=complexity,
        )
        return task.to_dict()
    finally:
        await orch.close()


@app.post("/config/llm")
async def configure_llm(req: LLMConfigRequest, x_api_key: str | None = Header(None)):
    """Update LLM configuration at runtime."""
    _check_api_key(x_api_key)
    new_llm = LLMClient(
        base_url=req.base_url or None,
        api_key=req.api_key or None,
        model=req.model or None,
    )
    _orchestrator.llm = new_llm
    for agent in _orchestrator.agents.values():
        agent.llm = new_llm
    return {"status": "ok", "llm": new_llm.usage_info}


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    """WebSocket endpoint for real-time agent collaboration streaming."""
    # Simple API key check via query param
    if cfg.api_key:
        token = ws.query_params.get("token")
        if token != cfg.api_key:
            await ws.close(code=4001, reason="Unauthorized")
            return

    await ws.accept()
    try:
        while True:
            data = await ws.receive_text()
            try:
                msg = json.loads(data)
            except json.JSONDecodeError:
                await ws.send_json({"event_type": "error", "message": "Invalid JSON"})
                continue

            if not isinstance(msg, dict):
                await ws.send_json({"event_type": "error", "message": "Expected a JSON object"})
                continue

            action = msg.get("action")
            if not action:
                await ws.send_json({"event_type": "error", "message": "Missing 'action' field"})
                continue

            if action == "run":
                description = msg.get("description", "").strip()
                if not description:
                    await ws.send_json({"event_type": "error", "message": "Description cannot be empty"})
                    continue
                complexity = TaskComplexity(msg.get("complexity", "moderate"))
                orch = Orchestrator()
                try:
                    async for event in orch.run(
                        description,
                        title=msg.get("title", ""),
                        complexity=complexity,
                        stream=True,
                    ):
                        await ws.send_json(event.to_dict())
                    await ws.send_json({"event_type": "done"})
                except Exception as exc:
                    await ws.send_json({"event_type": "error", "message": str(exc)})
                finally:
                    await orch.close()

            elif action == "status":
                await ws.send_json(_orchestrator.get_status())

            elif action == "configure":
                if cfg.api_key:
                    token = msg.get("api_key")
                    if token != cfg.api_key:
                        await ws.send_json({"event_type": "error", "message": "Unauthorized"})
                        continue
                try:
                    new_llm = LLMClient(
                        base_url=msg.get("base_url") or None,
                        api_key=msg.get("api_key") or None,
                        model=msg.get("model") or None,
                    )
                    _orchestrator.llm = new_llm
                    for agent in _orchestrator.agents.values():
                        agent.llm = new_llm
                    await ws.send_json({"event_type": "config_updated", "llm": new_llm.usage_info})
                except Exception as exc:
                    await ws.send_json({"event_type": "error", "message": str(exc)})

            else:
                await ws.send_json({"event_type": "error", "message": f"Unknown action: {action}"})

    except WebSocketDisconnect:
        pass
