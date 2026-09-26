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

    def validate_template(self, template_id: str, auth: AuthContext) -> dict[str, object]: ...

    def validate_network(self, network_id: str, auth: AuthContext) -> dict[str, object]: ...

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

    def validate_template(self, template_id: str, auth: AuthContext) -> dict[str, object]:
        auth.require_mutation()
        raise _refuse(self.provider)

    def validate_network(self, network_id: str, auth: AuthContext) -> dict[str, object]:
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

    def inventory(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "endpoint": "",
            "templates": sorted(self.templates),
            "networks": [
                {
                    "id": self.isolated_network,
                    "nic_count": 1,
                    "uplink": False,
                    "controlled_egress": False,
                }
            ],
        }

    def validate_template(self, template_id: str, auth: AuthContext) -> dict[str, object]:
        auth.require_mutation()
        if template_id not in self.templates:
            raise ValueError("template is not allowlisted")
        return {"template_id": template_id, "allowlisted": True}

    def validate_network(self, network_id: str, auth: AuthContext) -> dict[str, object]:
        auth.require_mutation()
        if network_id != self.isolated_network:
            raise IsolationError("analysis guest can attach only the isolated fixture network")
        return {
            "network_id": network_id,
            "nic_count": 1,
            "uplink": False,
            "controlled_egress": False,
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
