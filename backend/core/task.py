from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TaskStatus(str, Enum):
    PENDING = "pending"
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    REVIEWING = "reviewing"
    TESTING = "testing"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskComplexity(str, Enum):
    SIMPLE = "simple"  # single agent, single step
    MODERATE = "moderate"  # 2-3 agents, sequential
    COMPLEX = "complex"  # all agents, iterative refinement
    EPIC = "epic"  # full pipeline with parallel sub-tasks


@dataclass
class SubTask:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    description: str = ""
    assigned_agent: str = ""  # agent role name
    status: TaskStatus = TaskStatus.PENDING
    result: str = ""
    dependencies: list[str] = field(default_factory=list)  # sub-task ids
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "assigned_agent": self.assigned_agent,
            "status": self.status.value,
            "result": self.result[:200] if self.result else "",
            "dependencies": self.dependencies,
        }


@dataclass
class Task:
    """A software engineering task decomposed into sub-tasks for multi-agent execution."""

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = ""
    description: str = ""
    complexity: TaskComplexity = TaskComplexity.MODERATE
    status: TaskStatus = TaskStatus.PENDING
    sub_tasks: list[SubTask] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def decompose_plan(description: str, complexity: TaskComplexity) -> list[SubTask]:
        """Decompose a task description into a plan based on complexity.

        This is a heuristic decomposition; the Orchestrator can override it
        via LLM-driven planning for complex tasks.
        """
        if complexity == TaskComplexity.SIMPLE:
            return [
                SubTask(description="Analyze requirements", assigned_agent="architect"),
                SubTask(
                    description=f"Implement: {description}",
                    assigned_agent="coder",
                    dependencies=["0"],
                ),
            ]
        elif complexity == TaskComplexity.MODERATE:
            return [
                SubTask(description="Analyze requirements and design solution", assigned_agent="architect"),
                SubTask(
                    description=f"Implement core logic: {description}",
                    assigned_agent="coder",
                    dependencies=["0"],
                ),
                SubTask(
                    description="Review code for correctness and style",
                    assigned_agent="reviewer",
                    dependencies=["1"],
                ),
                SubTask(
                    description="Generate and run tests",
                    assigned_agent="tester",
                    dependencies=["1"],
                ),
            ]
        else:  # COMPLEX or EPIC
            return [
                SubTask(description="System design and architecture planning", assigned_agent="architect"),
                SubTask(
                    description="Implement module A (core logic)",
                    assigned_agent="coder",
                    dependencies=["0"],
                ),
                SubTask(
                    description="Implement module B (integration layer)",
                    assigned_agent="coder",
                    dependencies=["0"],
                ),
                SubTask(
                    description="Review module A",
                    assigned_agent="reviewer",
                    dependencies=["1"],
                ),
                SubTask(
                    description="Review module B",
                    assigned_agent="reviewer",
                    dependencies=["2"],
                ),
                SubTask(
                    description="Integration tests for A + B",
                    assigned_agent="tester",
                    dependencies=["3", "4"],
                ),
                SubTask(
                    description="End-to-end validation and performance check",
                    assigned_agent="tester",
                    dependencies=["5"],
                ),
            ]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "complexity": self.complexity.value,
            "status": self.status.value,
            "sub_tasks": [st.to_dict() for st in self.sub_tasks],
        }
