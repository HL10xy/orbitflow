from __future__ import annotations

import json
from typing import Any, AsyncIterator

import httpx

from config import default_config as cfg


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

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        tools: list[dict] | None = None,
        temperature: float = 0.7,
    ) -> dict[str, Any]:
        """Send a chat completion request and return the parsed response."""
        payload = self._build_payload(messages, tools=tools, temperature=temperature)
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self._headers,
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        """Stream chat completion tokens."""
        payload = self._build_payload(messages, stream=True, temperature=temperature)
        async with httpx.AsyncClient(timeout=300) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=self._headers,
                json=payload,
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.startswith("data: ") and line != "data: [DONE]":
                        chunk = json.loads(line[6:])
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
