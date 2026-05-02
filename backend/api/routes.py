from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from agents.orchestrator import Orchestrator
from core.llm import LLMClient
from core.task import TaskComplexity

app = FastAPI(
    title="OrbitFlow API",
    description="Multi-Agent Software Engineering Framework",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = Orchestrator()


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
    return orchestrator.get_status()


@app.post("/task/run")
async def run_task(req: RunTaskRequest):
    """Run a task (non-streaming). Returns the completed task."""
    complexity = TaskComplexity(req.complexity)
    task = await orchestrator.run_sync(
        req.description,
        title=req.title,
        complexity=complexity,
    )
    return task.to_dict()


@app.post("/config/llm")
async def configure_llm(req: LLMConfigRequest):
    """Update LLM configuration at runtime."""
    new_llm = LLMClient(
        base_url=req.base_url or None,
        api_key=req.api_key or None,
        model=req.model or None,
    )
    orchestrator.llm = new_llm
    for agent in orchestrator.agents.values():
        agent.llm = new_llm
    return {"status": "ok", "llm": new_llm.usage_info}


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    """WebSocket endpoint for real-time agent collaboration streaming."""
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
                complexity = TaskComplexity(msg.get("complexity", "moderate"))
                try:
                    async for event in orchestrator.run(
                        msg.get("description", ""),
                        title=msg.get("title", ""),
                        complexity=complexity,
                        stream=True,
                    ):
                        await ws.send_json(event.to_dict())
                    await ws.send_json({"event_type": "done"})
                except Exception as exc:
                    await ws.send_json({"event_type": "error", "message": str(exc)})

            elif action == "status":
                await ws.send_json(orchestrator.get_status())

            elif action == "configure":
                try:
                    new_llm = LLMClient(
                        base_url=msg.get("base_url") or None,
                        api_key=msg.get("api_key") or None,
                        model=msg.get("model") or None,
                    )
                    orchestrator.llm = new_llm
                    for agent in orchestrator.agents.values():
                        agent.llm = new_llm
                    await ws.send_json({"event_type": "config_updated", "llm": new_llm.usage_info})
                except Exception as exc:
                    await ws.send_json({"event_type": "error", "message": str(exc)})

            else:
                await ws.send_json({"event_type": "error", "message": f"Unknown action: {action}"})

    except WebSocketDisconnect:
        pass
