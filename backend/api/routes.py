from __future__ import annotations

import asyncio
import hmac
import ipaddress
import json
import logging
import time
from collections import deque
from contextlib import asynccontextmanager
from typing import Any
from urllib.parse import urlparse

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from agents.base import _sanitize_input
from agents.orchestrator import Orchestrator
from config import default_config as cfg
from core.llm import LLMClient
from core.task import TaskComplexity

logger = logging.getLogger(__name__)

_orchestrator = Orchestrator()
_orch_lock = asyncio.Lock()


def _validate_base_url(url: str) -> str:
    """Validate base_url to prevent SSRF to internal services."""
    parsed = urlparse(url)
    if parsed.scheme not in ("https", "http"):
        raise ValueError("base_url must use http or https scheme")
    hostname = (parsed.hostname or "").strip("[]")
    # Try to parse as IP address
    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            raise ValueError("base_url cannot point to private/loopback/link-local addresses")
        return url
    except ValueError as exc:
        if "cannot point to" in str(exc):
            raise
    # Hostname is a domain — block known loopback aliases
    if hostname in ("localhost",):
        raise ValueError("base_url cannot point to localhost")
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
    await ws.accept()

    # Authenticate via first message if API key is configured
    authenticated = not cfg.api_key
    if not authenticated:
        try:
            first_msg = await asyncio.wait_for(ws.receive_text(), timeout=10)
            data = json.loads(first_msg)
            token = data.get("token", "") if isinstance(data, dict) else ""
            if not (token and hmac.compare_digest(token, cfg.api_key)):
                await ws.send_json({"event_type": "error", "message": "Unauthorized"})
                await ws.close(code=4001, reason="Unauthorized")
                return
            authenticated = True
        except (json.JSONDecodeError, asyncio.TimeoutError):
            await ws.send_json({"event_type": "error", "message": "Expected auth message as first frame"})
            await ws.close(code=4001, reason="Unauthorized")
            return

    # Rate limiting state
    msg_timestamps: deque[float] = deque()
    rate_limit = cfg.ws_rate_limit

    def _check_rate_limit():
        now = time.monotonic()
        while msg_timestamps and now - msg_timestamps[0] > 1.0:
            msg_timestamps.popleft()
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
                        _sanitize_input(description),
                        title=_sanitize_input(msg.get("title", ""), 200),
                        complexity=complexity,
                        stream=True,
                    ):
                        await ws.send_json(event.to_dict())
                    await ws.send_json({"event_type": "done"})
                except Exception as exc:
                    logger.exception("WS run action failed")
                    await ws.send_json({"event_type": "error", "message": "Internal error during task execution"})
                finally:
                    await orch.close()

            elif action == "status":
                await ws.send_json(_orchestrator.get_status())

            else:
                await ws.send_json({"event_type": "error", "message": f"Unknown action: {action}"})

    except WebSocketDisconnect:
        pass
