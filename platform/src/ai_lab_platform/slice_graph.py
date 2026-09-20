"""Vertical-slice LangGraph workflow.

LangGraph owns *steps and resume*. PostgreSQL (or SQLite in tests) owns the work-order
record. Dispatch, permissions, and approvals remain explicit nodes — not implicit graph magic.
"""

from __future__ import annotations

from typing import Any, NotRequired, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from .dispatch import DispatchFn, StudioUnavailable
from .store import WorkOrderStore
from .work_order import Status, utcnow


class SliceState(TypedDict):
    work_order_id: str
    objective: str
    agent: str
    studio_ok: bool
    studio_detail: str
    error: str
    approval: str
    plan_ok: NotRequired[bool]


def _set_status(store: WorkOrderStore, order_id: str, status: Status, **fields: Any) -> None:
    order = store.get(order_id)
    if order is None:
        raise KeyError(order_id)
    for key, value in fields.items():
        setattr(order, key, value)
    store.put(order)
    if order.status != status:
        store.set_status(order_id, status)


def build_slice_graph(store: WorkOrderStore, dispatch: DispatchFn, checkpointer: Any):
    def mark_running(state: SliceState) -> dict[str, Any]:
        order = store.get(state["work_order_id"])
        if order is None:
            raise KeyError(state["work_order_id"])
        if order.status == Status.QUEUED:
            store.set_status(order.id, Status.RUNNING)
        elif order.status == Status.CREATED:
            store.put(order)
            store.set_status(order.id, Status.QUEUED)
            store.set_status(order.id, Status.RUNNING)
        return {}

    def call_studio(state: SliceState) -> dict[str, Any]:
        order = store.get(state["work_order_id"])
        if order is None:
            raise KeyError(state["work_order_id"])
        try:
            result = dispatch(
                {
                    "work_order_id": order.id,
                    "objective": order.objective,
                    "agent": order.agent,
                    "bounded_scope": order.bounded_scope,
                    "allowed_tools": list(order.allowed_tools),
                    "approved_tools": list(order.approved_tools),
                }
            )
        except StudioUnavailable as exc:
            return {
                "studio_ok": False,
                "plan_ok": False,
                "studio_detail": "",
                "error": f"studio_unavailable: {exc}",
            }
        artifacts = result.get("artifacts") or []
        if artifacts:
            for item in artifacts:
                if item not in order.artifacts:
                    order.artifacts.append(item)
            store.put(order)
        plan_ok = bool(result.get("ok", True))
        detail = str(result.get("detail", result))
        return {
            "studio_ok": True,
            "plan_ok": plan_ok,
            "studio_detail": detail,
            "error": "" if plan_ok else f"plan_failed: {detail}",
        }

    def record_unavailable(state: SliceState) -> dict[str, Any]:
        order = store.get(state["work_order_id"])
        if order is None:
            raise KeyError(state["work_order_id"])
        order.log_refs.append("studio_unavailable")
        if order.attempt_history:
            order.attempt_history[-1].ended_at = utcnow()
            order.attempt_history[-1].error = state["error"]
        store.put(order)
        # Visible persistence: re-queue rather than delete.
        if order.status == Status.RUNNING:
            store.set_status(order.id, Status.QUEUED)
        return {}

    def record_failed(state: SliceState) -> dict[str, Any]:
        order = store.get(state["work_order_id"])
        if order is None:
            raise KeyError(state["work_order_id"])
        order.log_refs.append("plan_failed")
        order.final_result = state.get("error") or state.get("studio_detail") or "plan failed"
        store.put(order)
        if order.status == Status.RUNNING:
            store.set_status(order.id, Status.FAILED)
        return {}

    def await_approval(state: SliceState) -> dict[str, Any]:
        order = store.get(state["work_order_id"])
        if order is None:
            raise KeyError(state["work_order_id"])
        if order.status == Status.RUNNING:
            store.set_status(order.id, Status.AWAITING_APPROVAL)
        decision = interrupt(
            {
                "work_order_id": state["work_order_id"],
                "question": "approve studio worker result?",
                "studio_detail": state.get("studio_detail", ""),
            }
        )
        return {"approval": str(decision)}

    def finalize(state: SliceState) -> dict[str, Any]:
        approval = (state.get("approval") or "").lower()
        order = store.get(state["work_order_id"])
        if order is None:
            raise KeyError(state["work_order_id"])
        if approval in {"rejected", "deny", "denied", "false", "no"}:
            order.final_result = f"rejected: {state.get('studio_detail', '')}"
            store.put(order)
            if order.status == Status.AWAITING_APPROVAL:
                store.set_status(order.id, Status.FAILED)
            return {}
        order.final_result = state.get("studio_detail") or "completed"
        order.approved_tools = list(dict.fromkeys([*order.approved_tools, "studio_execute"]))
        store.put(order)
        if order.status == Status.AWAITING_APPROVAL:
            store.set_status(order.id, Status.RUNNING)
            store.set_status(order.id, Status.COMPLETED)
        elif order.status == Status.RUNNING:
            store.set_status(order.id, Status.COMPLETED)
        return {}

    def route_after_studio(state: SliceState) -> str:
        if not state.get("studio_ok"):
            return "record_unavailable"
        if not state.get("plan_ok", True):
            return "record_failed"
        return "await_approval"

    graph = StateGraph(SliceState)
    graph.add_node("mark_running", mark_running)
    graph.add_node("call_studio", call_studio)
    graph.add_node("record_unavailable", record_unavailable)
    graph.add_node("record_failed", record_failed)
    graph.add_node("await_approval", await_approval)
    graph.add_node("finalize", finalize)
    graph.add_edge(START, "mark_running")
    graph.add_edge("mark_running", "call_studio")
    graph.add_conditional_edges(
        "call_studio",
        route_after_studio,
        {
            "await_approval": "await_approval",
            "record_unavailable": "record_unavailable",
            "record_failed": "record_failed",
        },
    )
    graph.add_edge("record_unavailable", END)
    graph.add_edge("record_failed", END)
    graph.add_edge("await_approval", "finalize")
    graph.add_edge("finalize", END)
    return graph.compile(checkpointer=checkpointer)


def thread_config(work_order_id: str) -> dict[str, Any]:
    return {"configurable": {"thread_id": work_order_id}}
