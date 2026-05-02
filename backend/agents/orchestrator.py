from __future__ import annotations

import asyncio
from typing import Any, AsyncIterator

from agents.architect import ArchitectAgent
from agents.base import BaseAgent
from agents.coder import CoderAgent
from agents.reviewer import ReviewerAgent
from agents.tester import TesterAgent
from core.llm import LLMClient
from core.memory import SharedMemory
from core.pipeline import Pipeline, PipelineEvent
from core.task import Task, TaskComplexity, TaskStatus


class Orchestrator:
    """Central coordinator for multi-agent software engineering.

    The Orchestrator manages the lifecycle of a task:
    1. Decomposes the task into sub-tasks based on complexity
    2. Assigns sub-tasks to specialized agents
    3. Runs the pipeline respecting dependencies
    4. Emits real-time events for monitoring

    Usage:
        orchestrator = Orchestrator()
        async for event in orchestrator.run("Build a REST API"):
            print(event.message)
    """

    def __init__(self, llm: LLMClient | None = None):
        self.llm = llm or LLMClient()
        self.agents: dict[str, BaseAgent] = {
            "architect": ArchitectAgent(self.llm),
            "coder": CoderAgent(self.llm),
            "reviewer": ReviewerAgent(self.llm),
            "tester": TesterAgent(self.llm),
        }
        self.memory = SharedMemory()
        self.pipeline = Pipeline()
        self.current_task: Task | None = None

    async def run(
        self,
        description: str,
        *,
        complexity: TaskComplexity = TaskComplexity.MODERATE,
        title: str = "",
        context: dict[str, Any] | None = None,
        stream: bool = True,
    ) -> AsyncIterator[PipelineEvent]:
        """Run a task through the multi-agent pipeline.

        Args:
            description: The task description.
            complexity: Task complexity level.
            title: Optional task title.
            context: Optional additional context.
            stream: If True, yields events in real-time as the pipeline runs.

        Yields:
            PipelineEvent objects for real-time monitoring.
        """
        task = Task(
            title=title or description[:80],
            description=description,
            complexity=complexity,
            context=context or {},
        )
        task.sub_tasks = Task.decompose_plan(description, complexity)
        self.current_task = task

        # Build event queue for streaming
        event_queue: asyncio.Queue[PipelineEvent | None] = asyncio.Queue()

        async def collect(event: PipelineEvent):
            await event_queue.put(event)

        self.pipeline.on_event(collect)

        # Run pipeline in background
        pipeline_task = asyncio.create_task(
            self.pipeline.execute(task, self.agents, self.memory)
        )

        # Stream events as they arrive
        while True:
            event = await event_queue.get()
            if event is None:
                break
            yield event
            if event.event_type == "task_end":
                # Pipeline is done, signal completion
                await event_queue.put(None)
                break

        await pipeline_task
        self.current_task = task

    async def run_sync(self, description: str, **kwargs) -> Task:
        """Run a task and return the completed Task (non-streaming)."""
        task = Task(
            title=kwargs.get("title", description[:80]),
            description=description,
            complexity=kwargs.get("complexity", TaskComplexity.MODERATE),
        )
        task.sub_tasks = Task.decompose_plan(description, task.complexity)
        self.current_task = task

        events: list[PipelineEvent] = []

        def collect(event: PipelineEvent):
            events.append(event)

        self.pipeline.on_event(collect)
        try:
            return await self.pipeline.execute(task, self.agents, self.memory)
        finally:
            self.pipeline._listeners.remove(collect)

    def get_status(self) -> dict[str, Any]:
        """Return current orchestrator status."""
        return {
            "agents": list(self.agents.keys()),
            "memory": self.memory.snapshot(),
            "current_task": self.current_task.to_dict() if self.current_task else None,
            "llm": self.llm.usage_info,
        }
