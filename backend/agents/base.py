from __future__ import annotations

import json
from abc import ABC, abstractmethod
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


class BaseAgent(ABC):
    """Abstract base for all specialized agents."""

    role: str = "base"
    icon: str = "?"

    def __init__(self, llm: LLMClient | None = None):
        self.llm = llm or LLMClient()
        self.system_prompt = SYSTEM_PROMPTS.get(self.role, "You are a helpful AI assistant.")

    @abstractmethod
    async def run(
        self,
        sub_task: SubTask,
        dependencies: dict[str, str],
        memory: Any,
    ) -> str:
        """Execute the agent's logic on a sub-task.

        Args:
            sub_task: The sub-task to execute.
            dependencies: Map of completed dependency sub-task IDs -> results.
            memory: SharedMemory instance for inter-agent context.

        Returns:
            The agent's output as a string.
        """
        ...

    async def _llm_call(self, messages: list[dict[str, str]]) -> str:
        """Convenience wrapper around LLM chat."""
        resp = await self.llm.chat(messages)
        return self.llm.extract_content(resp)

    def _build_context(self, sub_task: SubTask, dependencies: dict[str, str], memory: Any) -> str:
        """Build a context string from dependency results and memory."""
        parts = [f"## Current Task\n{sub_task.description}\n"]
        if dependencies:
            parts.append("## Dependency Results\n")
            for dep_id, dep_result in dependencies.items():
                parts.append(f"### Input from {dep_id}\n{dep_result}\n")
        recent = memory.read_all()[-10:]
        if recent:
            parts.append("## Recent Agent Communications\n")
            for entry in recent:
                parts.append(f"[{entry.role}]: {entry.content[:300]}\n")
        return "\n".join(parts)
