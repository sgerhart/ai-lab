"""Control-plane security domain (IWO-065).

Importing this package does not open sockets, read hypervisor inventory,
or change approval authority.
"""

from __future__ import annotations

from .events import EVENT_SCHEMA, EvidenceRef, SecurityEvent
from .hypervisor import DEFAULT_TRUSTED_NETWORK_DENYLIST, IsolatedNetworkSpec
from .mcp_registry import McpRegistry
from .policy_eval import evaluate_tool
from .posture import AgentSecurityPosture, evaluate_agent_posture
from .providers import ProviderRegistry, default_providers

__all__ = [
    "AgentSecurityPosture",
    "DEFAULT_TRUSTED_NETWORK_DENYLIST",
    "EVENT_SCHEMA",
    "EvidenceRef",
    "IsolatedNetworkSpec",
    "McpRegistry",
    "ProviderRegistry",
    "SecurityEvent",
    "default_providers",
    "evaluate_agent_posture",
    "evaluate_tool",
]
