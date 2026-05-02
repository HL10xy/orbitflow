from __future__ import annotations

from typing import Any

from agents.base import BaseAgent
from core.task import SubTask


class ArchitectAgent(BaseAgent):
    role = "architect"
    icon = "🏗️"

    async def run(self, sub_task: SubTask, dependencies: dict[str, str], memory: Any) -> str:
        context = self._build_context(sub_task, dependencies, memory)
        context += "\n\nFocus on: architecture decisions, component boundaries, data flow, and technology choices. Output structured markdown."
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": context},
        ]
        result = await self._llm_call(messages)
        memory.write(f"agent:{self.role}", result, sub_task_id=sub_task.id)
        return result
