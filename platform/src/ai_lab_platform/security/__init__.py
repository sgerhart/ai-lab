"""Control-plane security domain (IWO-065).

Importing this package does not open sockets, read hypervisor inventory,
or change approval authority.
"""

from __future__ import annotations

from .events import EVENT_SCHEMA, EvidenceRef, SecurityEvent
from .mcp_registry import McpRegistry
from .policy_eval import evaluate_tool
from .providers import ProviderRegistry, default_providers

__all__ = [
    "EVENT_SCHEMA",
    "EvidenceRef",
    "McpRegistry",
    "ProviderRegistry",
    "SecurityEvent",
    "default_providers",
    "evaluate_tool",
]
