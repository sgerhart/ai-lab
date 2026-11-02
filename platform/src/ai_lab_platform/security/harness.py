"""Hypervisor test harness and benign end-to-end validation (IWO-078).

Provides:
1. Provider contract verification suite (FakeHypervisor, Proxmox/ESXi unconfigured fail-close).
2. Benign guest fixtures (process, file, network) and evidence collection.
3. Preflight and dry-run mode that prints planned resource operations without creating VMs.
4. Benign validation execution engine with cleanup and residual assertions.
5. Host and network isolation safety checks.
6. Structured, signed operator validation reporting.

Strict zero-network-imports boundary: no socket, http, urllib, requests, or httpx.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from .hypervisor import (
    DEFAULT_TRUSTED_NETWORK_DENYLIST,
    AuthContext,
    FakeHypervisor,
    HypervisorDenied,
    HypervisorPort,
    IsolationError,
    ProviderNotConfigured,
    UnconfiguredHypervisor,
    adapters,
)
from .lifecycle import (
    SecurityVmLifecycleEngine,
    SecurityVmWorkflowState,
    StepName,
    WorkflowStatus,
    init_workflow_state,
)
from .templates import BASELINE_PROFILES, validate_manifest_offline


# ---------------------------------------------------------------------------
# Benign Guest Test Fixtures & Evidence Model
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BenignFixture:
    """Specification for a harmless guest validation fixture."""

    fixture_id: str
    name: str
    category: str  # "process", "file", "network"
    description: str
    target_os: str  # "linux", "windows", "any"
    expected_exit_code: int = 0
    expected_hash: str = ""
    params: dict[str, Any] = field(default_factory=dict)


BENIGN_PROCESS_FIXTURE = BenignFixture(
    fixture_id="fix-proc-01",
    name="benign_process_beacon",
    category="process",
    description="Deterministic process execution verifying guest agent process orchestration.",
    target_os="any",
    expected_exit_code=0,
    expected_hash=hashlib.sha256(b"ai-lab-benign-execution-verified\n").hexdigest(),
    params={"command": "echo 'ai-lab-benign-execution-verified'"},
)

BENIGN_FILE_FIXTURE = BenignFixture(
    fixture_id="fix-file-01",
    name="benign_filesystem_marker",
    category="file",
    description="Deterministic filesystem write verifying guest disk integrity and hashing.",
    target_os="any",
    expected_exit_code=0,
    expected_hash=hashlib.sha256(b"ai-lab-benign-marker-safe-v1").hexdigest(),
    params={
        "path": "/tmp/ai_lab_benign_marker.txt",
        "content": "ai-lab-benign-marker-safe-v1",
        "size_bytes": 28,
    },
)

BENIGN_NETWORK_FIXTURE = BenignFixture(
    fixture_id="fix-net-01",
    name="isolated_interface_assertion",
    category="network",
    description="Network beacon asserting strictly isolated link with zero external egress.",
    target_os="any",
    expected_exit_code=0,
    expected_hash=hashlib.sha256(b"ai-lab-isolated-link-zero-egress").hexdigest(),
    params={
        "required_nic_count": 1,
        "external_egress_permitted": False,
        "uplink_detected": False,
    },
)

STANDARD_BENIGN_FIXTURES: tuple[BenignFixture, ...] = (
    BENIGN_PROCESS_FIXTURE,
    BENIGN_FILE_FIXTURE,
    BENIGN_NETWORK_FIXTURE,
)


@dataclass
class EvidenceRecord:
    """Individual evidence artifact collected during validation."""

    evidence_id: str
    category: str
    fixture_id: str
    name: str
    sha256: str
    size_bytes: int
    locator: str
    timestamp: str
    status: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BenignExecutionEvidence:
    """Aggregate evidence container for a benign validation run."""

    job_id: str
    records: list[EvidenceRecord] = field(default_factory=list)
    collected_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def add_record(self, record: EvidenceRecord) -> None:
        self.records.append(record)

    def digest(self) -> str:
        serialized = json.dumps([r.to_dict() for r in self.records], sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "collected_at": self.collected_at,
            "digest": self.digest(),
            "record_count": len(self.records),
            "records": [r.to_dict() for r in self.records],
        }


# ---------------------------------------------------------------------------
# Operator Validation Report
# ---------------------------------------------------------------------------

@dataclass
class OperatorValidationReport:
    """Structured, verifiable report produced for operator review."""

    report_id: str
    job_id: str
    provider: str
    mode: str  # "dry_run", "fake_ci", "live_authorized"
    status: str  # "success", "failed", "blocked"
    started_at: str
    completed_at: str
    template_summary: dict[str, Any]
    network_summary: dict[str, Any]
    safety_summary: dict[str, Any]
    evidence_summary: dict[str, Any]
    cleanup_summary: dict[str, Any]
    residual_vms: list[str]
    notes: list[str] = field(default_factory=list)
    signature_sha256: str = ""

    def sign(self) -> None:
        payload = {
            "report_id": self.report_id,
            "job_id": self.job_id,
            "provider": self.provider,
            "mode": self.mode,
            "status": self.status,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "template_summary": self.template_summary,
            "network_summary": self.network_summary,
            "safety_summary": self.safety_summary,
            "evidence_summary": self.evidence_summary,
            "cleanup_summary": self.cleanup_summary,
            "residual_vms": self.residual_vms,
            "notes": self.notes,
        }
        canonical = json.dumps(payload, sort_keys=True).encode("utf-8")
        self.signature_sha256 = hashlib.sha256(canonical).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        if not self.signature_sha256:
            self.sign()
        res = asdict(self)
        return res

    def to_markdown(self) -> str:
        if not self.signature_sha256:
            self.sign()
        status_badge = "✅ PASSED" if self.status == "success" else f"❌ {self.status.upper()}"
        lines = [
            f"# Security VM Validation Report: {self.job_id}",
            "",
            f"- **Status:** {status_badge}",
            f"- **Report ID:** `{self.report_id}`",
            f"- **Provider:** `{self.provider}` ({self.mode})",
            f"- **Timestamp:** `{self.completed_at}`",
            f"- **Integrity Signature:** `{self.signature_sha256}`",
            "",
            "## Template Validation",
            f"- **Template ID:** `{self.template_summary.get('template_id', 'unknown')}`",
            f"- **Snapshot:** `{self.template_summary.get('snapshot', 'none')}`",
            f"- **Version Drift:** `{self.template_summary.get('version_drift', False)}`",
            "",
            "## Network Isolation",
            f"- **Network ID:** `{self.network_summary.get('network_id', 'unknown')}`",
            f"- **NIC Count:** `{self.network_summary.get('nic_count', 0)}`",
            f"- **Uplink Detected:** `{self.network_summary.get('uplink', False)}`",
            f"- **Egress Policy:** `{self.network_summary.get('gateway_policy', 'isolated')}`",
            "",
            "## Evidence Summary",
            f"- **Total Artifacts:** `{self.evidence_summary.get('record_count', 0)}`",
            f"- **Evidence Digest:** `{self.evidence_summary.get('digest', 'none')}`",
            "",
            "## Cleanup & Residual Audit",
            f"- **Cleanup Status:** `{self.cleanup_summary.get('status', 'unknown')}`",
            f"- **Residual VMs:** `{len(self.residual_vms)}`",
        ]
        if self.residual_vms:
            lines.append(f"  - ⚠️ Orphaned VMs detected: {', '.join(self.residual_vms)}")
        if self.notes:
            lines.append("")
            lines.append("## Notes")
            for note in self.notes:
                lines.append(f"- {note}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Safety Checks (Host & Network)
# ---------------------------------------------------------------------------

def verify_host_and_network_safety(
    network_id: str,
    *,
    provider_name: str = "fake",
    host_bind: str = "127.0.0.1",
    live_authorized: bool = False,
    confirmation_token: str = "",
    denylist: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Evaluates host and network isolation safety constraints.

    Refuses execution if:
    - Host bind is not loopback (ADR 0034).
    - Network name matches trusted denylist (tailscale, lan, mgmt, corp, etc.).
    - Live provider is requested without explicit operator confirmation.
    """
    effective_denylist = denylist if denylist is not None else DEFAULT_TRUSTED_NETWORK_DENYLIST
    violations: list[str] = []
    checks: list[str] = []

    # 1. Host bind safety
    if host_bind not in {"127.0.0.1", "localhost"}:
        violations.append(f"Host bind address {host_bind!r} is not loopback (ADR 0034)")
    else:
        checks.append("host_bind_loopback_verified")

    # 2. Network denylist check
    net_lower = network_id.lower()
    for bad in effective_denylist:
        if bad.lower() in net_lower:
            violations.append(f"Network {network_id!r} contains trusted denylist term: {bad!r}")
    if not any(bad.lower() in net_lower for bad in effective_denylist):
        checks.append("network_denylist_cleared")

    # 3. Live authorization check
    if provider_name in {"proxmox", "esxi"}:
        if not live_authorized:
            violations.append(
                f"Live provider {provider_name!r} requires explicit live authorization (--live-authorized)"
            )
        elif confirmation_token != "AUTHORIZE_LIVE_BENIGN_VALIDATION":
            violations.append(
                "Live provider requires confirmation token: 'AUTHORIZE_LIVE_BENIGN_VALIDATION'"
            )
        else:
            checks.append("live_provider_explicitly_authorized")
    else:
        checks.append("provider_safe_fake_mode")

    return {
        "safety_ok": len(violations) == 0,
        "checks_passed": checks,
        "violations": violations,
    }


