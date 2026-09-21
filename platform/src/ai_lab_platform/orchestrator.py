"""Orchestrator: intake, queue, recovery. Postgres/Redis not required for unit tests."""

from __future__ import annotations

from .approvals import requires_approval
from .queue import MemoryQueue
from .state_machine import IllegalTransition
from .store import SqliteStore
from .work_order import Attempt, Status, WorkOrder, utcnow


class Orchestrator:
    def __init__(self, store: SqliteStore, queue: MemoryQueue | None = None) -> None:
        self.store = store
        self.queue = queue or MemoryQueue()

    def submit(self, order: WorkOrder) -> WorkOrder:
        if order.status != Status.CREATED:
            raise IllegalTransition("submit requires status=created")
        self.store.put(order)
        order = self.store.set_status(order.id, Status.QUEUED)
        self.queue.enqueue(order.id)
        self.store.append_audit(order.id, "harness", "submitted", {"agent": order.agent})
        return order

    def hydrate_queue(self) -> int:
        """Load queued ids from the durable store. Call once on process start."""
        count = 0
        for order in self.store.list(Status.QUEUED):
            self.queue.enqueue(order.id)
            count += 1
        return count

    def start_next(self) -> WorkOrder | None:
        while True:
            order_id = self.queue.dequeue()
            if order_id is None:
                return None
            order = self.store.get(order_id)
            if order is None or order.status != Status.QUEUED:
                continue
            order = self.store.set_status(order.id, Status.RUNNING)
            attempt = Attempt(index=len(order.attempt_history) + 1, started_at=utcnow())
            order.attempt_history.append(attempt)
            self.store.put(order)
            return order

    def request_tool(self, order_id: str, tool: str, approved: set[str] | None = None) -> WorkOrder:
        order = self.store.get(order_id)
        if order is None:
            raise KeyError(order_id)
        if requires_approval(tool, order.allowed_tools, approved or set()):
            return self.store.set_status(order.id, Status.AWAITING_APPROVAL)
        return order

    def approve(self, order_id: str, tools: list[str] | None = None) -> WorkOrder:
        order = self.store.get(order_id)
        if order is None:
            raise KeyError(order_id)
        if tools:
            merged = list(dict.fromkeys([*order.approved_tools, *tools]))
            order.approved_tools = merged
            self.store.put(order)
        order = self.store.set_status(order_id, Status.QUEUED)
        self.queue.enqueue(order.id)
        self.store.append_audit(order.id, "human", "approved", {"tools": tools or []})
        return order

    def cancel(self, order_id: str) -> WorkOrder:
        return self.store.set_status(order_id, Status.CANCELLED)

    def complete(self, order_id: str, result: str) -> WorkOrder:
        order = self.store.get(order_id)
        if order is None:
            raise KeyError(order_id)
        if order.attempt_history:
            order.attempt_history[-1].ended_at = utcnow()
        order.final_result = result
        self.store.put(order)
        done = self.store.set_status(order.id, Status.COMPLETED)
        self.store.append_audit(order.id, "harness", "completed", {})
        return done

    def fail(self, order_id: str, error: str) -> WorkOrder:
        order = self.store.get(order_id)
        if order is None:
            raise KeyError(order_id)
        if order.attempt_history:
            order.attempt_history[-1].ended_at = utcnow()
            order.attempt_history[-1].error = error
        attempts = len(order.attempt_history)
        self.store.put(order)
        order = self.store.set_status(order.id, Status.FAILED)
        self.store.append_audit(order.id, "harness", "failed", {"error": error, "attempts": attempts})
        if attempts < order.execution_policy.max_attempts:
            order = self.store.set_status(order.id, Status.QUEUED)
            self.queue.enqueue(order.id)
        return order

    def recover_running(self) -> list[WorkOrder]:
        """After a process restart: running jobs are not lost (store is durable)."""
        recovered: list[WorkOrder] = []
        for order in self.store.list(Status.RUNNING):
            if order.execution_policy.retry_on_interrupt:
                order = self.fail(order.id, "interrupted by restart")
            else:
                order = self.store.set_status(order.id, Status.FAILED)
            recovered.append(order)
        return recovered
