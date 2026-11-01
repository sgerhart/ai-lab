"""IWO-068 — Agent Studio security posture unit and contract tests (FEAT-018)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.agent_definitions import AgentDefinition, AgentDefinitionStore
from ai_lab_platform.security.mcp_registry import McpRegistry
from ai_lab_platform.security.posture import (
    PERMANENTLY_DENIED_TOOLS,
    AgentSecurityPosture,
    evaluate_agent_posture,
)

try:
    from fastapi.testclient import TestClient
    from langgraph.checkpoint.memory import MemorySaver

    from ai_lab_platform.control_app import create_control_app
    from ai_lab_platform.model_router import ModelRouter
    from ai_lab_platform.store import SqliteStore

    _HAS_FASTAPI = True
except ImportError:
    _HAS_FASTAPI = False


class AgentSecurityPostureUnitTests(unittest.TestCase):
    def test_coding_assistant_posture(self) -> None:
        # Without worktree/patch tools -> Tier 1 read-only
        read_posture = evaluate_agent_posture("coding-assistant", requested_tools=["repo_read"])
        self.assertEqual(read_posture.isolation_tier, 1)
        self.assertEqual(read_posture.filesystem_class, "isolated-worktree")
        self.assertEqual(read_posture.network_class, "none")
        self.assertEqual(read_posture.network_endpoints, ())
        self.assertIn("apply_patch", read_posture.approval_required_tools)
        self.assertIn("git_commit", read_posture.approval_required_tools)

        # With patch/worktree tools -> Tier 2 isolated worktree sandbox
        sandbox_posture = evaluate_agent_posture(
            "coding-assistant",
            requested_tools=["repo_read", "sandbox", "apply_patch"],
        )
        self.assertEqual(sandbox_posture.isolation_tier, 2)
        self.assertEqual(sandbox_posture.filesystem_class, "isolated-worktree")
        self.assertIn("apply_patch", sandbox_posture.intent_vs_policy["enforced_approval_required"])

    def test_personal_agent_posture(self) -> None:
        posture = evaluate_agent_posture("personal", requested_tools=["memory", "web", "files"])
        self.assertEqual(posture.isolation_tier, 0)
        self.assertEqual(posture.filesystem_class, "user-vault-scoped")
        self.assertEqual(posture.network_class, "egress-allowlist")
        self.assertTrue(posture.audit_logging)
        self.assertEqual(len(posture.approval_required_tools), 0)

    def test_research_agent_posture(self) -> None:
        posture = evaluate_agent_posture("research", requested_tools=["web", "reports"])
        self.assertEqual(posture.isolation_tier, 1)
        self.assertEqual(posture.filesystem_class, "reports-scoped")
        self.assertEqual(posture.network_class, "egress-allowlist")

    def test_lab_operations_posture(self) -> None:
        posture = evaluate_agent_posture("lab-operations", requested_tools=["files", "memory"])
        self.assertEqual(posture.isolation_tier, 0)
        self.assertEqual(posture.filesystem_class, "read-only")
        self.assertEqual(posture.network_class, "tailnet-client")

    def test_vuln_localize_posture(self) -> None:
        posture = evaluate_agent_posture("vuln-localize", requested_tools=["localize"])
        self.assertEqual(posture.isolation_tier, 1)
        self.assertEqual(posture.network_class, "none")

    def test_permanently_denied_tools_generate_warnings(self) -> None:
        posture = evaluate_agent_posture(
            "coding-assistant",
            requested_tools=["repo_read", "git_push", "rm_rf"],
        )
        self.assertIn("git_push", PERMANENTLY_DENIED_TOOLS)
        self.assertIn("rm_rf", PERMANENTLY_DENIED_TOOLS)
        # Denied tools must not be in allowed list
        self.assertNotIn("git_push", posture.intent_vs_policy["enforced_allowed"])
        self.assertNotIn("rm_rf", posture.intent_vs_policy["enforced_allowed"])
        # Warning recorded
        self.assertTrue(any("git_push" in w for w in posture.warnings))
        self.assertTrue(any("rm_rf" in w for w in posture.warnings))

    def test_unlisted_mcp_servers_flagged(self) -> None:
        tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        tmp.write(b'{"policy":"deny-unlisted","servers":[{"id":"authorized-mcp"}]}')
        tmp.close()
        registry = McpRegistry(allowlist_path=Path(tmp.name))

        posture = evaluate_agent_posture(
            "lab-operations",
            mcp_server_ids=["authorized-mcp", "untrusted-mcp"],
            mcp_registry=registry,
        )
        statuses = {s["id"]: s["status"] for s in posture.mcp_servers}
        self.assertEqual(statuses["authorized-mcp"], "authorized")
        self.assertEqual(statuses["untrusted-mcp"], "unlisted_denied")
        self.assertTrue(any("untrusted-mcp" in w for w in posture.warnings))

    def test_posture_to_dict_serialization(self) -> None:
        posture = evaluate_agent_posture("personal", title="My Assistant")
        data = posture.to_dict()
        self.assertEqual(data["agent_id"], "personal")
        self.assertEqual(data["title"], "My Assistant")
        self.assertIn("isolation_tier", data)
        self.assertIn("filesystem_class", data)
        self.assertIn("network_class", data)
        self.assertIn("approval_required_tools", data)
        self.assertIn("intent_vs_policy", data)


@unittest.skipUnless(_HAS_FASTAPI, "fastapi not installed")
class AgentSecurityPostureApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        store = SqliteStore(Path(self.tmp.name) / "wo.sqlite")
        self.app = create_control_app(
            store=store,
            checkpointer=MemorySaver(),
            token="lab-token",
            dispatch=lambda _p: {"ok": True, "detail": "x"},
            model_router=ModelRouter(backends={}),
        )
        self.app.state.agent_definition_store = AgentDefinitionStore(Path(self.tmp.name) / "defs.sqlite")
        self.client = TestClient(self.app)
        self.h = {"Authorization": "Bearer lab-token"}

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_draft_security_posture_endpoint(self) -> None:
        res = self.client.post(
            "/v1/agent-studio/security-posture",
            headers=self.h,
            json={
                "agent": "coding-assistant",
                "title": "Engineer",
                "tools": ["repo_read", "apply_patch"],
            },
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["agent_id"], "coding-assistant")
        self.assertEqual(data["isolation_tier"], 2)
        self.assertEqual(data["filesystem_class"], "isolated-worktree")
        self.assertIn("apply_patch", data["approval_required_tools"])

    def test_get_definition_security_posture_endpoint(self) -> None:
        created = self.client.post(
            "/v1/agent-definitions",
            headers=self.h,
            json={
                "title": "Ops Agent",
                "agent": "lab-operations",
                "system_prompt": "Help lab",
                "tools": ["files_read"],
            },
        )
        self.assertEqual(created.status_code, 200)
        def_id = created.json()["id"]

        # Directly enriched in creation response
        self.assertIn("security_posture", created.json())
        self.assertEqual(created.json()["security_posture"]["isolation_tier"], 0)

        # Dedicated endpoint
        res = self.client.get(f"/v1/agent-definitions/{def_id}/security-posture", headers=self.h)
        self.assertEqual(res.status_code, 200)
        posture = res.json()
        self.assertEqual(posture["agent_id"], "lab-operations")
        self.assertEqual(posture["filesystem_class"], "read-only")

        # In list endpoint
        listed = self.client.get("/v1/agent-definitions", headers=self.h)
        self.assertEqual(listed.status_code, 200)
        defs = listed.json()["definitions"]
        self.assertEqual(len(defs), 1)
        self.assertIn("security_posture", defs[0])


if __name__ == "__main__":
    unittest.main()
