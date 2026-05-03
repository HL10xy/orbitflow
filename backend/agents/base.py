from __future__ import annotations

from abc import ABC
from typing import Any

from core.llm import LLMClient
from core.task import SubTask


SYSTEM_PROMPTS: dict[str, str] = {
    "architect": """You are a Senior Software Architect. Your role is to analyze requirements and produce clear, detailed technical designs.

When given a task:
1. Identify core requirements and constraints
2. Propose architecture (components, data flow, technology choices)
3. List implementation steps in dependency order
4. Flag potential risks and trade-offs

Output your design as structured markdown with clear sections. Be specific — name files, functions, types, and data structures.""",

    "coder": """You are a Senior Software Engineer. Your role is to implement production-quality code based on architecture designs.

When given a task:
1. Review the architect's design thoroughly
2. Write clean, idiomatic code with proper error handling
3. Follow the project's conventions and patterns
4. Include brief comments only where the logic is non-obvious

Output the complete implementation with file paths. Never output placeholder or pseudo-code.""",

    "reviewer": """You are a Code Reviewer. Your role is to review code for correctness, security, performance, and maintainability.

When given code to review:
1. Check for logical errors and edge cases
2. Identify security vulnerabilities (OWASP Top 10)
3. Assess performance implications
4. Suggest improvements with concrete examples

Output a structured review: Summary, Critical Issues, Suggestions, Approved (yes/no).""",

    "tester": """You are a QA Engineer. Your role is to design and write comprehensive tests.

When given implementation code:
1. Identify all testable behaviors and edge cases
2. Write unit tests covering happy path, error cases, and boundaries
3. Write integration tests where components interact
4. Ensure tests are deterministic and isolated

Output complete test files that can be run directly.""",
}


MAX_DESCRIPTION_LENGTH = 10_000


def _sanitize_input(text: str, max_length: int = MAX_DESCRIPTION_LENGTH) -> str:
    """Truncate and strip control characters to mitigate prompt injection."""
    text = text[:max_length]
    # Strip control characters except newlines/tabs
    return "".join(ch for ch in text if ch in ("\n", "\t") or (ord(ch) >= 32))


class BaseAgent(ABC):
    """Base for all specialized agents."""

    role: str = "base"
    icon: str = "?"
    context_hint: str = ""

    def __init__(self, llm: LLMClient | None = None):
        self.llm = llm or LLMClient()
        self.system_prompt = SYSTEM_PROMPTS.get(self.role, "You are a helpful AI assistant.")

    async def run(
        self,
        sub_task: SubTask,
        dependencies: dict[str, str],
        memory: Any,
    ) -> str:
        """Execute the agent's logic on a sub-task."""
        context = self._build_context(sub_task, dependencies, memory)
        if self.context_hint:
            context += f"\n\n{self.context_hint}"
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": context},
        ]
        result = await self._llm_call(messages)
        memory.write(f"agent:{self.role}", result, sub_task_id=sub_task.id)
        return result

    async def _llm_call(self, messages: list[dict[str, str]]) -> str:
        resp = await self.llm.chat(messages)
        return self.llm.extract_content(resp)

    def _build_context(self, sub_task: SubTask, dependencies: dict[str, str], memory: Any) -> str:
        parts = [f"## Current Task\n{_sanitize_input(sub_task.description)}\n"]
        if dependencies:
            parts.append("## Dependency Results\n")
            for dep_id, dep_result in dependencies.items():
                parts.append(f"### Input from {dep_id}\n{_sanitize_input(dep_result)}\n")
        recent = memory.read_recent(10)
        if recent:
            parts.append("## Recent Agent Communications\n")
            for entry in recent:
                parts.append(f"[{entry.role}]: {entry.content[:300]}\n")
        return "\n".join(parts)
