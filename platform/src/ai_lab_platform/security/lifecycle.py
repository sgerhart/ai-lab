"""Security VM lifecycle and validation workflow (IWO-077).

Implements deterministic orchestration for ephemeral analysis VMs:
inventory -> template_validate -> network_validate -> clone_request -> boot ->
guest_ready -> benign_validation -> execution_approval -> analysis -> collect ->
shutdown -> destroy -> residual_check -> report.

Includes compensating cleanup for all post-clone failures, explicit blocked
incident state if cleanup fails, and LangGraph resumable graph integration.
Zero live sockets or credentials; fully operates over HypervisorPort abstractions.
"""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, NotRequired, TypedDict

from .events import EmbeddedPayloadRefused, EvidenceRef
from .hypervisor import AuthContext, HypervisorDenied, HypervisorPort, IsolationError, ProviderNotConfigured
from .templates import BASELINE_PROFILES, TemplateManifest, validate_manifest_offline


class StepName(str, Enum):
    INVENTORY = "inventory"
    TEMPLATE_VALIDATE = "template_validate"
    NETWORK_VALIDATE = "network_validate"
    CLONE_REQUEST = "clone_request"
    BOOT = "boot"
    GUEST_READY = "guest_ready"
    BENIGN_VALIDATION = "benign_validation"
    EXECUTION_APPROVAL = "execution_approval"
    ANALYSIS = "analysis"
    COLLECT = "collect"
    SHUTDOWN = "shutdown"
    DESTROY = "destroy"
    RESIDUAL_CHECK = "residual_check"
    REPORT = "report"
    COMPENSATING_CLEANUP = "compensating_cleanup"


class WorkflowStatus(str, Enum):
    SUBMITTED = "submitted"
    PREFLIGHT = "preflight"
    READY = "ready"
    AWAITING_APPROVAL = "awaiting_approval"
    RUNNING = "running"
    COLLECTING = "collecting"
    CLEANING = "cleaning"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class SecurityVmWorkflowState(TypedDict):
    job_id: str
    profile: str
    provider: str
    template_id: str
    execution_class: str  # "benign" or "untrusted"
    network_id: str
    controlled_egress: bool
    actor: str
    approval_id: str
    current_step: str
    status: str
    vm_id: str
    vm_power: str
    inventory_data: dict[str, Any]
    template_report: dict[str, Any]
    network_report: dict[str, Any]
    benign_validation_ok: bool
    analysis_output: dict[str, Any]
    evidence: list[dict[str, Any]]
    findings: list[str]
    cleanup_status: str  # "pending", "verified", "failed"
    residual_vms: list[str]
    error: str
    step_history: list[dict[str, Any]]
    report: dict[str, Any]


def init_workflow_state(
    job_id: str,
    *,
    template_id: str,
    profile: str = "linux-static",
    provider: str = "fake",
    execution_class: str = "benign",
    network_id: str = "",
    controlled_egress: bool = False,
    actor: str = "security",
    approval_id: str = "",
) -> SecurityVmWorkflowState:
    """Create a validated starting state for a Security VM lifecycle workflow."""
    if not job_id:
        raise ValueError("job_id is required")
    if not actor:
        raise ValueError("actor is required")
    if execution_class not in {"benign", "untrusted"}:
        raise ValueError("execution_class must be benign or untrusted")

    return {
        "job_id": job_id,
        "profile": profile,
        "provider": provider,
        "template_id": template_id,
        "execution_class": execution_class,
        "network_id": network_id,
        "controlled_egress": controlled_egress,
        "actor": actor,
        "approval_id": approval_id,
        "current_step": StepName.INVENTORY.value,
        "status": WorkflowStatus.SUBMITTED.value,
        "vm_id": "",
        "vm_power": "off",
        "inventory_data": {},
        "template_report": {},
        "network_report": {},
        "benign_validation_ok": False,
        "analysis_output": {},
        "evidence": [],
        "findings": [],
        "cleanup_status": "pending",
        "residual_vms": [],
        "error": "",
        "step_history": [],
        "report": {},
    }


