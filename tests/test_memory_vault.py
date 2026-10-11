"""Personal memory vault: grep by alias, confine paths, file a day without edits."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.agent_loop import loop_system_prompt, run_until_idle  # noqa: E402
from ai_lab_platform.conversation import AgentRun, AgentRunStatus, BillingClass  # noqa: E402
from ai_lab_platform.memory_vault import MemoryVault, VaultError  # noqa: E402
from ai_lab_platform.model_router import ModelRouter, ScriptedToolBackend  # noqa: E402
from ai_lab_platform.policy import load_policy  # noqa: E402
from ai_lab_platform.store import SqliteStore  # noqa: E402
from ai_lab_platform.tool_runtime import build_tool_context, execute_allowed_tool  # noqa: E402
from ai_lab_platform.tools import ToolContext  # noqa: E402


_DINING = """---
id: dining
type: preference
aliases: [food, lunch, restaurants, takeout, delivery, dining]
---

- **Pasta:** Loves pasta; stated on 2026-09-15.
"""


def _vault() -> MemoryVault:
    return MemoryVault(Path(tempfile.mkdtemp()))


class MemoryVaultTests(unittest.TestCase):
    def test_alias_hits_and_a_paraphrase_does_not(self) -> None:
        vault = _vault()
        vault.ensure_layout()
        pref = vault.root / "knowledge" / "preferences" / "dining.md"
        pref.write_text(_DINING, encoding="utf-8")
        takeout = vault.grep("takeout")
        self.assertIn("knowledge/preferences/dining.md", takeout)
        self.assertIn("hits=1", takeout)
        pasta = vault.grep("pasta")
        self.assertIn("dining.md", pasta)
        missed = vault.grep("Italian noodles I enjoy")
        self.assertIn("hits=0", missed)

    def test_read_rejects_parent_segments(self) -> None:
        vault = _vault()
        vault.ensure_layout()
        with self.assertRaises(VaultError):
            vault.read("../../etc/passwd")
        with self.assertRaises(VaultError):
            vault.read("/etc/passwd")

    def test_symlink_outside_the_vault_is_skipped(self) -> None:
        vault = _vault()
        vault.ensure_layout()
        outside = Path(tempfile.mkdtemp()) / "secret.md"
        outside.write_text("token material stays outside", encoding="utf-8")
        link = vault.root / "knowledge" / "facts" / "leak.md"
        link.symlink_to(outside)
        listed = vault.list_files("knowledge/facts")
        self.assertNotIn("leak.md", listed)
        with self.assertRaises(VaultError):
            vault.read("knowledge/facts/leak.md")

    def test_record_day_appends_timeline_and_leaves_preferences(self) -> None:
        vault = _vault()
        vault.ensure_layout()
        pref = vault.root / "knowledge" / "preferences" / "dining.md"
        pref.write_text(_DINING, encoding="utf-8")
        before = pref.read_text(encoding="utf-8")
        rel = vault.record_day("2026-10-05", ["Asked about dinner.", "Left the preference file alone."])
        self.assertEqual(rel, "timeline/daily/2026-10-05.md")
        filed = (vault.root / rel).read_text(encoding="utf-8")
        self.assertIn("Asked about dinner.", filed)
        self.assertEqual(pref.read_text(encoding="utf-8"), before)
        vault.record_day("2026-10-05", ["Second note."])
        again = (vault.root / rel).read_text(encoding="utf-8")
        self.assertEqual(again.count("id: 2026-10-05"), 1)
        self.assertIn("Second note.", again)

    def test_brief_names_open_work_and_the_day(self) -> None:
        vault = _vault()
        vault.ensure_layout()
        (vault.root / "identity.md").write_text(
            "---\nid: operator\ntype: identity\naliases: [me]\n---\n\nTimezone is unset.\n",
            encoding="utf-8",
        )
        (vault.root / "workstreams" / "active" / "move.md").write_text(
            "---\nid: move\ntype: workstream\naliases: [apartment]\n---\n\n# Pack the apartment\n",
            encoding="utf-8",
        )
        brief = vault.render_brief(day="2026-10-05")
        self.assertIn("as of 2026-10-05 UTC", brief)
        self.assertIn("Timezone is unset.", brief)
        self.assertIn("Pack the apartment", brief)
        self.assertIn("No timeline note for 2026-10-05", brief)


class PersonalAgentLoopTests(unittest.TestCase):
    def test_lab_prompt_has_no_personal_brief(self) -> None:
        prompt = loop_system_prompt(load_policy("lab-operations"))
        self.assertNotIn("Personal memory brief", prompt)

    def test_personal_run_greps_then_reads_then_greps_again(self) -> None:
        vault = _vault()
        vault.ensure_layout()
        (vault.root / "knowledge" / "preferences" / "dining.md").write_text(_DINING, encoding="utf-8")
        store_path = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
        store_path.close()
        store = SqliteStore(store_path.name)
        scripted = ScriptedToolBackend(
            [
                {"type": "tool", "name": "vault_grep", "args": {"query": "takeout"}},
                {"type": "tool", "name": "vault_read", "args": {"path": "knowledge/preferences/dining.md"}},
                {"type": "tool", "name": "vault_grep", "args": {"query": "pasta"}},
                {"type": "final", "text": "Pasta, from the dining note."},
            ]
        )
        router = ModelRouter(backends={"scripted": scripted}, default_backend="scripted")
        run = AgentRun.new(
            agent="personal",
            objective="What do I like to eat?",
            backend="scripted",
            billing_class=BillingClass.LOCAL,
        )
        run.budget.max_steps = 12
        store.put_agent_run(run)
        ctx = build_tool_context()
        ctx.vault_root = vault.root
        done = run_until_idle(run, router=router, store_put=store.put_agent_run, ctx=ctx)
        self.assertEqual(done.status, AgentRunStatus.COMPLETED, done.final_result)
        self.assertIn("Pasta", done.final_result or "")
        tools = [trace.get("tool") for trace in done.traces if trace.get("kind") == "tool_result"]
        self.assertEqual(tools, ["vault_grep", "vault_read", "vault_grep"])
        brief = vault.render_brief(day="2026-10-05")
        prompt = loop_system_prompt(load_policy("personal"), brief=brief)
        self.assertIn("Personal memory brief", prompt)
        self.assertIn("as of 2026-10-05 UTC", prompt)

    def test_repeating_health_read_still_stops(self) -> None:
        store_path = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
        store_path.close()
        store = SqliteStore(store_path.name)
        scripted = ScriptedToolBackend(
            [
                {"type": "tool", "name": "health_read", "args": {}},
                {"type": "tool", "name": "health_read", "args": {"ports": [8088]}},
            ]
        )
        router = ModelRouter(backends={"scripted": scripted}, default_backend="scripted")
        run = AgentRun.new(agent="lab-operations", objective="check", backend="scripted")
        store.put_agent_run(run)
        done = run_until_idle(run, router=router, store_put=store.put_agent_run)
        self.assertEqual(done.status, AgentRunStatus.COMPLETED)
        self.assertIn("stopped repeating health_read", done.final_result or "")

    def test_tool_path_escape_is_denied_as_an_observation(self) -> None:
        vault = _vault()
        vault.ensure_layout()
        ctx = ToolContext(
            workspace_root=ROOT,
            artifact_root=ROOT / "artifacts",
            vault_root=vault.root,
        )
        result = execute_allowed_tool(
            "vault_read",
            {"path": "../../etc/passwd"},
            allowed_tools=["vault_read"],
            approved_tools=set(),
            ctx=ctx,
        )
        self.assertFalse(result.ok)
        self.assertIn("escapes", result.observation)


if __name__ == "__main__":
    unittest.main()
