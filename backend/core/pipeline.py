from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Callable

from core.task import Task, TaskStatus, SubTask


@dataclass
class PipelineEvent:
    """Emitted during pipeline execution for real-time monitoring."""

    event_type: str  # "task_start" | "task_end" | "agent_start" | "agent_end" | "log"
    task_id: str = ""
    sub_task_id: str = ""
    agent: str = ""
    message: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type,
            "task_id": self.task_id,
            "sub_task_id": self.sub_task_id,
            "agent": self.agent,
            "message": self.message,
            "timestamp": self.timestamp,
        }


class Pipeline:
    """Executes a Task through the multi-agent pipeline.

    The pipeline resolves sub-task dependencies, invokes the appropriate
    agents, and emits real-time events for the WebSocket layer.
    """

    def __init__(self):
        self._listeners: list[Callable[[PipelineEvent], Any]] = []

    def on_event(self, listener: Callable[[PipelineEvent], Any]):
        self._listeners.append(listener)

    async def _emit(self, event: PipelineEvent):
        for listener in self._listeners:
            if asyncio.iscoroutinefunction(listener):
                await listener(event)
            else:
                listener(event)

    async def execute(
        self,
        task: Task,
        agent_registry: dict[str, Any],
        memory: Any,
        event_stream: Callable[[PipelineEvent], Any] | None = None,
    ) -> Task:
        """Run a task through the pipeline, respecting sub-task dependencies."""
        task.status = TaskStatus.IN_PROGRESS
        await self._emit(PipelineEvent(
            event_type="task_start", task_id=task.id,
            message=f"Starting task: {task.title}",
        ))

        completed: dict[str, str] = {}  # sub_task_id -> result

        for sub_task in task.sub_tasks:
            # Wait for dependencies
            for dep_id in sub_task.dependencies:
                while dep_id not in completed:
                    await asyncio.sleep(0.1)

            sub_task.status = TaskStatus.IN_PROGRESS
            agent = agent_registry.get(sub_task.assigned_agent)
            if agent is None:
                sub_task.status = TaskStatus.FAILED
                sub_task.result = f"No agent found for role: {sub_task.assigned_agent}"
                continue

            await self._emit(PipelineEvent(
                event_type="agent_start",
                task_id=task.id,
                sub_task_id=sub_task.id,
                agent=sub_task.assigned_agent,
                message=f"Agent '{sub_task.assigned_agent}' starting: {sub_task.description}",
            ))

            # Gather dependency results as context
            dep_results = {dep_id: completed[dep_id] for dep_id in sub_task.dependencies}

            try:
                result = await agent.run(sub_task, dep_results, memory)
                sub_task.result = result
                sub_task.status = TaskStatus.COMPLETED
                completed[sub_task.id] = result

                await self._emit(PipelineEvent(
                    event_type="agent_end",
                    task_id=task.id,
                    sub_task_id=sub_task.id,
                    agent=sub_task.assigned_agent,
                    message=f"Agent '{sub_task.assigned_agent}' completed",
                ))
            except Exception as exc:
                sub_task.result = str(exc)
                sub_task.status = TaskStatus.FAILED
                await self._emit(PipelineEvent(
                    event_type="log",
                    task_id=task.id,
                    sub_task_id=sub_task.id,
                    agent=sub_task.assigned_agent,
                    message=f"Agent '{sub_task.assigned_agent}' failed: {exc}",
                ))

        task.status = TaskStatus.COMPLETED
        await self._emit(PipelineEvent(
            event_type="task_end", task_id=task.id,
            message=f"Task completed: {task.title}",
        ))
        return task
