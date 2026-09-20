"""Explicit work-order state machine."""

from __future__ import annotations

from .work_order import Status, TERMINAL

ALLOWED: dict[Status, frozenset[Status]] = {
    Status.CREATED: frozenset({Status.QUEUED, Status.CANCELLED}),
    Status.QUEUED: frozenset({Status.RUNNING, Status.CANCELLED}),
    Status.RUNNING: frozenset(
        {Status.AWAITING_APPROVAL, Status.COMPLETED, Status.FAILED, Status.QUEUED, Status.CANCELLED}
    ),
    Status.AWAITING_APPROVAL: frozenset(
        {Status.RUNNING, Status.QUEUED, Status.CANCELLED, Status.FAILED}
    ),
    Status.FAILED: frozenset({Status.QUEUED, Status.CANCELLED}),
    Status.COMPLETED: frozenset(),
    Status.CANCELLED: frozenset(),
}


class IllegalTransition(ValueError):
    pass


def can_transition(current: Status, target: Status) -> bool:
    if current in TERMINAL and current != Status.FAILED:
        return False
    return target in ALLOWED[current]


def transition(current: Status, target: Status) -> Status:
    if not can_transition(current, target):
        raise IllegalTransition(f"{current.value} -> {target.value} is not allowed")
    return target
