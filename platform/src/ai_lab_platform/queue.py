"""Non-authoritative queue. Redis in production; memory for tests."""

from __future__ import annotations

from collections import deque


class MemoryQueue:
    def __init__(self) -> None:
        self._items: deque[str] = deque()

    def enqueue(self, order_id: str) -> None:
        self._items.append(order_id)

    def dequeue(self) -> str | None:
        if not self._items:
            return None
        return self._items.popleft()

    def __len__(self) -> int:
        return len(self._items)