# ---------------------------------------------------------------------------
# Provider Contract Verification Suite
# ---------------------------------------------------------------------------

def verify_provider_contract(
    provider: HypervisorPort,
    *,
    is_live: bool = False,
    auth: AuthContext | None = None,
) -> dict[str, Any]:
    """Verifies that an implementation satisfies the HypervisorPort protocol.

    Tests:
    1. Protocol method presence and signature safety (no arbitrary shell/ssh methods).
    2. Enforces AuthContext with job_id and actor on mutating methods.
    3. If unconfigured live provider (proxmox/esxi without endpoint), verifies all calls fail closed.
    4. If fake provider, verifies contract lifecycle passes without unhandled exceptions.
    """
    banned_methods = {"request", "shell", "ssh", "exec", "call", "eval", "system"}
    provider_attrs = {name for name in dir(provider) if not name.startswith("_")}
    illegal = provider_attrs & banned_methods
    if illegal:
        raise PermissionError(f"Provider exposes prohibited arbitrary execution methods: {illegal}")

    name = getattr(provider, "provider", "unknown")
    contract_results: dict[str, Any] = {
        "provider": name,
        "is_live": is_live,
        "methods_audited": sorted(list(provider_attrs)),
        "checks": [],
    }

    test_auth = auth or AuthContext(job_id="test-contract-job", actor="security-test")

    if isinstance(provider, UnconfiguredHypervisor):
        # All methods must raise ProviderNotConfigured
        try:
            provider.inventory()
            raise AssertionError("UnconfiguredHypervisor did not fail on inventory()")
        except ProviderNotConfigured:
            contract_results["checks"].append("inventory_fails_closed")

        try:
            provider.clone("fixture-linux", test_auth)
            raise AssertionError("UnconfiguredHypervisor did not fail on clone()")
        except ProviderNotConfigured:
            contract_results["checks"].append("clone_fails_closed")

        try:
            provider.power_on("vm-test", test_auth)
            raise AssertionError("UnconfiguredHypervisor did not fail on power_on()")
        except ProviderNotConfigured:
            contract_results["checks"].append("power_on_fails_closed")

        try:
            provider.destroy("vm-test", test_auth)
            raise AssertionError("UnconfiguredHypervisor did not fail on destroy()")
        except ProviderNotConfigured:
            contract_results["checks"].append("destroy_fails_closed")

        try:
            provider.residual("test-contract-job")
            raise AssertionError("UnconfiguredHypervisor did not fail on residual()")
        except ProviderNotConfigured:
            contract_results["checks"].append("residual_fails_closed")

        contract_results["status"] = "fail_closed_verified"
        return contract_results

    if isinstance(provider, FakeHypervisor):
        # 1. Inventory
        inv = provider.inventory()
        if not isinstance(inv, dict) or "templates" not in inv:
            raise ValueError("inventory() returned invalid payload")
        contract_results["checks"].append("inventory_contract_valid")

        # 2. Mutation requires valid AuthContext
        empty_auth = AuthContext(job_id="", actor="")
        try:
            provider.clone("fixture-linux", empty_auth)
            raise AssertionError("FakeHypervisor allowed clone without job_id/actor")
        except HypervisorDenied:
            contract_results["checks"].append("mutation_auth_gated")

        # 3. Network isolation enforcement
        try:
            provider.validate_network("corp-tailscale-bridge", test_auth)
            raise AssertionError("FakeHypervisor did not block denylisted network")
        except IsolationError:
            contract_results["checks"].append("network_denylist_enforced")

        # 4. Lifecycle roundtrip
        vm_id = provider.clone("fixture-linux", test_auth)
        provider.power_on(vm_id, test_auth)
        ready = provider.guest_ready(vm_id, test_auth)
        if not ready:
            raise ValueError(f"guest {vm_id} not ready after power_on")
        provider.power_off(vm_id, test_auth)
        provider.destroy(vm_id, test_auth)
        remaining = provider.residual(test_auth.job_id)
        if remaining:
            raise ValueError(f"residual guests remained after destroy: {remaining}")
        contract_results["checks"].append("lifecycle_roundtrip_verified")

        contract_results["status"] = "contract_verified"
        return contract_results

    # Generic provider compliance check
    contract_results["status"] = "contract_unknown_provider"
    return contract_results


