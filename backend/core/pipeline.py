from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from core.task import Task, TaskStatus, SubTask

logger = logging.getLogger(__name__)


@dataclass
class PipelineEvent:
    """Emitted during pipeline execution for real-time monitoring."""

    event_type: str  # "task_start" | "task_end" | "agent_start" | "agent_end" | "agent_failed" | "log"
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
    """Executes a Task through the multi-agent pipeline with parallel DAG scheduling."""

    def __init__(self):
        self._listeners: list[Callable[[PipelineEvent], Any]] = []

    def on_event(self, listener: Callable[[PipelineEvent], Any]):
        self._listeners.append(listener)

    def clear_listeners(self):
        self._listeners.clear()

    def remove_listener(self, listener: Callable[[PipelineEvent], Any]):
        self._listeners = [l for l in self._listeners if l is not listener]

    async def _emit(self, event: PipelineEvent):
        for listener in self._listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(event)
                else:
                    listener(event)
            except Exception:
                logger.exception("Listener error during event emission")
                raise

    async def _run_subtask(
        self,
        sub_task: SubTask,
        task: Task,
        agent_registry: dict[str, Any],
        memory: Any,
        completed: dict[str, str],
        failed: set[str],
        events: dict[str, asyncio.Event],
    ) -> None:
        """Execute a single sub-task after its dependencies are met."""
        for dep_id in sub_task.dependencies:
            if dep_id in events:
                await events[dep_id].wait()

        failed_deps = [dep_id for dep_id in sub_task.dependencies if dep_id in failed]
        if failed_deps:
            sub_task.status = TaskStatus.FAILED
            sub_task.result = f"Skipped: dependency {failed_deps[0]} failed"
            failed.add(sub_task.id)
            await self._emit(PipelineEvent(
                event_type="log",
                task_id=task.id,
                sub_task_id=sub_task.id,
                agent=sub_task.assigned_agent,
                message=f"Skipping '{sub_task.assigned_agent}': dependency failed",
            ))
            events[sub_task.id].set()
            return

        sub_task.status = TaskStatus.IN_PROGRESS
        agent = agent_registry.get(sub_task.assigned_agent)
        if agent is None:
            sub_task.status = TaskStatus.FAILED
            sub_task.result = f"No agent found for role: {sub_task.assigned_agent}"
            failed.add(sub_task.id)
            events[sub_task.id].set()
            return

        await self._emit(PipelineEvent(
            event_type="agent_start",
            task_id=task.id,
            sub_task_id=sub_task.id,
            agent=sub_task.assigned_agent,
            message=f"Agent '{sub_task.assigned_agent}' starting: {sub_task.description}",
        ))

        dep_results = {dep_id: completed[dep_id] for dep_id in sub_task.dependencies if dep_id in completed}

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
            logger.exception("Agent '%s' failed on sub-task %s", sub_task.assigned_agent, sub_task.id)
            sub_task.result = str(exc)
            sub_task.status = TaskStatus.FAILED
            failed.add(sub_task.id)
            await self._emit(PipelineEvent(
                event_type="agent_failed",
                task_id=task.id,
                sub_task_id=sub_task.id,
                agent=sub_task.assigned_agent,
                message=f"Agent '{sub_task.assigned_agent}' failed: {exc}",
            ))
        finally:
            events[sub_task.id].set()

    async def execute(
        self,
        task: Task,
        agent_registry: dict[str, Any],
        memory: Any,
    ) -> Task:
        """Run a task through the pipeline with parallel DAG scheduling.

        Sub-tasks with no unmet dependencies run concurrently.
        Failed sub-tasks cause their dependents to be skipped.
        """
        task.status = TaskStatus.IN_PROGRESS
        await self._emit(PipelineEvent(
            event_type="task_start", task_id=task.id,
            message=f"Starting task: {task.title}",
        ))

        completed: dict[str, str] = {}
        failed: set[str] = set()
        events: dict[str, asyncio.Event] = {st.id: asyncio.Event() for st in task.sub_tasks}

        coros = [
            self._run_subtask(sub_task, task, agent_registry, memory, completed, failed, events)
            for sub_task in task.sub_tasks
        ]
        await asyncio.gather(*coros)

        if any(st.status == TaskStatus.FAILED for st in task.sub_tasks):
            task.status = TaskStatus.FAILED
            msg = f"Task failed: {task.title}"
        else:
            task.status = TaskStatus.COMPLETED
            msg = f"Task completed: {task.title}"

        await self._emit(PipelineEvent(
            event_type="task_end", task_id=task.id, message=msg,
        ))
        return task