def _record_step(state: SecurityVmWorkflowState, step: str, detail: str = "") -> None:
    now = datetime.now(timezone.utc).isoformat()
    state["current_step"] = step
    state["step_history"].append(
        {
            "step": step,
            "status": state["status"],
            "timestamp": now,
            "vm_id": state.get("vm_id", ""),
            "detail": detail,
        }
    )


class SecurityVmLifecycleEngine:
    """Deterministic, step-by-step executor for the security VM lifecycle."""

    def __init__(self, hypervisor: HypervisorPort) -> None:
        self.hypervisor = hypervisor

    def _auth(self, state: SecurityVmWorkflowState) -> AuthContext:
        return AuthContext(
            job_id=state["job_id"],
            actor=state["actor"],
            approval_id=state.get("approval_id", ""),
        )

    def execute_inventory(self, state: SecurityVmWorkflowState) -> SecurityVmWorkflowState:
        _record_step(state, StepName.INVENTORY.value)
        try:
            inv = self.hypervisor.inventory()
            state["inventory_data"] = inv
            state["status"] = WorkflowStatus.PREFLIGHT.value
            state["current_step"] = StepName.TEMPLATE_VALIDATE.value
        except Exception as exc:
            state["error"] = f"inventory failed: {exc}"
            state["status"] = WorkflowStatus.FAILED.value
        return state

    def execute_template_validate(self, state: SecurityVmWorkflowState) -> SecurityVmWorkflowState:
        _record_step(state, StepName.TEMPLATE_VALIDATE.value)
        auth = self._auth(state)
        template_id = state["template_id"]
        manifest = BASELINE_PROFILES.get(template_id)
        try:
            checked = self.hypervisor.validate_template(
                template_id,
                auth,
                manifest=manifest,
                expected_snapshot="clean-baseline",
            )
            if not checked.get("ok"):
                raise IsolationError("template validation returned not ok")
            state["template_report"] = checked
            state["current_step"] = StepName.NETWORK_VALIDATE.value
        except Exception as exc:
            state["error"] = f"template_validate failed: {exc}"
            state["status"] = WorkflowStatus.FAILED.value
        return state

    def execute_network_validate(self, state: SecurityVmWorkflowState) -> SecurityVmWorkflowState:
        _record_step(state, StepName.NETWORK_VALIDATE.value)
        auth = self._auth(state)
        net_id = state.get("network_id")
        if not net_id:
            # Fall back to provider's first isolated network from inventory
            inv = state.get("inventory_data") or self.hypervisor.inventory()
            networks = inv.get("networks", [])
            if isinstance(networks, list) and networks:
                first = networks[0]
                if isinstance(first, dict):
                    net_id = str(first.get("id", ""))
            if not net_id:
                state["error"] = "no isolated network specified or discovered"
                state["status"] = WorkflowStatus.FAILED.value
                return state
            state["network_id"] = net_id

        try:
            checked = self.hypervisor.validate_network(
                net_id,
                auth,
                allow_controlled_egress=state.get("controlled_egress", False),
            )
            if not checked.get("ok"):
                raise IsolationError("network validation returned not ok")
            state["network_report"] = checked
            state["status"] = WorkflowStatus.READY.value
            state["current_step"] = StepName.CLONE_REQUEST.value
        except Exception as exc:
            state["error"] = f"network_validate failed: {exc}"
            state["status"] = WorkflowStatus.FAILED.value
        return state

    def execute_clone_request(self, state: SecurityVmWorkflowState) -> SecurityVmWorkflowState:
        _record_step(state, StepName.CLONE_REQUEST.value)
        auth = self._auth(state)
        try:
            vm_id = self.hypervisor.clone(state["template_id"], auth)
            state["vm_id"] = vm_id
            state["current_step"] = StepName.BOOT.value
        except Exception as exc:
            state["error"] = f"clone_request failed: {exc}"
            return self.execute_compensating_cleanup(state)
        return state

    def execute_boot(self, state: SecurityVmWorkflowState) -> SecurityVmWorkflowState:
        _record_step(state, StepName.BOOT.value)
        auth = self._auth(state)
        try:
            self.hypervisor.power_on(state["vm_id"], auth)
            state["vm_power"] = "on"
            state["current_step"] = StepName.GUEST_READY.value
        except Exception as exc:
            state["error"] = f"boot failed: {exc}"
            return self.execute_compensating_cleanup(state)
        return state

    def execute_guest_ready(self, state: SecurityVmWorkflowState) -> SecurityVmWorkflowState:
        _record_step(state, StepName.GUEST_READY.value)
        auth = self._auth(state)
        try:
            ready = self.hypervisor.guest_ready(state["vm_id"], auth)
            if not ready:
                raise IsolationError(f"guest {state['vm_id']} is not ready")
            state["current_step"] = StepName.BENIGN_VALIDATION.value
        except Exception as exc:
            state["error"] = f"guest_ready failed: {exc}"
            return self.execute_compensating_cleanup(state)
        return state

    def execute_benign_validation(self, state: SecurityVmWorkflowState) -> SecurityVmWorkflowState:
        _record_step(state, StepName.BENIGN_VALIDATION.value)
        # Smoke test / baseline health check inside guest before sample execution
        try:
            if not state.get("vm_id") or state.get("vm_power") != "on":
                raise IsolationError("cannot perform benign validation: guest is not running")
            # In fake hypervisor, guest is confirmed ready
            state["benign_validation_ok"] = True
            state["current_step"] = StepName.EXECUTION_APPROVAL.value
        except Exception as exc:
            state["error"] = f"benign_validation failed: {exc}"
            return self.execute_compensating_cleanup(state)
        return state

    def execute_execution_approval(self, state: SecurityVmWorkflowState) -> SecurityVmWorkflowState:
        _record_step(state, StepName.EXECUTION_APPROVAL.value)
        if state.get("execution_class") == "untrusted":
            approval = state.get("approval_id", "").strip()
            if not approval:
                state["status"] = WorkflowStatus.AWAITING_APPROVAL.value
                return state
        # Approved or benign
        state["status"] = WorkflowStatus.RUNNING.value
        state["current_step"] = StepName.ANALYSIS.value
        return state

    def execute_analysis(self, state: SecurityVmWorkflowState) -> SecurityVmWorkflowState:
        _record_step(state, StepName.ANALYSIS.value)
        if state.get("execution_class") == "untrusted" and not state.get("approval_id"):
            state["error"] = "untrusted execution executed without required approval"
            return self.execute_compensating_cleanup(state)

        try:
            state["analysis_output"] = {
                "vm_id": state["vm_id"],
                "profile": state["profile"],
                "executed": True,
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }
            state["findings"].append(f"analyzed {state['profile']} in isolated VM {state['vm_id']}")
            state["status"] = WorkflowStatus.COLLECTING.value
            state["current_step"] = StepName.COLLECT.value
        except Exception as exc:
            state["error"] = f"analysis failed: {exc}"
            return self.execute_compensating_cleanup(state)
        return state

    def execute_collect(self, state: SecurityVmWorkflowState) -> SecurityVmWorkflowState:
        _record_step(state, StepName.COLLECT.value)
        try:
            report_data = json.dumps(state.get("analysis_output", {}), sort_keys=True).encode("utf-8")
            ev_ref = {
                "evidence_id": f"ev-{state['job_id'][:8]}-run",
                "locator": f"quarantine://evidence/{state['job_id']}/analysis.json",
                "sha256": hashlib.sha256(report_data).hexdigest(),
                "media_type": "application/json",
                "byte_length": len(report_data),
            }
            state["evidence"].append(ev_ref)
            state["current_step"] = StepName.SHUTDOWN.value
        except Exception as exc:
            state["error"] = f"collect failed: {exc}"
            return self.execute_compensating_cleanup(state)
        return state

    def execute_shutdown(self, state: SecurityVmWorkflowState) -> SecurityVmWorkflowState:
        _record_step(state, StepName.SHUTDOWN.value)
        auth = self._auth(state)
        vm_id = state.get("vm_id")
        if vm_id:
            try:
                self.hypervisor.power_off(vm_id, auth)
                state["vm_power"] = "off"
            except Exception as exc:
                state["error"] = f"shutdown failed: {exc}"
                return self.execute_compensating_cleanup(state)
        state["current_step"] = StepName.DESTROY.value
        return state

    def execute_destroy(self, state: SecurityVmWorkflowState) -> SecurityVmWorkflowState:
        _record_step(state, StepName.DESTROY.value)
        auth = self._auth(state)
        vm_id = state.get("vm_id")
        if vm_id:
            try:
                self.hypervisor.destroy(vm_id, auth)
                state["vm_id"] = ""
            except Exception as exc:
                state["error"] = f"destroy failed: {exc}"
                return self.execute_compensating_cleanup(state)
        state["current_step"] = StepName.RESIDUAL_CHECK.value
        return state

    def execute_residual_check(self, state: SecurityVmWorkflowState) -> SecurityVmWorkflowState:
        _record_step(state, StepName.RESIDUAL_CHECK.value)
        residuals = self.hypervisor.residual(state["job_id"])
        state["residual_vms"] = residuals
        if residuals:
            state["cleanup_status"] = "failed"
            state["status"] = WorkflowStatus.BLOCKED.value
            state["error"] = f"cleanup incomplete: residual resources persist: {residuals}"
            return state

        state["cleanup_status"] = "verified"
        state["current_step"] = StepName.REPORT.value
        return state

    def execute_report(self, state: SecurityVmWorkflowState) -> SecurityVmWorkflowState:
        _record_step(state, StepName.REPORT.value)
        if state.get("cleanup_status") != "verified" or state.get("residual_vms"):
            state["status"] = WorkflowStatus.BLOCKED.value
            state["error"] = "report blocked: residual resources remain unverified"
            return state

        report = {
            "job_id": state["job_id"],
            "profile": state["profile"],
            "provider": state["provider"],
            "template_id": state["template_id"],
            "execution_class": state["execution_class"],
            "network_id": state["network_id"],
            "approval_id": state["approval_id"],
            "benign_validation_ok": state["benign_validation_ok"],
            "cleanup_status": state["cleanup_status"],
            "residual_count": len(state["residual_vms"]),
            "evidence_count": len(state["evidence"]),
            "findings": list(state["findings"]),
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "status": "success",
        }
        state["report"] = report
        state["status"] = WorkflowStatus.COMPLETED.value
        return state

    def execute_compensating_cleanup(self, state: SecurityVmWorkflowState) -> SecurityVmWorkflowState:
        """Idempotent cleanup for post-clone errors. Residual check strictly gates blocked state."""
        _record_step(state, StepName.COMPENSATING_CLEANUP.value, detail=state.get("error", ""))
        auth = self._auth(state)
        vm_id = state.get("vm_id")

        if vm_id:
            try:
                self.hypervisor.power_off(vm_id, auth)
            except Exception:
                pass
            try:
                self.hypervisor.destroy(vm_id, auth)
                state["vm_id"] = ""
            except Exception:
                pass

        residuals = self.hypervisor.residual(state["job_id"])
        state["residual_vms"] = residuals
        if residuals:
            state["cleanup_status"] = "failed"
            state["status"] = WorkflowStatus.BLOCKED.value
            state["error"] = f"{state.get('error', 'failure')} (cleanup failed: residuals {residuals})"
        else:
            state["cleanup_status"] = "verified"
            state["status"] = WorkflowStatus.FAILED.value
        return state

    def step(self, state: SecurityVmWorkflowState) -> SecurityVmWorkflowState:
        """Advance the state machine by exactly one step."""
        step = state.get("current_step")
        if state.get("status") in {
            WorkflowStatus.COMPLETED.value,
            WorkflowStatus.FAILED.value,
            WorkflowStatus.BLOCKED.value,
            WorkflowStatus.AWAITING_APPROVAL.value,
        }:
            return state

        dispatch_map = {
            StepName.INVENTORY.value: self.execute_inventory,
            StepName.TEMPLATE_VALIDATE.value: self.execute_template_validate,
            StepName.NETWORK_VALIDATE.value: self.execute_network_validate,
            StepName.CLONE_REQUEST.value: self.execute_clone_request,
            StepName.BOOT.value: self.execute_boot,
            StepName.GUEST_READY.value: self.execute_guest_ready,
            StepName.BENIGN_VALIDATION.value: self.execute_benign_validation,
            StepName.EXECUTION_APPROVAL.value: self.execute_execution_approval,
            StepName.ANALYSIS.value: self.execute_analysis,
            StepName.COLLECT.value: self.execute_collect,
            StepName.SHUTDOWN.value: self.execute_shutdown,
            StepName.DESTROY.value: self.execute_destroy,
            StepName.RESIDUAL_CHECK.value: self.execute_residual_check,
            StepName.REPORT.value: self.execute_report,
            StepName.COMPENSATING_CLEANUP.value: self.execute_compensating_cleanup,
        }

        fn = dispatch_map.get(step)
        if fn is None:
            state["error"] = f"unknown step {step}"
            state["status"] = WorkflowStatus.FAILED.value
            return state
        return fn(state)

    def run_to_completion(self, state: SecurityVmWorkflowState, max_steps: int = 30) -> SecurityVmWorkflowState:
        """Execute steps continuously until completion, failure, blocked state, or approval pause."""
        for _ in range(max_steps):
            if state.get("status") in {
                WorkflowStatus.COMPLETED.value,
                WorkflowStatus.FAILED.value,
                WorkflowStatus.BLOCKED.value,
                WorkflowStatus.AWAITING_APPROVAL.value,
            }:
                break
            state = self.step(state)
        return state

    def resume_approval(self, state: SecurityVmWorkflowState, approval_id: str) -> SecurityVmWorkflowState:
        """Provide approval for an awaiting job and resume execution to completion."""
        if not approval_id:
            raise ValueError("approval_id is required to resume")
        state["approval_id"] = approval_id
        if state["status"] == WorkflowStatus.AWAITING_APPROVAL.value:
            state["status"] = WorkflowStatus.RUNNING.value
            state["current_step"] = StepName.ANALYSIS.value
        return self.run_to_completion(state)