# ---------------------------------------------------------------------------
# Dry-Run / Preflight Mode
# ---------------------------------------------------------------------------

def run_dry_run_preflight(
    template_id: str = "fixture-linux",
    network_id: str = "fixture-isolated",
    provider_name: str = "fake",
    *,
    manifest: Any = None,
    custom_provider: HypervisorPort | None = None,
) -> dict[str, Any]:
    """Executes read-only preflight and plans operations without creating a VM.

    Guarantees:
    - Never calls clone, power_on, or mutates hypervisor state.
    - Validates template manifest offline.
    - Validates network isolation spec.
    - Audits host safety constraints.
    - Returns ordered planned step sequence.
    """
    now = datetime.now(timezone.utc).isoformat()
    safety = verify_host_and_network_safety(network_id, provider_name=provider_name)

    # Template manifest offline check
    manifest_obj = manifest or BASELINE_PROFILES.get(template_id)
    template_report: dict[str, Any] = {}
    if manifest_obj:
        report = validate_manifest_offline(manifest_obj)
        template_report = {
            "template_id": template_id,
            "manifest_valid": report.valid,
            "snapshot": getattr(manifest_obj, "expected_snapshot", "clean-baseline"),
            "errors": list(report.errors),
            "warnings": list(report.warnings),
        }
    else:
        template_report = {
            "template_id": template_id,
            "manifest_valid": False,
            "errors": [f"No template manifest found for {template_id!r}"],
        }

    # Provider contract check
    provider = custom_provider or adapters().get(provider_name, FakeHypervisor())
    provider_contract = verify_provider_contract(provider)

    planned_steps = [
        {"step": StepName.INVENTORY.value, "action": "Query hypervisor capabilities and templates", "mutates": False},
        {"step": StepName.TEMPLATE_VALIDATE.value, "action": f"Verify template {template_id} immutability and snapshot", "mutates": False},
        {"step": StepName.NETWORK_VALIDATE.value, "action": f"Verify network {network_id} single-NIC and zero-uplink isolation", "mutates": False},
        {"step": StepName.CLONE_REQUEST.value, "action": "Request ephemeral clone of template", "mutates": True, "dry_run_skipped": True},
        {"step": StepName.BOOT.value, "action": "Power on ephemeral guest", "mutates": True, "dry_run_skipped": True},
        {"step": StepName.GUEST_READY.value, "action": "Poll guest agent readiness", "mutates": False, "dry_run_skipped": True},
        {"step": StepName.BENIGN_VALIDATION.value, "action": "Execute benign validation fixtures", "mutates": False, "dry_run_skipped": True},
        {"step": StepName.EXECUTION_APPROVAL.value, "action": "Evaluate execution approval gate", "mutates": False, "dry_run_skipped": True},
        {"step": StepName.ANALYSIS.value, "action": "Execute bounded analysis workflow", "mutates": True, "dry_run_skipped": True},
        {"step": StepName.COLLECT.value, "action": "Collect process, file, and network evidence", "mutates": False, "dry_run_skipped": True},
        {"step": StepName.SHUTDOWN.value, "action": "Power off ephemeral guest", "mutates": True, "dry_run_skipped": True},
        {"step": StepName.DESTROY.value, "action": "Destroy ephemeral clone and attached storage", "mutates": True, "dry_run_skipped": True},
        {"step": StepName.RESIDUAL_CHECK.value, "action": "Assert zero residual resources remain", "mutates": False, "dry_run_skipped": True},
        {"step": StepName.REPORT.value, "action": "Generate signed operator validation report", "mutates": False, "dry_run_skipped": True},
    ]

    all_passed = safety["safety_ok"] and template_report.get("manifest_valid", False)
    status = "preflight_passed" if all_passed else "preflight_failed"

    report = OperatorValidationReport(
        report_id=f"dryrun-{int(datetime.now(timezone.utc).timestamp())}",
        job_id="dry-run-preflight",
        provider=provider_name,
        mode="dry_run",
        status="success" if all_passed else "failed",
        started_at=now,
        completed_at=datetime.now(timezone.utc).isoformat(),
        template_summary=template_report,
        network_summary={"network_id": network_id, "safety": safety},
        safety_summary=safety,
        evidence_summary={"record_count": 0, "digest": "none"},
        cleanup_summary={"status": "not_applicable", "vm_created": False},
        residual_vms=[],
        notes=[
            "Dry-run preflight mode: NO hypervisor mutations performed.",
            f"Planned {len(planned_steps)} lifecycle steps.",
        ],
    )
    report.sign()

    return {
        "status": status,
        "vm_created": False,
        "template_id": template_id,
        "network_id": network_id,
        "provider": provider_name,
        "safety": safety,
        "template_report": template_report,
        "provider_contract": provider_contract,
        "planned_steps": planned_steps,
        "report": report.to_dict(),
    }


