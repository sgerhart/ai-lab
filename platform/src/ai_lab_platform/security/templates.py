"""Security Compute VM template manifest schema and validation (IWO-073).

Acceptance criteria:
1. Template manifest validates offline.
2. Missing required tool/snapshot fails preflight.
3. Version drift is reported.
4. Windows/Linux profiles exist.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_SECRET_PATTERN = re.compile(
    r"(password|secret|token|api_key|authorization|credential|private_key)",
    re.IGNORECASE,
)
_REQUIRED_FIELDS = frozenset(
    {
        "template_id",
        "os_type",
        "os_version",
        "version",
        "expected_snapshot",
        "tools",
        "sensors",
    }
)
_VALID_OS = frozenset({"linux", "windows"})


@dataclass(frozen=True)
class TemplateManifest:
    template_id: str
    os_type: str
    os_version: str
    version: str
    expected_snapshot: str
    tools: tuple[str, ...]
    sensors: tuple[str, ...]
    network_policy: str = "isolated"
    guest_agent_ready: bool = True
    disposable_credentials_policy: str = "ephemeral-per-job"
    immutable: bool = True
    min_ram_mb: int = 4096
    min_cpu_cores: int = 2
    hashes: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "os_type": self.os_type,
            "os_version": self.os_version,
            "version": self.version,
            "expected_snapshot": self.expected_snapshot,
            "tools": list(self.tools),
            "sensors": list(self.sensors),
            "network_policy": self.network_policy,
            "guest_agent_ready": self.guest_agent_ready,
            "disposable_credentials_policy": self.disposable_credentials_policy,
            "immutable": self.immutable,
            "min_ram_mb": self.min_ram_mb,
            "min_cpu_cores": self.min_cpu_cores,
            "hashes": dict(self.hashes),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TemplateManifest:
        report = validate_manifest_offline(data)
        if not report.valid:
            raise ValueError(f"Invalid template manifest: {'; '.join(report.errors)}")
        return cls(
            template_id=str(data["template_id"]),
            os_type=str(data["os_type"]),
            os_version=str(data["os_version"]),
            version=str(data["version"]),
            expected_snapshot=str(data["expected_snapshot"]),
            tools=tuple(str(t) for t in data.get("tools", ())),
            sensors=tuple(str(s) for s in data.get("sensors", ())),
            network_policy=str(data.get("network_policy", "isolated")),
            guest_agent_ready=bool(data.get("guest_agent_ready", True)),
            disposable_credentials_policy=str(data.get("disposable_credentials_policy", "ephemeral-per-job")),
            immutable=bool(data.get("immutable", True)),
            min_ram_mb=int(data.get("min_ram_mb", 4096)),
            min_cpu_cores=int(data.get("min_cpu_cores", 2)),
            hashes={str(k): str(v) for k, v in dict(data.get("hashes", {})).items()},
        )


@dataclass(frozen=True)
class TemplateValidationReport:
    valid: bool
    template_id: str
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    version_drift: bool = False
    drift_details: dict[str, str] = field(default_factory=dict)
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "template_id": self.template_id,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "version_drift": self.version_drift,
            "drift_details": dict(self.drift_details),
            "details": dict(self.details),
        }


def _check_secrets(obj: Any, path: str = "") -> list[str]:
    errors: list[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            k_str = str(k)
            if k_str == "disposable_credentials_policy":
                continue
            curr = f"{path}.{k_str}" if path else k_str
            if _SECRET_PATTERN.search(k_str):
                errors.append(f"Secret-like key name forbidden in manifest: {curr}")
            errors.extend(_check_secrets(v, curr))
    elif isinstance(obj, (list, tuple)):
        for idx, item in enumerate(obj):
            errors.extend(_check_secrets(item, f"{path}[{idx}]"))
    elif isinstance(obj, str):
        if "-----BEGIN" in obj:
            errors.append(f"PEM encoded key or certificate payload embedded in manifest at {path}")
    return errors


def validate_manifest_offline(data: dict[str, Any] | TemplateManifest) -> TemplateValidationReport:
    """Validate a template manifest completely offline without network or hypervisor access."""
    if isinstance(data, TemplateManifest):
        raw = data.to_dict()
    elif isinstance(data, dict):
        raw = data
    else:
        return TemplateValidationReport(
            valid=False,
            template_id="",
            errors=("manifest must be a dictionary or TemplateManifest instance",),
        )

    errors: list[str] = []
    warnings: list[str] = []
    template_id = str(raw.get("template_id") or "")

    # Secret checks
    secret_errors = _check_secrets(raw)
    errors.extend(secret_errors)

    # Required field presence
    for req in _REQUIRED_FIELDS:
        if req not in raw or raw[req] is None or raw[req] == "":
            errors.append(f"missing required field: {req}")

    os_type = str(raw.get("os_type") or "").lower()
    if os_type and os_type not in _VALID_OS:
        errors.append(f"invalid os_type {os_type!r}; must be one of {sorted(_VALID_OS)}")

    # Tools must be non-empty list
    tools = raw.get("tools")
    if not isinstance(tools, (list, tuple)) or not tools:
        errors.append("tools must be a non-empty sequence of tool names")

    # Sensors must be list
    sensors = raw.get("sensors")
    if not isinstance(sensors, (list, tuple)):
        errors.append("sensors must be a sequence of sensor names")

    # Expected snapshot must be specified
    snapshot = str(raw.get("expected_snapshot") or "").strip()
    if not snapshot:
        errors.append("expected_snapshot cannot be blank")

    # Network policy must be isolated
    net_policy = str(raw.get("network_policy") or "").lower()
    if net_policy and net_policy != "isolated":
        errors.append(f"network_policy must be 'isolated', found {net_policy!r}")

    # Golden templates must be immutable
    if "immutable" in raw and raw["immutable"] is not True:
        errors.append("immutable must be True; security agent cannot mutate golden templates")

    # RAM and CPU sane minimums
    if "min_ram_mb" in raw and int(raw.get("min_ram_mb") or 0) < 1024:
        warnings.append("min_ram_mb is below recommended 1024 MB")
    if "min_cpu_cores" in raw and int(raw.get("min_cpu_cores") or 0) < 1:
        errors.append("min_cpu_cores must be at least 1")

    return TemplateValidationReport(
        valid=len(errors) == 0,
        template_id=template_id,
        errors=tuple(errors),
        warnings=tuple(warnings),
        details={"os_type": os_type, "version": str(raw.get("version") or "")},
    )


def check_template_drift(
    manifest: TemplateManifest,
    template_version: str,
) -> tuple[bool, dict[str, str]]:
    """Compare manifest version with actual template version to report version drift."""
    mv = manifest.version.strip()
    tv = template_version.strip()
    if mv and tv and mv != tv:
        return True, {"manifest_version": mv, "template_version": tv}
    return False, {}


LINUX_BASELINE_PROFILE = TemplateManifest(
    template_id="fixture-linux",
    os_type="linux",
    os_version="ubuntu-24.04",
    version="1.0.0",
    expected_snapshot="clean-baseline",
    tools=("wireshark", "tcpdump", "auditd", "yara", "strace", "gdb"),
    sensors=("auditd", "osquery"),
    network_policy="isolated",
    guest_agent_ready=True,
    disposable_credentials_policy="ephemeral-per-job",
    immutable=True,
    min_ram_mb=4096,
    min_cpu_cores=2,
    hashes={"root_fs_sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"},
)

WINDOWS_BASELINE_PROFILE = TemplateManifest(
    template_id="fixture-windows",
    os_type="windows",
    os_version="windows-11-23h2",
    version="1.0.0",
    expected_snapshot="clean-baseline",
    tools=("sysinternals", "wireshark", "procmon", "procexp", "yara"),
    sensors=("sysmon", "osquery"),
    network_policy="isolated",
    guest_agent_ready=True,
    disposable_credentials_policy="ephemeral-per-job",
    immutable=True,
    min_ram_mb=4096,
    min_cpu_cores=2,
    hashes={"vhd_sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"},
)

BASELINE_PROFILES: dict[str, TemplateManifest] = {
    "fixture-linux": LINUX_BASELINE_PROFILE,
    "linux-baseline": LINUX_BASELINE_PROFILE,
    "fixture-windows": WINDOWS_BASELINE_PROFILE,
    "windows-baseline": WINDOWS_BASELINE_PROFILE,
}


def load_manifest_file(file_path: str | Path) -> TemplateManifest:
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Manifest file not found: {file_path}")
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return TemplateManifest.from_dict(data)


def main() -> int:
    if len(sys.argv) < 3 or sys.argv[1] != "validate":
        print("Usage: python3 -m ai_lab_platform.security.templates validate <manifest.json>", file=sys.stderr)
        return 1
    file_path = Path(sys.argv[2])
    try:
        manifest = load_manifest_file(file_path)
        print(f"PASS: {manifest.template_id} ({manifest.os_type} v{manifest.version}) validates offline.")
        return 0
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
