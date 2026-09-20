"""Deterministic plans for catalog agents. No LLM, no network fetch."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.agent_plans import _execute, execute_plan, plan_for
from ai_lab_platform.approvals import PRIVILEGED_TOOLS
from ai_lab_platform.policy import constrain_tools, load_policy
from ai_lab_platform.tools import ToolContext, ToolError


def _ctx(workspace: Path, artifacts: Path, bounded_scope: str = "") -> ToolContext:
    return ToolContext(workspace_root=workspace, artifact_root=artifacts, bounded_scope=bounded_scope)


class AgentPlanTests(unittest.TestCase):
    def test_catalog_plans_are_non_privileged(self) -> None:
        for agent in ("lab-operations", "research", "development"):
            plan = plan_for(agent)
            self.assertTrue(plan)
            overlap = PRIVILEGED_TOOLS.intersection(plan)
            self.assertFalse(overlap, f"{agent} plan includes privileged tools: {overlap}")

    def test_unknown_agent_has_no_plan(self) -> None:
        with self.assertRaises(ToolError):
            plan_for("not-an-agent")
        result = execute_plan("not-an-agent", "x", _ctx(ROOT, Path(tempfile.mkdtemp())), ["health_read"])
        self.assertFalse(result.ok)
        self.assertIn("no local plan", result.detail)

    def test_lab_operations_plan_runs(self) -> None:
        policy = load_policy("lab-operations")
        allowed = constrain_tools(list(policy.allowed_tools), policy)
        result = execute_plan("lab-operations", "health", _ctx(ROOT, Path(tempfile.mkdtemp())), allowed)
        self.assertTrue(result.ok)
        self.assertEqual(result.tools_run, ["health_read", "compose_ps_read"])
        self.assertIn("127.0.0.1:5432", result.detail)

    def test_research_does_not_invent_citations(self) -> None:
        artifacts = Path(tempfile.mkdtemp())
        policy = load_policy("research")
        result = execute_plan(
            "research",
            "summarize X",
            _ctx(ROOT, artifacts),
            list(policy.allowed_tools),
        )
        self.assertTrue(result.ok)
        self.assertTrue(result.artifacts)
        text = Path(result.artifacts[0]).read_text(encoding="utf-8")
        self.assertIn("citations were not invented", text)
        self.assertNotIn("http://", text)

    def test_development_reads_bounded_repo(self) -> None:
        git_root = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init"], cwd=git_root, check=True, capture_output=True)
        (git_root / "README").write_text("x\n", encoding="utf-8")
        policy = load_policy("development")
        result = execute_plan(
            "development",
            "status",
            _ctx(git_root, Path(tempfile.mkdtemp())),
            list(policy.allowed_tools),
        )
        self.assertTrue(result.ok)
        self.assertIn("README", result.detail)

    def test_lab_ops_cannot_run_git_push(self) -> None:
        policy = load_policy("lab-operations")
        allowed = constrain_tools(["git_push", *policy.allowed_tools], policy)
        self.assertNotIn("git_push", allowed)
        result = execute_plan(
            "lab-operations",
            "push please",
            _ctx(ROOT, Path(tempfile.mkdtemp())),
            allowed,
        )
        self.assertTrue(result.ok)
        self.assertNotIn("git_push", result.tools_run)

    def test_privileged_tool_impl_refuses(self) -> None:
        with self.assertRaises(ToolError):
            _execute("git_push", _ctx(ROOT, Path(tempfile.mkdtemp())), "x", [])

    def test_path_escape_fails_the_plan(self) -> None:
        policy = load_policy("development")
        result = execute_plan(
            "development",
            "escape",
            _ctx(Path(tempfile.mkdtemp()), Path(tempfile.mkdtemp()), bounded_scope="../"),
            list(policy.allowed_tools),
        )
        self.assertFalse(result.ok)
        self.assertIn("escapes workspace", result.detail)

    def test_missing_allowlist_blocks_first_tool(self) -> None:
        result = execute_plan("lab-operations", "x", _ctx(ROOT, Path(tempfile.mkdtemp())), [])
        self.assertFalse(result.ok)
        self.assertEqual(result.blocked_tool, "health_read")


if __name__ == "__main__":
    unittest.main()
