"""Normalized security event and evidence envelope (IWO-066)."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

SEVERITIES = ("info", "low", "medium", "high", "critical")
CLASSIFICATIONS = ("policy", "approval", "mcp", "finding", "evidence", "inventory")
PROVIDERS = ("antares", "defenseclaw", "vise", "mcp", "approval", "platform")
RETENTION_DEFAULT = "until-operator-purge"

_SECRET_KEY = re.compile(
    r"(password|secret|token|api_key|authorization|credential|private_key)",
    re.IGNORECASE,
)
_PAYLOAD_KEYS = frozenset(
    {"content", "bytes", "payload", "sample", "malware", "binary", "raw"}
)
_MAX_TEXT = 2000

EVENT_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "ai-lab://security/event-envelope/v1",
    "title": "AI Lab security event",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "schema_version",
        "event_id",
        "occurred_at",
        "provider",
        "severity",
        "classification",
        "agent_id",
        "resource_id",
        "run_id",
        "job_id",
        "tool",
        "approval_id",
        "summary",
        "evidence",
        "retention",
        "details",
    ],
    "properties": {
        "schema_version": {"const": 1},
        "event_id": {"type": "string", "minLength": 1},
        "occurred_at": {"type": "string", "minLength": 1},
        "provider": {"enum": list(PROVIDERS)},
        "severity": {"enum": list(SEVERITIES)},
        "classification": {"enum": list(CLASSIFICATIONS)},
        "agent_id": {"type": "string"},
        "resource_id": {"type": "string"},
        "run_id": {"type": "string"},
        "job_id": {"type": "string"},
        "tool": {"type": "string"},
        "approval_id": {"type": "string"},
        "summary": {"type": "string", "maxLength": _MAX_TEXT},
        "evidence": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["evidence_id", "locator", "sha256", "media_type", "byte_length"],
                "properties": {
                    "evidence_id": {"type": "string"},
                    "locator": {"type": "string"},
                    "sha256": {"type": "string"},
                    "media_type": {"type": "string"},
                    "byte_length": {"type": "integer", "minimum": 0},
                },
            },
        },
        "retention": {"type": "string"},
        "details": {"type": "object"},
    },
}


class EmbeddedPayloadRefused(ValueError):
    """Event tried to carry secret material or raw bytes."""


def _utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def redact(value: Any) -> Any:
    """Drop secret-like fields and refuse embedded payloads."""
    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        for key, item in value.items():
            name = str(key)
            if name.lower() in _PAYLOAD_KEYS:
                raise EmbeddedPayloadRefused(f"refusing embedded field {name}")
            if _SECRET_KEY.search(name):
                cleaned[name] = "[redacted]"
                continue
            cleaned[name] = redact(item)
        return cleaned
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, str):
        if len(value) > _MAX_TEXT:
            raise EmbeddedPayloadRefused("refusing oversized text")
        return value
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    raise EmbeddedPayloadRefused("refusing non-json value")


def _sha256(value: str) -> str:
    if value and (len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value.lower())):
        raise ValueError("sha256 must be 64 hex characters or empty")
    return value.lower()


@dataclass(frozen=True)
class EvidenceRef:
    evidence_id: str
    locator: str
    sha256: str
    media_type: str
    byte_length: int

    def to_dict(self) -> dict[str, Any]:
        if not self.evidence_id:
            raise ValueError("evidence_id is required")
        if not self.locator or "://" not in self.locator:
            raise ValueError("locator must be an external reference")
        if self.byte_length < 0:
            raise ValueError("byte_length must be zero or positive")
        return {
            "evidence_id": self.evidence_id,
            "locator": self.locator,
            "sha256": _sha256(self.sha256),
            "media_type": self.media_type,
            "byte_length": int(self.byte_length),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EvidenceRef:
        if any(key in data for key in _PAYLOAD_KEYS):
            raise EmbeddedPayloadRefused("evidence cannot embed bytes")
        ref = cls(
            evidence_id=str(data.get("evidence_id") or ""),
            locator=str(data.get("locator") or ""),
            sha256=str(data.get("sha256") or ""),
            media_type=str(data.get("media_type") or ""),
            byte_length=int(data.get("byte_length") or 0),
        )
        ref.to_dict()
        return ref


@dataclass(frozen=True)
class SecurityEvent:
    event_id: str
    occurred_at: str
    provider: str
    severity: str
    classification: str
    agent_id: str
    resource_id: str
    run_id: str
    job_id: str
    tool: str
    approval_id: str
    summary: str
    evidence: tuple[EvidenceRef, ...]
    retention: str
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        if self.provider not in PROVIDERS:
            raise ValueError(f"unknown provider {self.provider}")
        if self.severity not in SEVERITIES:
            raise ValueError(f"unknown severity {self.severity}")
        if self.classification not in CLASSIFICATIONS:
            raise ValueError(f"unknown classification {self.classification}")
        if not self.agent_id and not self.resource_id:
            raise ValueError("agent_id or resource_id is required")
        body = {
            "schema_version": 1,
            "event_id": self.event_id,
            "occurred_at": self.occurred_at,
            "provider": self.provider,
            "severity": self.severity,
            "classification": self.classification,
            "agent_id": self.agent_id,
            "resource_id": self.resource_id,
            "run_id": self.run_id,
            "job_id": self.job_id,
            "tool": self.tool,
            "approval_id": self.approval_id,
            "summary": self.summary,
            "evidence": [item.to_dict() for item in self.evidence],
            "retention": self.retention or RETENTION_DEFAULT,
            "details": redact(self.details),
        }
        return body

    @classmethod
    def create(
        cls,
        *,
        provider: str,
        severity: str,
        classification: str,
        summary: str,
        agent_id: str = "",
        resource_id: str = "",
        run_id: str = "",
        job_id: str = "",
        tool: str = "",
        approval_id: str = "",
        evidence: tuple[EvidenceRef, ...] | list[EvidenceRef] = (),
        retention: str = RETENTION_DEFAULT,
        details: dict[str, Any] | None = None,
        event_id: str = "",
        occurred_at: str = "",
    ) -> SecurityEvent:
        event = cls(
            event_id=event_id or str(uuid.uuid4()),
            occurred_at=occurred_at or _utcnow(),
            provider=provider,
            severity=severity,
            classification=classification,
            agent_id=agent_id,
            resource_id=resource_id,
            run_id=run_id,
            job_id=job_id,
            tool=tool,
            approval_id=approval_id,
            summary=summary,
            evidence=tuple(evidence),
            retention=retention,
            details=dict(details or {}),
        )
        event.to_dict()
        return event

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SecurityEvent:
        if int(data.get("schema_version") or 0) != 1:
            raise ValueError("schema_version must be 1")
        evidence = tuple(EvidenceRef.from_dict(item) for item in data.get("evidence") or [])
        return cls.create(
            event_id=str(data.get("event_id") or ""),
            occurred_at=str(data.get("occurred_at") or ""),
            provider=str(data.get("provider") or ""),
            severity=str(data.get("severity") or ""),
            classification=str(data.get("classification") or ""),
            summary=str(data.get("summary") or ""),
            agent_id=str(data.get("agent_id") or ""),
            resource_id=str(data.get("resource_id") or ""),
            run_id=str(data.get("run_id") or ""),
            job_id=str(data.get("job_id") or ""),
            tool=str(data.get("tool") or ""),
            approval_id=str(data.get("approval_id") or ""),
            evidence=evidence,
            retention=str(data.get("retention") or RETENTION_DEFAULT),
            details=dict(data.get("details") or {}),
        )
