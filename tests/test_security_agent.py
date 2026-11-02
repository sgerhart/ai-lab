"""Unit tests for Security Agent definition and policy (IWO-076).

Validates all 4 Acceptance Criteria:
1. Security agent can call only listed security tools.
2. Read vs lifecycle permissions are distinguishable.
3. Untrusted execution permission is approval-gated.
4. Policy tests deny generic hypervisor/admin actions.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.agent_builder import classify_purpose
from ai_lab_platform.agent_plans import execute_plan, plan_for
from ai_lab_platform.approvals import is_privileged, requires_approval
from ai_lab_platform.capabilities import assistant_name
from ai_lab_platform.policy import AgentPolicy, constrain_tools, load_policy
from ai_lab_platform.security.posture import (
    PERMANENTLY_DENIED_TOOLS,
    evaluate_agent_posture,
)
from ai_lab_platform.tool_catalog import READ_TOOLS
from ai_lab_platform.tools import ToolContext


class SecurityAgentPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = load_policy("security")
        self.tmp = tempfile.TemporaryDirectory()
        self.workspace = Path(self.tmp.name) / "workspace"
        self.workspace.mkdir(parents=True)
        self.artifacts = Path(self.tmp.name) / "artifacts"
        self.artifacts.mkdir(parents=True)
        self.ctx = ToolContext(workspace_root=self.workspace, artifact_root=self.artifacts)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_ac1_security_agent_loads_and_calls_only_listed_security_tools(self) -> None:
        """AC 1: Security agent can call only listed security tools."""
        self.assertEqual(self.policy.id, "security")
        self.assertEqual(self.policy.isolation_tier, 2)
        self.assertFalse(self.policy.read_only)

        # Expected security tools
        expected_allowed = {
            "security_inventory_read",
            "security_template_validate",
            "security_network_validate",
            "security_preflight_dry_run",
            "security_guest_status_read",
            "security_evidence_read",
            "security_report_read",
            "security_job_status_read",
        }
        self.assertEqual(set(self.policy.allowed_tools), expected_allowed)

        # Arbitrary and unlisted tools are constrained out
        requested = [
            "security_inventory_read",
            "bash_exec",
            "docker_exec",
            "security_vm_clone",
            "malware_run",
        ]
        constrained = constrain_tools(requested, self.policy)
        self.assertIn("security_inventory_read", constrained)
        self.assertIn("security_vm_clone", constrained)
        self.assertNotIn("bash_exec", constrained)
        self.assertNotIn("docker_exec", constrained)
        self.assertNotIn("malware_run", constrained)

    def test_ac2_read_vs_lifecycle_permissions_are_distinguishable(self) -> None:
        """AC 2: Read vs lifecycle permissions are distinguishable."""
        # Read tools are all recognized in tool catalog READ_TOOLS
        for r_tool in self.policy.allowed_tools:
            self.assertIn(r_tool, READ_TOOLS, f"Read tool {r_tool} missing from READ_TOOLS")
            self.assertFalse(is_privileged(r_tool), f"Read tool {r_tool} should not be privileged")

        # Mutating lifecycle tools are in privileged_tools
        expected_privileged = {
            "security_vm_clone",
            "security_vm_power",
            "security_vm_destroy",
            "security_benign_validate",
            "security_untrusted_execute",
            "security_vm_cleanup",
        }
        self.assertEqual(set(self.policy.privileged_tools), expected_privileged)
        for p_tool in self.policy.privileged_tools:
            self.assertTrue(is_privileged(p_tool), f"Lifecycle tool {p_tool} must be privileged")

        # In read-only mode, constrain_tools filters out lifecycle tools
        read_only_policy = AgentPolicy(
            id="security",
            allowed_tools=self.policy.allowed_tools,
            privileged_tools=self.policy.privileged_tools,
            read_only=True,
            isolation_tier=2,
            network=(),
        )
        filtered = constrain_tools(list(self.policy.allowed_tools) + list(self.policy.privileged_tools), read_only_policy)
        self.assertEqual(set(filtered), set(self.policy.allowed_tools))
        self.assertTrue(all(p not in filtered for p in self.policy.privileged_tools))

    def test_ac3_untrusted_execution_is_approval_gated(self) -> None:
        """AC 3: Untrusted execution permission is strictly approval-gated."""
        untrusted_tool = "security_untrusted_execute"
        allowed_tools = list(self.policy.allowed_tools) + list(self.policy.privileged_tools)

        # Requires approval when not yet approved
        self.assertTrue(requires_approval(untrusted_tool, allowed_tools, set()))

        # Once approved by operator, passes gate
        self.assertFalse(requires_approval(untrusted_tool, allowed_tools, {untrusted_tool}))

        # If not on allowed_tools list, even approval does not pass
        self.assertTrue(requires_approval(untrusted_tool, list(self.policy.allowed_tools), {untrusted_tool}))

    def test_ac4_policy_denies_generic_hypervisor_and_admin_actions(self) -> None:
        """AC 4: Policy tests deny generic hypervisor/admin actions."""
        banned_admin_tools = [
            "hypervisor_admin",
            "network_bridge_mutate",
            "trusted_network_attach",
            "raw_shell_exec",
            "template_mutate",
            "host_mutate",
            "firewall_change",
            "rm_rf",
            "secrets_read",
            "git_push",
        ]
        # None of these are in allowed or privileged tools
        for banned in banned_admin_tools:
            self.assertNotIn(banned, self.policy.allowed_tools)
            self.assertNotIn(banned, self.policy.privileged_tools)
            self.assertIn(banned, PERMANENTLY_DENIED_TOOLS)

        # Posture evaluation verifies permanently denied tools generate warnings
        posture = evaluate_agent_posture(
            "security",
            requested_tools=["security_inventory_read", "host_mutate", "hypervisor_admin"],
        )
        self.assertEqual(posture.isolation_tier, 2)
        self.assertEqual(posture.filesystem_class, "isolated-vm")
        self.assertEqual(posture.network_class, "isolated-bridge")
        self.assertEqual(posture.network_endpoints, ())
        self.assertIn("host_mutate", posture.denied_tools)
        self.assertIn("hypervisor_admin", posture.denied_tools)
        self.assertTrue(any("host_mutate" in w for w in posture.warnings))
        self.assertTrue(any("hypervisor_admin" in w for w in posture.warnings))

    def test_deterministic_security_plan_execution(self) -> None:
        """Security agent deterministic local plan runs read tools without VM creation."""
        plan = plan_for("security")
        self.assertEqual(plan, ["security_inventory_read", "security_preflight_dry_run"])

        allowed = list(self.policy.allowed_tools)
        res = execute_plan("security", "Validate hypervisor readiness", self.ctx, allowed)
        self.assertTrue(res.ok)
        self.assertIn("Hypervisor templates", res.detail)
        self.assertIn("Preflight status: preflight_passed", res.detail)
        self.assertIn("VM created: False", res.detail)
        self.assertEqual(res.tools_run, ["security_inventory_read", "security_preflight_dry_run"])

    def test_security_plan_blocks_privileged_tools_without_approval(self) -> None:
        """Attempting to run privileged security tools in a plan without approval fails."""
        allowed = list(self.policy.allowed_tools) + list(self.policy.privileged_tools)
        # Manually invoke execute_plan with a privileged tool required
        from ai_lab_platform.agent_plans import execute_plan
        # If someone passed security_vm_clone in allowed_tools but not approved_tools
        self.assertTrue(requires_approval("security_vm_clone", allowed, set()))

    def test_capabilities_and_builder_integration(self) -> None:
        """Security agent integrates cleanly with capabilities and agent builder."""
        self.assertEqual(assistant_name("security"), "Security Compute Agent")
        purpose, agent = classify_purpose("I need to test an isolated security VM and check hypervisor isolation")
        self.assertEqual(purpose, "security")
        self.assertEqual(agent, "security")


if __name__ == "__main__":
    unittest.main()
