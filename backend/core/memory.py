from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MemoryEntry:
    role: str  # "system" | "agent:{name}" | "tool"
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


class SharedMemory:
    """Shared memory for inter-agent communication.

    All agents read from and write to the same memory space, enabling
    true multi-agent collaboration. The memory enforces a configurable
    max size and supports context-window-aware truncation.

    Note: not thread-safe; safe for single-event-loop async use.
    """

    def __init__(self, max_entries: int = 200):
        self._entries: OrderedDict[int, MemoryEntry] = OrderedDict()
        self._counter = 0
        self.max_entries = max_entries

    def write(self, role: str, content: str, **metadata) -> int:
        """Write an entry and return its id."""
        self._counter += 1
        self._entries[self._counter] = MemoryEntry(
            role=role, content=content, metadata=metadata
        )
        self._evict()
        return self._counter

    def read(self, entry_id: int) -> MemoryEntry | None:
        return self._entries.get(entry_id)

    def read_all(self) -> list[MemoryEntry]:
        return list(self._entries.values())

    def read_by_role(self, role: str) -> list[MemoryEntry]:
        return [e for e in self._entries.values() if e.role == role]

    def to_messages(self, system_prompt: str = "") -> list[dict[str, str]]:
        """Convert memory entries to LLM-compatible messages.

        Agent entries become 'assistant' messages, tool entries become
        'user' messages, preserving the conversation flow.
        """
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        for entry in self._entries.values():
            if entry.role == "system":
                messages.append({"role": "system", "content": entry.content})
            elif entry.role.startswith("agent:"):
                agent_name = entry.role.split(":", 1)[1]
                messages.append({
                    "role": "assistant",
                    "content": f"[{agent_name}]: {entry.content}",
                })
            else:
                messages.append({"role": "user", "content": entry.content})
        return messages

    def snapshot(self) -> dict[str, Any]:
        """Return a JSON-serializable snapshot for the API."""
        return {
            "total_entries": len(self._entries),
            "entries": [
                {
                    "id": eid,
                    "role": entry.role,
                    "content": entry.content[:500],
                    "metadata": entry.metadata,
                }
                for eid, entry in self._entries.items()
            ],
        }

    def _evict(self):
        while len(self._entries) > self.max_entries:
            self._entries.popitem(last=False)

    def clear(self):
        self._entries.clear()
        self._counter = 0
