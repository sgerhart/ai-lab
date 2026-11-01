"""Hypervisor port for the Security Compute Plane (IWO-071).

The fake adapter is the only implementation that runs. Proxmox and ESXi are
named so the contract can represent both, and both refuse every call until an
operator supplies an endpoint. This module does not open a socket.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class ProviderNotConfigured(RuntimeError):
    """Live hypervisor has no endpoint. Do not invent one."""


class IsolationError(ValueError):
    """Guest network failed the one-NIC isolated-bridge rule."""


class HypervisorDenied(PermissionError):
    """Mutating call lacked a job id and an actor."""


DEFAULT_TRUSTED_NETWORK_DENYLIST: tuple[str, ...] = (
    "tailscale",
    "lan",
    "home",
    "mgmt",
    "management",
    "trusted",
    "lab-trusted",
    "internal",
    "corp",
)


@dataclass(frozen=True)
class IsolatedNetworkSpec:
    network_id: str
    nic_count: int = 1
    uplink: bool = False
    controlled_egress: bool = False
    gateway_policy: str = "isolated"
    denylisted_identifiers: tuple[str, ...] = DEFAULT_TRUSTED_NETWORK_DENYLIST


@dataclass(frozen=True)
class AuthContext:
    job_id: str
    actor: str
    approval_id: str = ""

    def require_mutation(self) -> None:
        if not self.job_id or not self.actor:
            raise HypervisorDenied("mutating calls require a job id and an actor")


@dataclass
class _Guest:
    vm_id: str
    job_id: str
    template_id: str
    network_id: str
    power: str = "off"
    nics: int = 1


class HypervisorPort(Protocol):
    provider: str

    def inventory(self) -> dict[str, object]: ...

    def validate_template(
        self,
        template_id: str,
        auth: AuthContext,
        *,
        manifest: Any = None,
        expected_snapshot: str = "",
        required_tools: tuple[str, ...] | None = None,
    ) -> dict[str, object]: ...

    def validate_network(
        self,
        network_id: str,
        auth: AuthContext,
        *,
        denylist: tuple[str, ...] | None = None,
        allow_controlled_egress: bool = False,
    ) -> dict[str, object]: ...

    def clone(self, template_id: str, auth: AuthContext) -> str: ...

    def power_on(self, vm_id: str, auth: AuthContext) -> None: ...

    def power_off(self, vm_id: str, auth: AuthContext) -> None: ...

    def guest_ready(self, vm_id: str, auth: AuthContext) -> bool: ...

    def destroy(self, vm_id: str, auth: AuthContext) -> None: ...

    def residual(self, job_id: str) -> list[str]: ...


def _refuse(provider: str) -> ProviderNotConfigured:
    return ProviderNotConfigured(f"{provider} has no management endpoint")


class UnconfiguredHypervisor:
    """Placeholder for a live provider. It stores no URL and performs no I/O."""

    def __init__(self, provider: str) -> None:
        if provider not in {"proxmox", "esxi"}:
            raise ValueError("provider must be proxmox or esxi")
        self.provider = provider

    def inventory(self) -> dict[str, object]:
        raise _refuse(self.provider)

    def validate_template(
        self,
        template_id: str,
        auth: AuthContext,
        *,
        manifest: Any = None,
        expected_snapshot: str = "",
        required_tools: tuple[str, ...] | None = None,
    ) -> dict[str, object]:
        auth.require_mutation()
        raise _refuse(self.provider)

    def validate_network(
        self,
        network_id: str,
        auth: AuthContext,
        *,
        denylist: tuple[str, ...] | None = None,
        allow_controlled_egress: bool = False,
    ) -> dict[str, object]:
        auth.require_mutation()
        raise _refuse(self.provider)

    def clone(self, template_id: str, auth: AuthContext) -> str:
        auth.require_mutation()
        raise _refuse(self.provider)

    def power_on(self, vm_id: str, auth: AuthContext) -> None:
        auth.require_mutation()
        raise _refuse(self.provider)

    def power_off(self, vm_id: str, auth: AuthContext) -> None:
        auth.require_mutation()
        raise _refuse(self.provider)

    def guest_ready(self, vm_id: str, auth: AuthContext) -> bool:
        auth.require_mutation()
        raise _refuse(self.provider)

    def destroy(self, vm_id: str, auth: AuthContext) -> None:
        auth.require_mutation()
        raise _refuse(self.provider)

    def residual(self, job_id: str) -> list[str]:
        raise _refuse(self.provider)


class FakeHypervisor:
    """In-memory lifecycle for tests. Fixture names are not lab inventory."""

    provider = "fake"
    isolated_network = "fixture-isolated"
    templates = frozenset({"fixture-linux", "fixture-windows"})

    def __init__(self) -> None:
        self._guests: dict[str, _Guest] = {}
        self._seq = 0
        self._networks: dict[str, dict[str, Any]] = {
            self.isolated_network: {
                "id": self.isolated_network,
                "nic_count": 1,
                "uplink": False,
                "controlled_egress": False,
                "gateway_policy": "isolated",
            }
        }
        self._template_metadata: dict[str, dict[str, Any]] = {
            "fixture-linux": {
                "template_id": "fixture-linux",
                "os_type": "linux",
                "os_version": "ubuntu-24.04",
                "version": "1.0.0",
                "snapshot": "clean-baseline",
                "tools": ["wireshark", "tcpdump", "auditd", "yara", "strace", "gdb"],
                "sensors": ["auditd", "osquery"],
                "guest_agent_ready": True,
                "disposable_credentials_policy": "ephemeral-per-job",
                "network_policy": "isolated",
                "immutable": True,
            },
            "fixture-windows": {
                "template_id": "fixture-windows",
                "os_type": "windows",
                "os_version": "windows-11-23h2",
                "version": "1.0.0",
                "snapshot": "clean-baseline",
                "tools": ["sysinternals", "wireshark", "procmon", "procexp", "yara"],
                "sensors": ["sysmon", "osquery"],
                "guest_agent_ready": True,
                "disposable_credentials_policy": "ephemeral-per-job",
                "network_policy": "isolated",
                "immutable": True,
            },
        }

    def set_template_metadata(self, template_id: str, metadata: dict[str, Any]) -> None:
        self._template_metadata[template_id] = dict(metadata)
        if template_id not in self.templates:
            self.templates = frozenset(set(self.templates) | {template_id})

    def add_network(
        self,
        network_id: str,
        *,
        nic_count: int = 1,
        uplink: bool = False,
        controlled_egress: bool = False,
        gateway_policy: str = "isolated",
    ) -> None:
        self._networks[network_id] = {
            "id": network_id,
            "nic_count": nic_count,
            "uplink": uplink,
            "controlled_egress": controlled_egress,
            "gateway_policy": gateway_policy,
        }

    def inventory(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "endpoint": "",
            "templates": sorted(self.templates),
            "networks": list(self._networks.values()),
        }

    def validate_template(
        self,
        template_id: str,
        auth: AuthContext,
        *,
        manifest: Any = None,
        expected_snapshot: str = "",
        required_tools: tuple[str, ...] | None = None,
    ) -> dict[str, object]:
        auth.require_mutation()
        if template_id not in self.templates:
            raise ValueError("template is not allowlisted")
        tmpl = self._template_metadata.get(template_id, {})
        if tmpl.get("immutable") is False:
            raise IsolationError(f"template {template_id!r} is not marked immutable")
        if tmpl.get("guest_agent_ready") is False:
            raise IsolationError(f"template {template_id!r} guest agent is not ready")

        # Snapshot check
        target_snap = expected_snapshot or (getattr(manifest, "expected_snapshot", "") if manifest else "") or "clean-baseline"
        current_snap = tmpl.get("snapshot", "")
        if target_snap and current_snap != target_snap:
            raise IsolationError(
                f"template {template_id!r} expected snapshot {target_snap!r}, found {current_snap!r}"
            )

        # Required tools check
        tools_req = required_tools if required_tools is not None else (getattr(manifest, "tools", ()) if manifest else ())
        installed = set(tmpl.get("tools", [])) | set(tmpl.get("sensors", []))
        for t in tools_req:
            if t not in installed:
                raise IsolationError(f"template {template_id!r} is missing required tool: {t}")

        # Version drift check
        manifest_ver = getattr(manifest, "version", "") if manifest else ""
        actual_ver = str(tmpl.get("version", "1.0.0"))
        version_drift = bool(manifest_ver and actual_ver and manifest_ver != actual_ver)
        drift_details = (
            {"manifest_version": manifest_ver, "template_version": actual_ver}
            if version_drift
            else {}
        )

        return {
            "template_id": template_id,
            "allowlisted": True,
            "os_type": tmpl.get("os_type", "linux"),
            "version": actual_ver,
            "version_drift": version_drift,
            "drift_details": drift_details,
            "snapshot": current_snap,
            "tools": list(tmpl.get("tools", [])),
            "sensors": list(tmpl.get("sensors", [])),
            "immutable": True,
            "ok": True,
        }

    def validate_network(
        self,
        network_id: str,
        auth: AuthContext,
        *,
        denylist: tuple[str, ...] | None = None,
        allow_controlled_egress: bool = False,
    ) -> dict[str, object]:
        auth.require_mutation()
        effective_denylist = denylist if denylist is not None else DEFAULT_TRUSTED_NETWORK_DENYLIST
        net_lower = network_id.lower()
        for bad in effective_denylist:
            if bad.lower() in net_lower:
                raise IsolationError(f"network {network_id!r} is denylisted as trusted ({bad})")
        if network_id not in self._networks:
            raise IsolationError(f"network {network_id!r} is not known to provider")
        net = self._networks[network_id]
        nic_count = int(net.get("nic_count", 1))
        if nic_count != 1:
            raise IsolationError(f"analysis guest requires exactly 1 NIC, found {nic_count}")
        if net.get("uplink", False):
            raise IsolationError(f"network {network_id!r} has an active uplink to trusted network")
        has_egress = bool(net.get("controlled_egress", False))
        if has_egress and not allow_controlled_egress:
            raise IsolationError("controlled egress defaults to false and was not permitted")
        return {
            "network_id": network_id,
            "nic_count": 1,
            "uplink": False,
            "controlled_egress": has_egress and allow_controlled_egress,
            "gateway_policy": str(net.get("gateway_policy") or "isolated"),
            "denylist_cleared": True,
            "ok": True,
        }

    def clone(self, template_id: str, auth: AuthContext) -> str:
        auth.require_mutation()
        self.validate_template(template_id, auth)
        self._seq += 1
        vm_id = f"vm-{self._seq}"
        self._guests[vm_id] = _Guest(
            vm_id=vm_id,
            job_id=auth.job_id,
            template_id=template_id,
            network_id=self.isolated_network,
        )
        return vm_id

    def power_on(self, vm_id: str, auth: AuthContext) -> None:
        guest = self._owned(vm_id, auth)
        guest.power = "on"

    def power_off(self, vm_id: str, auth: AuthContext) -> None:
        guest = self._owned(vm_id, auth)
        guest.power = "off"

    def guest_ready(self, vm_id: str, auth: AuthContext) -> bool:
        guest = self._owned(vm_id, auth)
        return guest.power == "on" and guest.nics == 1

    def destroy(self, vm_id: str, auth: AuthContext) -> None:
        self._owned(vm_id, auth)
        self._guests.pop(vm_id, None)

    def residual(self, job_id: str) -> list[str]:
        return sorted(guest.vm_id for guest in self._guests.values() if guest.job_id == job_id)

    def _owned(self, vm_id: str, auth: AuthContext) -> _Guest:
        auth.require_mutation()
        guest = self._guests.get(vm_id)
        if guest is None or guest.job_id != auth.job_id:
            raise HypervisorDenied("vm does not belong to this job")
        return guest


def adapters() -> dict[str, HypervisorPort]:
    return {
        "fake": FakeHypervisor(),
        "proxmox": UnconfiguredHypervisor("proxmox"),
        "esxi": UnconfiguredHypervisor("esxi"),
    }
