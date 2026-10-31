"""Worker attestation and audit logging contracts."""

from __future__ import annotations

from pydantic import BaseModel, Field


class WorkerAttestation(BaseModel):
    """Cryptographic attestation and environment report from a worker node."""
    worker_id: str
    worker_role: str = Field(default="sandbox_worker")
    runtime_image_digest: str = Field(description="Pinned sha256 digest of container runtime")
    sandbox_policy_version: str = Field(default="sandbox-v1")
    vm_identity: str = Field(description="Hypervisor VM UUID or unique host tag")
    timestamp_epoch_ms: int
    egress_denied_verified: bool = Field(default=True)


class AuditEvent(BaseModel):
    """Immutable audit record for platform events and security decisions."""
    event_id: str
    actor: str
    action: str
    resource_id: str
    decision: str = "allow"
    timestamp_utc: str
    details: dict[str, object] = Field(default_factory=dict)
