from __future__ import annotations

import asyncio
import hmac
import json
import time
from contextlib import asynccontextmanager
from typing import Any
from urllib.parse import urlparse

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from agents.orchestrator import Orchestrator
from config import default_config as cfg
from core.llm import LLMClient
from core.task import TaskComplexity

_orchestrator = Orchestrator()
_orch_lock = asyncio.Lock()


def _validate_base_url(url: str) -> str:
    """Validate base_url to prevent SSRF to internal services."""
    parsed = urlparse(url)
    if parsed.scheme not in ("https", "http"):
        raise ValueError("base_url must use http or https scheme")
    hostname = parsed.hostname or ""
    # Block private/link-local addresses
    if hostname in ("localhost", "127.0.0.1", "0.0.0.0", "::1"):
        return url
    if hostname.startswith("10.") or hostname.startswith("192.168.") or hostname.startswith("172."):
        raise ValueError("base_url cannot point to private network addresses")
    if hostname.startswith("169.254."):
        raise ValueError("base_url cannot point to link-local addresses")
    return url


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await _orchestrator.close()


app = FastAPI(
    title="OrbitFlow API",
    description="Multi-Agent Software Engineering Framework",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cfg.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _check_api_key(x_api_key: str | None = Header(None)):
    """Timing-attack-safe API key guard. Skipped if no key is configured."""
    if cfg.api_key and not (x_api_key and hmac.compare_digest(x_api_key, cfg.api_key)):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


class RunTaskRequest(BaseModel):
    description: str = Field(..., max_length=10_000)
    title: str = Field(default="", max_length=200)
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
async def run_task(req: RunTaskRequest, x_api_key: str | None = Header(None)):
    """Run a task (non-streaming). Returns the completed task."""
    _check_api_key(x_api_key)
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
    if req.base_url:
        try:
            _validate_base_url(req.base_url)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
    async with _orch_lock:
        old_llm = _orchestrator.llm
        new_llm = LLMClient(
            base_url=req.base_url or None,
            api_key=req.api_key or None,
            model=req.model or None,
        )
        _orchestrator.llm = new_llm
        for agent in _orchestrator.agents.values():
            agent.llm = new_llm
        await old_llm.close()
    return {"status": "ok", "llm": new_llm.usage_info}


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    """WebSocket endpoint for real-time agent collaboration streaming."""
    if cfg.api_key:
        token = ws.query_params.get("token")
        if not (token and hmac.compare_digest(token, cfg.api_key)):
            await ws.close(code=4001, reason="Unauthorized")
            return

    await ws.accept()

    # Rate limiting state
    msg_timestamps: list[float] = []
    rate_limit = cfg.ws_rate_limit

    def _check_rate_limit():
        now = time.monotonic()
        # Remove timestamps older than 1 second
        while msg_timestamps and now - msg_timestamps[0] > 1.0:
            msg_timestamps.pop(0)
        if len(msg_timestamps) >= rate_limit:
            return False
        msg_timestamps.append(now)
        return True

    try:
        while True:
            data = await ws.receive_text()

            if not _check_rate_limit():
                await ws.send_json({"event_type": "error", "message": "Rate limit exceeded"})
                continue

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
                if len(description) > 10_000:
                    await ws.send_json({"event_type": "error", "message": "Description too long (max 10000 chars)"})
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

            else:
                await ws.send_json({"event_type": "error", "message": f"Unknown action: {action}"})

    except WebSocketDisconnect:
        pass
