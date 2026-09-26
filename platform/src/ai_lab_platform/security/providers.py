"""Security provider registration. Descriptors carry no endpoints or credentials."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class SecurityProvider(Protocol):
    id: str
    kind: str

    def describe(self) -> dict[str, str]:
        """Return local metadata. Must not perform I/O."""


@dataclass(frozen=True)
class DescriptorProvider:
    id: str
    kind: str
    title: str

    def describe(self) -> dict[str, str]:
        return {
            "id": self.id,
            "kind": self.kind,
            "title": self.title,
            "network": "none",
        }


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, SecurityProvider] = {}

    def register(self, provider: SecurityProvider) -> None:
        if not provider.id or not provider.kind:
            raise ValueError("provider id and kind are required")
        if provider.id in self._providers:
            raise ValueError(f"provider already registered: {provider.id}")
        self._providers[provider.id] = provider

    def get(self, provider_id: str) -> SecurityProvider:
        try:
            return self._providers[provider_id]
        except KeyError as exc:
            raise KeyError(provider_id) from exc

    def list(self) -> tuple[dict[str, str], ...]:
        return tuple(provider.describe() for provider in self._providers.values())


def default_providers() -> ProviderRegistry:
    """Antares, DefenseClaw, and Vise as optional integrations. No live calls."""
    registry = ProviderRegistry()
    registry.register(DescriptorProvider("antares", "antares", "Antares software-security service"))
    registry.register(DescriptorProvider("defenseclaw", "defenseclaw", "DefenseClaw governance summary"))
    registry.register(DescriptorProvider("vise", "vise", "Cybersecurity Vise job control"))
    return registry
