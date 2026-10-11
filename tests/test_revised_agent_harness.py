"""Tests for the revised Agent Harness and Second Brain loop (IWO-102)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.agent_loop import (  # noqa: E402
    extract_thought_and_content,
    loop_system_prompt,
    parse_model_turn,
    run_until_idle,
)
from ai_lab_platform.conversation import AgentRun, AgentRunStatus, BillingClass  # noqa: E402
from ai_lab_platform.model_router import ModelRouter, ScriptedToolBackend  # noqa: E402
from ai_lab_platform.policy import load_policy  # noqa: E402
from ai_lab_platform.store import SqliteStore  # noqa: E402
from ai_lab_platform.tool_runtime import ToolContext  # noqa: E402


def _temp_store() -> SqliteStore:
    tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
    tmp.close()
    return SqliteStore(tmp.name)


class RevisedAgentHarnessTests(unittest.TestCase):
    def test_think_tag_extraction(self) -> None:
        raw = "<think>Analyzing user query. Need to check vault notes.</think>\nTOOL vault_read {\"file\": \"notes.md\"}"
        thought, cleaned = extract_thought_and_content(raw)
        self.assertIn("Analyzing user query", thought)
        self.assertEqual(cleaned, 'TOOL vault_read {"file": "notes.md"}')

        turn = parse_model_turn(raw)
        self.assertEqual(turn["type"], "tool")
        self.assertEqual(turn["name"], "vault_read")
        self.assertEqual(turn["args"], {"file": "notes.md"})

    def test_think_tag_with_final_synthesis(self) -> None:
        raw = "<think>I have reviewed the entire dossier.</think>\nFINAL The research indicates a 25% performance improvement."
        thought, cleaned = extract_thought_and_content(raw)
        self.assertEqual(thought, "I have reviewed the entire dossier.")
        turn = parse_model_turn(raw)
        self.assertEqual(turn["type"], "final")
        self.assertEqual(turn["text"], "The research indicates a 25% performance improvement.")

    def test_markdown_json_tool_block(self) -> None:
        raw = """Here is the tool I want to call:
```json
{
  "name": "web_search",
  "args": {"query": "AI agent architectures"}
}
```
"""
        turn = parse_model_turn(raw)
        self.assertEqual(turn["type"], "tool")
        self.assertEqual(turn["name"], "web_search")
        self.assertEqual(turn["args"], {"query": "AI agent architectures"})

    def test_function_call_format_parsing(self) -> None:
        raw = """```json
{
  "function": {
    "name": "research",
    "arguments": {"query": "autonomous agents", "name": "agents-dossier"}
  }
}
```"""
        turn = parse_model_turn(raw)
        self.assertEqual(turn["type"], "tool")
        self.assertEqual(turn["name"], "research")
        self.assertEqual(turn["args"]["query"], "autonomous agents")
        self.assertEqual(turn["args"]["name"], "agents-dossier")

    def test_system_prompt_includes_second_brain_guidance(self) -> None:
        policy = load_policy("personal")
        prompt = loop_system_prompt(policy, brief="User preference: concise reports")
        self.assertIn("second brain", prompt.lower())
        self.assertIn("vault", prompt.lower())
        self.assertIn("research", prompt.lower())
        self.assertIn("User preference: concise reports", prompt)

    def test_multi_turn_research_and_report_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = _temp_store()
            ctx = ToolContext(
                workspace_root=Path(tmpdir),
                artifact_root=Path(tmpdir) / "artifacts",
                vault_root=Path(tmpdir) / "vault",
                files_root=Path(tmpdir) / "files",
            )
            ctx.vault_root.mkdir(parents=True, exist_ok=True)
            (ctx.vault_root / "context.md").write_text("# Project Strategy\nBuild scalable agent systems.\n", encoding="utf-8")

            # Model executes vault_read then generates final report
            scripted = ScriptedToolBackend(
                [
                    {"type": "tool", "name": "vault_read", "args": {"file": "context.md"}},
                    {"type": "final", "text": "Strategy confirmed: build scalable agent systems."},
                ]
            )
            router = ModelRouter(backends={"scripted": scripted}, default_backend="scripted")
            run = AgentRun.new(
                agent="personal",
                objective="What is our project strategy?",
                backend="scripted",
                billing_class=BillingClass.LOCAL,
            )
            store.put_agent_run(run)
            done = run_until_idle(run, router=router, store_put=store.put_agent_run, ctx=ctx)
            self.assertEqual(done.status, AgentRunStatus.COMPLETED)
            self.assertIn("Strategy confirmed", done.final_result or "")
            self.assertTrue(any(t.get("kind") == "tool_result" and "Project Strategy" in t.get("observation", "") for t in done.traces))


if __name__ == "__main__":
    unittest.main()