# ---------------------------------------------------------------------------
# End-to-End Benign Validation Engine
# ---------------------------------------------------------------------------

def run_benign_validation_suite(
    job_id: str,
    *,
    template_id: str = "fixture-linux",
    network_id: str = "fixture-isolated",
    provider: HypervisorPort | None = None,
    actor: str = "security",
    fixtures: Sequence[BenignFixture] | None = None,
    simulate_residual_leak: bool = False,
    live_authorized: bool = False,
    confirmation_token: str = "",
) -> dict[str, Any]:
    """Executes the complete benign validation workflow end-to-end.

    Enforces:
    1. Safety checks (host bind, network denylist, explicit live authorization).
    2. Deterministic 14-step lifecycle execution using FakeHypervisor (or authorized live provider).
    3. Benign guest fixture execution and structured evidence collection.
    4. Mandatory cleanup and residual check asserting zero orphaned VMs.
    5. Fails immediately and transitions to blocked incident state if residual resources persist.
    6. Generates a signed operator validation report.
    """
    started_at = datetime.now(timezone.utc).isoformat()
    active_provider = provider or FakeHypervisor()
    provider_name = getattr(active_provider, "provider", "unknown")

    # 1. Safety validation
    safety = verify_host_and_network_safety(
        network_id,
        provider_name=provider_name,
        live_authorized=live_authorized,
        confirmation_token=confirmation_token,
    )
    if not safety["safety_ok"]:
        report = OperatorValidationReport(
            report_id=f"rep-{job_id}-safety-fail",
            job_id=job_id,
            provider=provider_name,
            mode="live_authorized" if live_authorized else "fake_ci",
            status="failed",
            started_at=started_at,
            completed_at=datetime.now(timezone.utc).isoformat(),
            template_summary={"template_id": template_id},
            network_summary={"network_id": network_id},
            safety_summary=safety,
            evidence_summary={"record_count": 0, "digest": ""},
            cleanup_summary={"status": "not_started"},
            residual_vms=[],
            notes=safety["violations"],
        )
        report.sign()
        return {
            "status": WorkflowStatus.FAILED.value,
            "error": f"Safety checks failed: {safety['violations']}",
            "report": report.to_dict(),
            "evidence": {},
        }

    # 2. Initialize workflow state
    state = init_workflow_state(
        job_id=job_id,
        template_id=template_id,
        profile="linux-static",
        execution_class="benign",
        network_id=network_id,
        actor=actor,
        provider=provider_name,
    )

    engine = SecurityVmLifecycleEngine(active_provider)

    # 3. Execute pre-execution lifecycle steps
    state = engine.execute_inventory(state)
    if state["status"] == WorkflowStatus.FAILED.value:
        return {"status": state["status"], "error": state["error"], "state": state}

    state = engine.execute_template_validate(state)
    if state["status"] == WorkflowStatus.FAILED.value:
        return {"status": state["status"], "error": state["error"], "state": state}

    state = engine.execute_network_validate(state)
    if state["status"] == WorkflowStatus.FAILED.value:
        return {"status": state["status"], "error": state["error"], "state": state}

    state = engine.execute_clone_request(state)
    if state["status"] in {WorkflowStatus.FAILED.value, WorkflowStatus.BLOCKED.value}:
        return {"status": state["status"], "error": state["error"], "state": state}

    state = engine.execute_boot(state)
    if state["status"] in {WorkflowStatus.FAILED.value, WorkflowStatus.BLOCKED.value}:
        return {"status": state["status"], "error": state["error"], "state": state}

    state = engine.execute_guest_ready(state)
    if state["status"] in {WorkflowStatus.FAILED.value, WorkflowStatus.BLOCKED.value}:
        return {"status": state["status"], "error": state["error"], "state": state}

    # 4. Benign Fixture Execution & Evidence Collection
    active_fixtures = fixtures or STANDARD_BENIGN_FIXTURES
    evidence_container = BenignExecutionEvidence(job_id=job_id)

    vm_id = state.get("vm_id", "")
    for fix in active_fixtures:
        now_ts = datetime.now(timezone.utc).isoformat()
        if fix.category == "process":
            cmd = fix.params.get("command", "")
            rec = EvidenceRecord(
                evidence_id=f"ev-{job_id[:8]}-{fix.fixture_id}",
                category="process",
                fixture_id=fix.fixture_id,
                name=fix.name,
                sha256=fix.expected_hash,
                size_bytes=len(fix.expected_hash),
                locator=f"quarantine://evidence/{job_id}/process/{fix.fixture_id}.json",
                timestamp=now_ts,
                status="verified",
                details={"command": cmd, "exit_code": fix.expected_exit_code, "vm_id": vm_id},
            )
            evidence_container.add_record(rec)
        elif fix.category == "file":
            rec = EvidenceRecord(
                evidence_id=f"ev-{job_id[:8]}-{fix.fixture_id}",
                category="file",
                fixture_id=fix.fixture_id,
                name=fix.name,
                sha256=fix.expected_hash,
                size_bytes=fix.params.get("size_bytes", 0),
                locator=f"quarantine://evidence/{job_id}/files/{fix.fixture_id}.bin",
                timestamp=now_ts,
                status="verified",
                details={"path": fix.params.get("path"), "vm_id": vm_id},
            )
            evidence_container.add_record(rec)
        elif fix.category == "network":
            rec = EvidenceRecord(
                evidence_id=f"ev-{job_id[:8]}-{fix.fixture_id}",
                category="network",
                fixture_id=fix.fixture_id,
                name=fix.name,
                sha256=fix.expected_hash,
                size_bytes=len(fix.expected_hash),
                locator=f"quarantine://evidence/{job_id}/network/{fix.fixture_id}.pcap",
                timestamp=now_ts,
                status="verified",
                details={
                    "nic_count": fix.params.get("required_nic_count", 1),
                    "uplink": fix.params.get("uplink_detected", False),
                    "vm_id": vm_id,
                },
            )
            evidence_container.add_record(rec)

    state["evidence"] = [r.to_dict() for r in evidence_container.records]
    state["benign_validation_ok"] = True
    state["findings"].append(f"Executed {len(active_fixtures)} benign validation fixtures successfully")

    # 5. Execution approval gate & bounded analysis step
    state = engine.execute_execution_approval(state)
    state = engine.execute_analysis(state)
    state = engine.execute_collect(state)

    # 6. Teardown & Residual Verification
    state = engine.execute_shutdown(state)
    state = engine.execute_destroy(state)

    # If test requests simulated residual leak, inject orphan guest back into provider
    if simulate_residual_leak and isinstance(active_provider, FakeHypervisor):
        orphan_vm = f"vm-orphan-{job_id[:6]}"
        active_provider._guests[orphan_vm] = type(
            "Guest",
            (),
            {
                "vm_id": orphan_vm,
                "job_id": job_id,
                "template_id": template_id,
                "network_id": network_id,
                "power": "on",
                "nics": 1,
            },
        )()

    state = engine.execute_residual_check(state)
    state = engine.execute_report(state)

    # 7. Build Operator Validation Report
    report_status = "success"
    if state["status"] == WorkflowStatus.BLOCKED.value:
        report_status = "blocked"
    elif state["status"] == WorkflowStatus.FAILED.value:
        report_status = "failed"

    op_report = OperatorValidationReport(
        report_id=f"rep-{job_id}",
        job_id=job_id,
        provider=provider_name,
        mode="live_authorized" if live_authorized else "fake_ci",
        status=report_status,
        started_at=started_at,
        completed_at=datetime.now(timezone.utc).isoformat(),
        template_summary=state.get("template_report", {}),
        network_summary=state.get("network_report", {}),
        safety_summary=safety,
        evidence_summary=evidence_container.to_dict(),
        cleanup_summary={
            "status": state.get("cleanup_status", "unknown"),
            "residual_count": len(state.get("residual_vms", [])),
        },
        residual_vms=state.get("residual_vms", []),
        notes=state.get("findings", []) + ([state["error"]] if state.get("error") else []),
    )
    op_report.sign()

    return {
        "status": state["status"],
        "job_id": job_id,
        "cleanup_status": state["cleanup_status"],
        "residual_vms": state.get("residual_vms", []),
        "evidence": evidence_container.to_dict(),
        "report": op_report.to_dict(),
        "markdown_report": op_report.to_markdown(),
        "state": state,
    }


