from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, AsyncIterator

import httpx

from config import default_config as cfg

logger = logging.getLogger(__name__)


class LLMClient:
    """OpenAI-compatible LLM client — pluggable for MiMo, OpenAI, or any provider."""

    def __init__(
        self,
        base_url: str = "",
        api_key: str = "",
        model: str = "",
        max_tokens: int = 0,
    ):
        self.base_url = base_url or cfg.llm_base_url
        self.api_key = api_key or cfg.llm_api_key
        self.model = model or cfg.llm_model
        self.max_tokens = max_tokens or cfg.agent_max_tokens

        if self.api_key == "your-api-key-here":
            logger.warning("LLM_API_KEY is set to the default placeholder; LLM calls will fail")

        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(120, read=300),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=5),
        )

    async def close(self):
        await self._client.aclose()

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _build_payload(
        self,
        messages: list[dict[str, str]],
        *,
        stream: bool = False,
        tools: list[dict] | None = None,
        temperature: float = 0.7,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": temperature,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        if stream:
            payload["stream"] = True
        return payload

    async def _request_with_retry(self, make_request, max_retries: int = 3):
        """Execute an HTTP request with exponential backoff on transient errors."""
        for attempt in range(max_retries):
            try:
                return await make_request()
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code in (429, 500, 502, 503) and attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise
            except httpx.TransportError:
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        tools: list[dict] | None = None,
        temperature: float = 0.7,
    ) -> dict[str, Any]:
        """Send a chat completion request and return the parsed response."""
        payload = self._build_payload(messages, tools=tools, temperature=temperature)

        async def do_request():
            resp = await self._client.post(
                f"{self.base_url}/chat/completions",
                headers=self._headers,
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()

        return await self._request_with_retry(do_request)

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        """Stream chat completion tokens."""
        payload = self._build_payload(messages, stream=True, temperature=temperature)

        async def do_request():
            resp = await self._client.send(
                self._client.build_request(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    headers=self._headers,
                    json=payload,
                ),
                stream=True,
            )
            resp.raise_for_status()
            return resp

        resp = await self._request_with_retry(do_request)
        async with resp:
            async for line in resp.aiter_lines():
                if line.startswith("data: ") and line != "data: [DONE]":
                    try:
                        chunk = json.loads(line[6:])
                    except json.JSONDecodeError:
                        continue
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    if content := delta.get("content"):
                        yield content

    def extract_content(self, response: dict[str, Any]) -> str:
        """Extract text content from a chat completion response."""
        try:
            return response["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            return ""

    def extract_tool_calls(self, response: dict[str, Any]) -> list[dict]:
        """Extract tool calls from a chat completion response."""
        try:
            return response["choices"][0]["message"].get("tool_calls", [])
        except (KeyError, IndexError):
            return []

    @property
    def usage_info(self) -> str:
        return f"model={self.model}, base_url={self.base_url}"
