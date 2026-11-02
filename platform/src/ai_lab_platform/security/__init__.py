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
from .lifecycle import (
    SecurityVmLifecycleEngine,
    SecurityVmWorkflowState,
    StepName,
    WorkflowStatus,
    build_security_vm_graph,
    init_workflow_state,
)
from .harness import (
    BENIGN_FILE_FIXTURE,
    BENIGN_NETWORK_FIXTURE,
    BENIGN_PROCESS_FIXTURE,
    STANDARD_BENIGN_FIXTURES,
    BenignExecutionEvidence,
    BenignFixture,
    EvidenceRecord,
    OperatorValidationReport,
    run_benign_validation_suite,
    run_dry_run_preflight,
    verify_host_and_network_safety,
    verify_provider_contract,
)
from .templates import (
    BASELINE_PROFILES,
    LINUX_BASELINE_PROFILE,
    WINDOWS_BASELINE_PROFILE,
    TemplateManifest,
    TemplateValidationReport,
    check_template_drift,
    validate_manifest_offline,
)

__all__ = [
    "AgentSecurityPosture",
    "BASELINE_PROFILES",
    "BENIGN_FILE_FIXTURE",
    "BENIGN_NETWORK_FIXTURE",
    "BENIGN_PROCESS_FIXTURE",
    "BenignExecutionEvidence",
    "BenignFixture",
    "DEFAULT_TRUSTED_NETWORK_DENYLIST",
    "EVENT_SCHEMA",
    "EvidenceRecord",
    "EvidenceRef",
    "IsolatedNetworkSpec",
    "LINUX_BASELINE_PROFILE",
    "McpRegistry",
    "OperatorValidationReport",
    "ProviderRegistry",
    "STANDARD_BENIGN_FIXTURES",
    "SecurityEvent",
    "SecurityVmLifecycleEngine",
    "SecurityVmWorkflowState",
    "StepName",
    "TemplateManifest",
    "TemplateValidationReport",
    "WINDOWS_BASELINE_PROFILE",
    "WorkflowStatus",
    "build_security_vm_graph",
    "check_template_drift",
    "default_providers",
    "evaluate_agent_posture",
    "evaluate_tool",
    "init_workflow_state",
    "run_benign_validation_suite",
    "run_dry_run_preflight",
    "validate_manifest_offline",
    "verify_host_and_network_safety",
    "verify_provider_contract",
]