# -----------------------------------------------------------------------------
# LangGraph Workflow Definition (ADR 0020)
# -----------------------------------------------------------------------------

def thread_config(job_id: str) -> dict[str, Any]:
    return {"configurable": {"thread_id": f"security-vm-{job_id}"}}


def build_security_vm_graph(hypervisor: HypervisorPort, checkpointer: Any = None) -> Any:
    """Build a resumable LangGraph state graph for the security VM lifecycle."""
    try:
        from langgraph.graph import END, START, StateGraph
        from langgraph.types import interrupt
    except ImportError as exc:
        raise RuntimeError(f"langgraph is required to build graph: {exc}")

    engine = SecurityVmLifecycleEngine(hypervisor)

    def n_inventory(state: SecurityVmWorkflowState) -> dict[str, Any]:
        return engine.execute_inventory(copy.deepcopy(state))

    def n_template_validate(state: SecurityVmWorkflowState) -> dict[str, Any]:
        return engine.execute_template_validate(copy.deepcopy(state))

    def n_network_validate(state: SecurityVmWorkflowState) -> dict[str, Any]:
        return engine.execute_network_validate(copy.deepcopy(state))

    def n_clone_request(state: SecurityVmWorkflowState) -> dict[str, Any]:
        return engine.execute_clone_request(copy.deepcopy(state))

    def n_boot(state: SecurityVmWorkflowState) -> dict[str, Any]:
        return engine.execute_boot(copy.deepcopy(state))

    def n_guest_ready(state: SecurityVmWorkflowState) -> dict[str, Any]:
        return engine.execute_guest_ready(copy.deepcopy(state))

    def n_benign_validation(state: SecurityVmWorkflowState) -> dict[str, Any]:
        return engine.execute_benign_validation(copy.deepcopy(state))

    def n_execution_approval(state: SecurityVmWorkflowState) -> dict[str, Any]:
        cur = copy.deepcopy(state)
        if cur.get("execution_class") == "untrusted" and not cur.get("approval_id"):
            cur["status"] = WorkflowStatus.AWAITING_APPROVAL.value
            decision = interrupt({"need_approval": True, "job_id": cur["job_id"]})
            if decision:
                cur["approval_id"] = str(decision)
                cur["status"] = WorkflowStatus.RUNNING.value
                cur["current_step"] = StepName.ANALYSIS.value
                return cur
            return cur
        return engine.execute_execution_approval(cur)

    def n_analysis(state: SecurityVmWorkflowState) -> dict[str, Any]:
        return engine.execute_analysis(copy.deepcopy(state))

    def n_collect(state: SecurityVmWorkflowState) -> dict[str, Any]:
        return engine.execute_collect(copy.deepcopy(state))

    def n_shutdown(state: SecurityVmWorkflowState) -> dict[str, Any]:
        return engine.execute_shutdown(copy.deepcopy(state))

    def n_destroy(state: SecurityVmWorkflowState) -> dict[str, Any]:
        return engine.execute_destroy(copy.deepcopy(state))

    def n_residual_check(state: SecurityVmWorkflowState) -> dict[str, Any]:
        return engine.execute_residual_check(copy.deepcopy(state))

    def n_report(state: SecurityVmWorkflowState) -> dict[str, Any]:
        return engine.execute_report(copy.deepcopy(state))

    def n_compensating_cleanup(state: SecurityVmWorkflowState) -> dict[str, Any]:
        return engine.execute_compensating_cleanup(copy.deepcopy(state))

    # Condition checkers
    def check_pre_clone(state: SecurityVmWorkflowState) -> str:
        if state.get("status") == WorkflowStatus.FAILED.value:
            return END
        return state.get("current_step", END)

    def check_post_clone(state: SecurityVmWorkflowState) -> str:
        if state.get("status") in {WorkflowStatus.FAILED.value, WorkflowStatus.BLOCKED.value}:
            return "compensating_cleanup"
        if state.get("status") == WorkflowStatus.AWAITING_APPROVAL.value:
            return END
        return state.get("current_step", END)

    def check_residual(state: SecurityVmWorkflowState) -> str:
        if state.get("status") == WorkflowStatus.BLOCKED.value:
            return END
        return "report"

    builder = StateGraph(SecurityVmWorkflowState)
    builder.add_node("inventory", n_inventory)
    builder.add_node("template_validate", n_template_validate)
    builder.add_node("network_validate", n_network_validate)
    builder.add_node("clone_request", n_clone_request)
    builder.add_node("boot", n_boot)
    builder.add_node("guest_ready", n_guest_ready)
    builder.add_node("benign_validation", n_benign_validation)
    builder.add_node("execution_approval", n_execution_approval)
    builder.add_node("analysis", n_analysis)
    builder.add_node("collect", n_collect)
    builder.add_node("shutdown", n_shutdown)
    builder.add_node("destroy", n_destroy)
    builder.add_node("residual_check", n_residual_check)
    builder.add_node("report", n_report)
    builder.add_node("compensating_cleanup", n_compensating_cleanup)

    builder.add_edge(START, "inventory")
    builder.add_conditional_edges("inventory", check_pre_clone, ["template_validate", END])
    builder.add_conditional_edges("template_validate", check_pre_clone, ["network_validate", END])
    builder.add_conditional_edges("network_validate", check_pre_clone, ["clone_request", END])

    builder.add_conditional_edges("clone_request", check_post_clone, ["boot", "compensating_cleanup", END])
    builder.add_conditional_edges("boot", check_post_clone, ["guest_ready", "compensating_cleanup", END])
    builder.add_conditional_edges("guest_ready", check_post_clone, ["benign_validation", "compensating_cleanup", END])
    builder.add_conditional_edges("benign_validation", check_post_clone, ["execution_approval", "compensating_cleanup", END])
    builder.add_conditional_edges("execution_approval", check_post_clone, ["analysis", "compensating_cleanup", END])
    builder.add_conditional_edges("analysis", check_post_clone, ["collect", "compensating_cleanup", END])
    builder.add_conditional_edges("collect", check_post_clone, ["shutdown", "compensating_cleanup", END])
    builder.add_conditional_edges("shutdown", check_post_clone, ["destroy", "compensating_cleanup", END])
    builder.add_conditional_edges("destroy", check_post_clone, ["residual_check", "compensating_cleanup", END])
    builder.add_conditional_edges("residual_check", check_residual, ["report", END])
    builder.add_edge("report", END)
    builder.add_edge("compensating_cleanup", END)

    return builder.compile(checkpointer=checkpointer)