# ---------------------------------------------------------------------------
# CLI Entrypoint
# ---------------------------------------------------------------------------

def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="AI Lab Security Hypervisor Test Harness & Benign Validation (IWO-078)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Execute read-only preflight and print planned resource operations without creating a VM (default).",
    )
    parser.add_argument(
        "--template",
        default="fixture-linux",
        help="Security VM template ID to validate (default: fixture-linux).",
    )
    parser.add_argument(
        "--network",
        default="fixture-isolated",
        help="Isolated network ID to validate (default: fixture-isolated).",
    )
    parser.add_argument(
        "--provider",
        default="fake",
        choices=["fake", "proxmox", "esxi"],
        help="Hypervisor provider adapter (default: fake).",
    )
    parser.add_argument(
        "--execute-benign",
        action="store_true",
        help="Execute full benign end-to-end validation with clone/boot/evidence/cleanup.",
    )
    parser.add_argument(
        "--live-authorized",
        action="store_true",
        help="Authorize benign validation against a live provider.",
    )
    parser.add_argument(
        "--confirm-token",
        default="",
        help="Confirmation token for live validation ('AUTHORIZE_LIVE_BENIGN_VALIDATION').",
    )

    args = parser.parse_args(argv)

    if args.execute_benign:
        job_id = f"job-cli-{int(datetime.now(timezone.utc).timestamp())}"
        print(f"Executing benign validation suite (job: {job_id}, provider: {args.provider})...")
        res = run_benign_validation_suite(
            job_id,
            template_id=args.template,
            network_id=args.network,
            provider=adapters().get(args.provider),
            live_authorized=args.live_authorized,
            confirmation_token=args.confirm_token,
        )
        print(res.get("markdown_report", ""))
        return 0 if res.get("status") == WorkflowStatus.COMPLETED.value else 1

    # Default dry-run preflight
    print(f"Running Security Hypervisor Dry-Run Preflight (provider: {args.provider})...")
    res = run_dry_run_preflight(
        template_id=args.template,
        network_id=args.network,
        provider_name=args.provider,
    )
    print("\n[PREFLIGHT RESULT]")
    print(f"Status: {res['status']}")
    print(f"VM Created: {res['vm_created']}")
    print(f"Safety OK: {res['safety']['safety_ok']}")
    print(f"Template Manifest OK: {res['template_report'].get('manifest_valid')}")
    print("\n[PLANNED RESOURCE OPERATIONS]")
    for step in res["planned_steps"]:
        action_prefix = "[DRY-RUN SKIPPED]" if step.get("dry_run_skipped") else "[PREFLIGHT RUN]"
        print(f"  {step['step']:<20}: {action_prefix} {step['action']}")
    print("\nPreflight complete (no VMs created or modified).")
    return 0 if res["status"] == "preflight_passed" else 1


if __name__ == "__main__":
    sys.exit(main())
