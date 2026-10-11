"""Tests for conversational scheduling and durable memory tools (IWO-103)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.agent_definitions import AgentDefinition, AgentDefinitionStore
from ai_lab_platform.memory_vault import MemoryVault
from ai_lab_platform.policy import load_policy
from ai_lab_platform.tool_runtime import ToolContext, execute_allowed_tool


class SchedulingAndVaultToolsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.vault_root = Path(self.tmp_dir.name) / "vault"
        self.workspace_root = Path(self.tmp_dir.name) / "workspace"
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        self.vault_root.mkdir(parents=True, exist_ok=True)
        self.ctx = ToolContext(
            workspace_root=self.workspace_root,
            artifact_root=self.workspace_root / "artifacts",
            vault_root=self.vault_root,
        )
        self.policy = load_policy("personal")

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def test_personal_policy_has_new_tools(self) -> None:
        self.assertIn("schedule_create", self.policy.allowed_tools)
        self.assertIn("schedule_list", self.policy.allowed_tools)
        self.assertIn("schedule_cancel", self.policy.allowed_tools)
        self.assertIn("vault_write", self.policy.allowed_tools)

    def test_schedule_create_validates_and_creates(self) -> None:
        res = execute_allowed_tool(
            "schedule_create",
            {
                "title": "Monday Security Scan",
                "cron": "0 9 * * 1",
                "instructions": "Audit repo for CVEs and outdated dependencies.",
                "agent": "personal",
            },
            allowed_tools=list(self.policy.allowed_tools),
            approved_tools=set(),
            ctx=self.ctx,
        )
        self.assertTrue(res.ok)
        self.assertIn("Scheduled 'Monday Security Scan'", res.observation)
        self.assertIn("cron '0 9 * * 1'", res.observation)

    def test_schedule_create_rejects_invalid_cron(self) -> None:
        res = execute_allowed_tool(
            "schedule_create",
            {
                "title": "Bad Schedule",
                "cron": "every monday",
                "instructions": "Will fail cron parser.",
            },
            allowed_tools=list(self.policy.allowed_tools),
            approved_tools=set(),
            ctx=self.ctx,
        )
        self.assertFalse(res.ok)
        self.assertIn("invalid cron expression", res.observation)

    def test_schedule_list_and_cancel(self) -> None:
        # Create
        execute_allowed_tool(
            "schedule_create",
            {
                "title": "Daily Repo Health Check",
                "cron": "0 8 * * *",
                "instructions": "Inspect git status and docker health.",
            },
            allowed_tools=list(self.policy.allowed_tools),
            approved_tools=set(),
            ctx=self.ctx,
        )
        # List
        res_list = execute_allowed_tool(
            "schedule_list",
            {},
            allowed_tools=list(self.policy.allowed_tools),
            approved_tools=set(),
            ctx=self.ctx,
        )
        self.assertTrue(res_list.ok)
        self.assertIn("Daily Repo Health Check", res_list.observation)
        self.assertIn("cron='0 8 * * *'", res_list.observation)

        # Cancel
        res_cancel = execute_allowed_tool(
            "schedule_cancel",
            {"title": "Daily Repo Health Check"},
            allowed_tools=list(self.policy.allowed_tools),
            approved_tools=set(),
            ctx=self.ctx,
        )
        self.assertTrue(res_cancel.ok)
        self.assertIn("Cancelled schedule for task 'Daily Repo Health Check'", res_cancel.observation)

    def test_vault_write_stores_preference(self) -> None:
        res = execute_allowed_tool(
            "vault_write",
            {
                "category": "preferences",
                "title": "Package Manager Preference",
                "content": "The operator prefers using 'uv' for Python environments over pip/poetry.",
            },
            allowed_tools=list(self.policy.allowed_tools),
            approved_tools=set(),
            ctx=self.ctx,
        )
        self.assertTrue(res.ok)
        self.assertIn("vault_write filed=knowledge/preferences/package-manager-preference.md", res.observation)

        # Verify file exists in vault
        saved = self.vault_root / "knowledge" / "preferences" / "package-manager-preference.md"
        self.assertTrue(saved.is_file())
        text = saved.read_text(encoding="utf-8")
        self.assertIn("The operator prefers using 'uv'", text)
        self.assertIn("type: preferences", text)

    def test_vault_write_stores_decision(self) -> None:
        res = execute_allowed_tool(
            "vault_write",
            {
                "category": "decisions",
                "title": "Use Local Apple Silicon M4",
                "content": "Selected Qwen 3.6 35B running locally via Ollama to avoid cloud API latency and costs.",
            },
            allowed_tools=list(self.policy.allowed_tools),
            approved_tools=set(),
            ctx=self.ctx,
        )
        self.assertTrue(res.ok)
        saved = self.vault_root / "knowledge" / "decisions" / "use-local-apple-silicon-m4.md"
        self.assertTrue(saved.is_file())
        self.assertIn("Selected Qwen 3.6 35B", saved.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
