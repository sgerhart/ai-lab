"""Cybersecurity Vise jobs (IWO-070). Records hashes and state. Never stores sample bytes."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from .events import EmbeddedPayloadRefused, EvidenceRef, redact
from .hypervisor import (
    AuthContext,
    HypervisorDenied,
    HypervisorPort,
    IsolationError,
    ProviderNotConfigured,
    adapters,
)

STATES = (
    "submitted",
    "preflight",
    "ready",
    "approval",
    "running",
    "collecting",
    "cleanup",
    "complete",
    "failed",
)
PROFILES = ("linux-static", "windows-static", "linux-behavioral", "windows-behavioral")
CLEANUP = ("pending", "verified", "failed")
_NEXT = {
    "submitted": {"preflight", "failed"},
    "preflight": {"ready", "failed"},
    "ready": {"approval", "running", "failed"},
    "approval": {"running", "failed"},
    "running": {"collecting", "failed"},
    "collecting": {"cleanup", "failed"},
    "cleanup": {"complete", "failed"},
    "failed": {"cleanup"},
    "complete": set(),
}
_PAYLOAD_KEYS = frozenset({"content", "bytes", "payload", "sample", "malware", "binary", "raw"})


class ViseTransitionError(ValueError):
    """Job cannot enter the requested state."""


def _sha256(value: str) -> str:
    text = value.strip().lower()
    if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
        raise ValueError("sha256 must be 64 hex characters")
    return text


def _execution_class(profile: str, requested: str) -> str:
    if profile.endswith("-behavioral"):
        return "untrusted"
    if requested not in {"", "benign", "untrusted"}:
        raise ValueError("execution_class must be benign or untrusted")
    return requested or "benign"


@dataclass
class ViseJob:
    job_id: str
    sha256: str
    byte_length: int
    media_type: str
    label: str
    profile: str
    provider: str
    template_id: str
    execution_class: str
    state: str = "submitted"
    cleanup_status: str = "pending"
    approval_id: str = ""
    vm_id: str = ""
    isolation: dict[str, Any] = field(default_factory=dict)
    evidence: list[EvidenceRef] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)
    failure: str = ""

    def to_dict(self) -> dict[str, Any]:
        if self.cleanup_status not in CLEANUP:
            raise ValueError("cleanup_status is required")
        return {
            "job_id": self.job_id,
            "sha256": self.sha256,
            "byte_length": self.byte_length,
            "media_type": self.media_type,
            "label": self.label,
            "profile": self.profile,
            "provider": self.provider,
            "template_id": self.template_id,
            "execution_class": self.execution_class,
            "state": self.state,
            "cleanup_status": self.cleanup_status,
            "approval_id": self.approval_id,
            "vm_id": self.vm_id,
            "isolation": dict(self.isolation),
            "evidence": [item.to_dict() for item in self.evidence],
            "findings": list(self.findings),
            "failure": self.failure,
        }


class ViseStore:
    def __init__(self, hypervisors: dict[str, HypervisorPort] | None = None) -> None:
        self.hypervisors = hypervisors if hypervisors is not None else adapters()
        self._jobs: dict[str, ViseJob] = {}

    def create(self, body: dict[str, Any]) -> ViseJob:
        self._reject_bytes(body)
        cleaned = redact(body)
        profile = str(cleaned.get("profile") or "linux-static")
        if profile not in PROFILES:
            raise ValueError("unknown analysis profile")
        provider = str(cleaned.get("provider") or "fake")
        if provider not in self.hypervisors:
            raise ValueError("unknown hypervisor provider")
        job = ViseJob(
            job_id=uuid.uuid4().hex,
            sha256=_sha256(str(cleaned.get("sha256") or "")),
            byte_length=int(cleaned.get("byte_length") or 0),
            media_type=str(cleaned.get("media_type") or "application/octet-stream"),
            label=str(cleaned.get("label") or "artifact")[:120],
            profile=profile,
            provider=provider,
            template_id=str(cleaned.get("template_id") or ""),
            execution_class=_execution_class(profile, str(cleaned.get("execution_class") or "")),
        )
        if job.byte_length < 0:
            raise ValueError("byte_length must be zero or positive")
        self._jobs[job.job_id] = job
        return job

    def get(self, job_id: str) -> ViseJob:
        try:
            return self._jobs[job_id]
        except KeyError as exc:
            raise KeyError(job_id) from exc

    def list(self) -> list[ViseJob]:
        return list(self._jobs.values())

    def advance(
        self,
        job_id: str,
        state: str,
        *,
        actor: str,
        approval_id: str = "",
        evidence: list[dict[str, Any]] | None = None,
        finding: str = "",
    ) -> ViseJob:
        job = self.get(job_id)
        if not actor:
            raise ViseTransitionError("actor is required")
        if state not in _NEXT.get(job.state, set()):
            raise ViseTransitionError(f"cannot move {job.state} to {state}")
        if state == "running" and job.execution_class == "untrusted" and not (approval_id or job.approval_id):
            raise ViseTransitionError("untrusted execution requires approval")
        if state == "complete" and job.cleanup_status != "verified":
            raise ViseTransitionError("complete requires verified cleanup")
        auth = AuthContext(job_id=job.job_id, actor=actor, approval_id=approval_id or job.approval_id)
        try:
            self._apply(job, state, auth, evidence or [], finding)
        except (ViseTransitionError, EmbeddedPayloadRefused):
            raise
        except (ProviderNotConfigured, IsolationError, HypervisorDenied, ValueError) as exc:
            job.state = "failed"
            job.failure = str(exc)
            if job.vm_id:
                job.cleanup_status = "pending"
            return job
        return job

    def _apply(
        self,
        job: ViseJob,
        state: str,
        auth: AuthContext,
        evidence: list[dict[str, Any]],
        finding: str,
    ) -> None:
        hypervisor = self.hypervisors[job.provider]
        if state == "preflight":
            checked = hypervisor.validate_template(job.template_id, auth)
            network = hypervisor.validate_network(_isolated_network(hypervisor), auth)
            job.isolation = {"template": checked, "network": network}
            job.state = "preflight"
            return
        if state == "ready":
            network = job.isolation.get("network") if isinstance(job.isolation, dict) else None
            if not isinstance(network, dict) or network.get("ok") is not True:
                raise ViseTransitionError("preflight has not passed")
            job.state = "ready"
            return
        if state == "approval":
            if not auth.approval_id:
                raise ViseTransitionError("approval_id is required")
            job.approval_id = auth.approval_id
            job.state = "approval"
            return
        if state == "running":
            if job.execution_class == "untrusted" and not job.approval_id and not auth.approval_id:
                raise ViseTransitionError("untrusted execution requires approval")
            job.approval_id = job.approval_id or auth.approval_id
            vm_id = hypervisor.clone(job.template_id, auth)
            hypervisor.power_on(vm_id, auth)
            if not hypervisor.guest_ready(vm_id, auth):
                raise ViseTransitionError("guest did not become ready")
            job.vm_id = vm_id
            job.state = "running"
            return
        if state == "collecting":
            refs = [EvidenceRef.from_dict(item) for item in evidence]
            if finding:
                job.findings.append(finding[:500])
            job.evidence.extend(refs)
            job.state = "collecting"
            return
        if state == "cleanup":
            if job.vm_id:
                hypervisor.power_off(job.vm_id, auth)
                hypervisor.destroy(job.vm_id, auth)
            left = hypervisor.residual(job.job_id)
            if left:
                job.cleanup_status = "failed"
                job.failure = "residual guests remain"
                job.state = "failed"
                return
            job.vm_id = ""
            job.cleanup_status = "verified"
            job.state = "cleanup"
            return
        if state == "complete":
            job.state = "complete"
            return
        if state == "failed":
            job.state = "failed"
            job.failure = job.failure or "operator marked the job failed"
            return
        raise ViseTransitionError(f"unhandled state {state}")

    def _reject_bytes(self, body: dict[str, Any]) -> None:
        for key in body:
            if str(key).lower() in _PAYLOAD_KEYS:
                raise EmbeddedPayloadRefused(f"refusing embedded field {key}")


def _isolated_network(hypervisor: HypervisorPort) -> str:
    inventory = hypervisor.inventory()
    networks = inventory.get("networks")
    if not isinstance(networks, list) or not networks:
        raise IsolationError("provider published no isolated network")
    first = networks[0]
    if not isinstance(first, dict) or first.get("nic_count") != 1 or first.get("uplink") is not False:
        raise IsolationError("analysis network must be one NIC with no uplink")
    return str(first["id"])
