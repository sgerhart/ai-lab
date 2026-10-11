"""Tests for Presentation Generation, Dynamic Skill Library, and Smart Model Routing (IWO-104)."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.model_catalog import resolve_smart_model
from ai_lab_platform.policy import load_policy
from ai_lab_platform.presentations import PresentationError, PresentationLibrary
from ai_lab_platform.skills_library import SkillError, SkillLibrary
from ai_lab_platform.tool_runtime import ToolContext, execute_allowed_tool


class PresentationsAndSkillsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp_dir.name)
        self.presentations_root = self.root / "presentations"
        self.skills_root = self.root / "skills"
        self.pres_lib = PresentationLibrary(self.presentations_root)
        self.skill_lib = SkillLibrary(self.skills_root)
        self.ctx = ToolContext(
            workspace_root=self.root,
            artifact_root=self.root / "artifacts",
        )
        self.policy = load_policy("personal")

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def test_personal_policy_has_iwo104_tools(self) -> None:
        self.assertIn("presentation_write", self.policy.allowed_tools)
        self.assertIn("presentation_list", self.policy.allowed_tools)
        self.assertIn("skill_create", self.policy.allowed_tools)
        self.assertIn("skill_list", self.policy.allowed_tools)
        self.assertIn("skill_read", self.policy.allowed_tools)

    def test_presentation_write_and_list(self) -> None:
        deck_content = (
            "# Introduction to AI Lab\n\n- Apple Silicon M4 local host\n- Zero cloud billing default\n\n"
            "---\n\n# Security Architecture\n\n- Gated worktree sandboxes\n- Vault confinement\n"
        )
        res = self.pres_lib.write("ai-lab-overview", "AI Lab Executive Overview", deck_content)
        self.assertIn("presentation_write filed=ai-lab-overview.html", res)
        self.assertIn("slides: 2", res)

        # Check html file generated
        html_file = self.presentations_root / "ai-lab-overview.html"
        self.assertTrue(html_file.is_file())
        html_content = html_file.read_text(encoding="utf-8")
        self.assertIn("AI Lab Executive Overview", html_content)
        self.assertIn("slide active", html_content)
        self.assertIn("Apple Silicon M4 local host", html_content)
        self.assertIn("Security Architecture", html_content)

        # Check md file generated
        md_file = self.presentations_root / "ai-lab-overview.md"
        self.assertTrue(md_file.is_file())

        # List
        listed = self.pres_lib.list_presentations()
        self.assertIn("ai-lab-overview.html", listed)

        # Path escape protection
        with self.assertRaises(PresentationError):
            self.pres_lib.write("../../etc/evil", "Bad", "Content")

    def test_presentation_header_split_and_title_sanitization(self) -> None:
        raw_markdown = (
            "# Agent Security 2026\n\n"
            "## Slide 1: The Rise of Autonomous Agents\n\n"
            "- Context: Shift from passive LLMs to agents.\n\n"
            "## Slide 2: Key Risk #1 - Prompt Injection & Jailbreaking\n\n"
            "- Vulnerability: Agents process untrusted inputs.\n\n"
            "## Slide 3: Key Risk #2 - Data Exfiltration\n\n"
            "- Data Flow: Multi-source access.\n"
        )
        res = self.pres_lib.write("agent-sec-test", "Agent Security 2026", raw_markdown)
        self.assertIn("slides: 3", res)

        html_file = self.presentations_root / "agent-sec-test.html"
        self.assertTrue(html_file.is_file())
        html = html_file.read_text(encoding="utf-8")

        # Titles should be cleanly sanitized
        self.assertIn("The Rise of Autonomous Agents", html)
        self.assertIn("Key Risk #1 - Prompt Injection", html)
        self.assertNotIn("Slide 1:", html)
        self.assertNotIn("Slide 2:", html)
        self.assertNotIn("Slide 3:", html)
        # Badges should have Slide 01 of 03
        self.assertIn("Slide 01 of 03", html)
        self.assertIn("Slide 02 of 03", html)
        self.assertIn("Slide 03 of 03", html)

    def test_skill_create_and_read(self) -> None:
        steps = (
            "1. Inspect CVE identifiers using NVD.\n"
            "2. Cross reference with OSV database.\n"
            "3. Report risk tier to operator.\n"
        )
        res = self.skill_lib.create("CVE Triage", "Analyze security vulnerability severity", steps)
        self.assertIn("skill_create success", res)
        self.assertIn("skills/cve-triage/SKILL.md", res)

        skill_file = self.skills_root / "cve-triage" / "SKILL.md"
        self.assertTrue(skill_file.is_file())
        content = skill_file.read_text(encoding="utf-8")
        self.assertIn("name: CVE Triage", content)
        self.assertIn("Procedural Execution Steps", content)
        self.assertIn("Cross reference with OSV database", content)

        # List
        listed = self.skill_lib.list_skills()
        self.assertIn("cve-triage", listed)

        # Read
        read_back = self.skill_lib.read("cve-triage")
        self.assertIn("Analyze security vulnerability severity", read_back)

        # Escape protection
        with self.assertRaises(SkillError):
            self.skill_lib.create("../../bad", "Bad", "steps")

    def test_smart_model_auto_routing(self) -> None:
        installed = ["qwen3.6:35b-a3b", "qwen3-coder:30b", "llama3.2:3b", "qwen3.8:27b"]

        # Coding queries route to qwen3-coder:30b
        model, backend = resolve_smart_model("Can you write a python unittest for this class?", "auto", installed)
        self.assertEqual(model, "qwen3-coder:30b")
        self.assertEqual(backend, "ollama")

        model, backend = resolve_smart_model("Review git diff and check for bug in function", "auto", installed)
        self.assertEqual(model, "qwen3-coder:30b")

        # Fast lightweight queries route to llama3.2:3b
        model, backend = resolve_smart_model("ping", "auto", installed)
        self.assertEqual(model, "llama3.2:3b")

        model, backend = resolve_smart_model("hello", "auto", installed)
        self.assertEqual(model, "llama3.2:3b")

        # Deep reasoning / planning queries route to qwen3.6:35b-a3b
        model, backend = resolve_smart_model("Synthesize our memory vault into a 6-month product roadmap and strategic plan.", "auto", installed)
        self.assertEqual(model, "qwen3.6:35b-a3b")

        # Explicit model overrides are respected
        model, backend = resolve_smart_model("write python code", "qwen3.8:27b", installed)
        self.assertEqual(model, "qwen3.8:27b")

    def test_tool_runtime_executes_new_tools(self) -> None:
        # presentation_write via tool_runtime
        res_pres = execute_allowed_tool(
            "presentation_write",
            {
                "title": "Roadmap Q4",
                "content": "# Q4 Goals\n- Finish local LLM agent\n---\n# Deliverables\n- Full deployment",
            },
            allowed_tools=list(self.policy.allowed_tools),
            approved_tools=set(),
            ctx=self.ctx,
        )
        self.assertTrue(res_pres.ok)
        self.assertIn("presentation_write filed=roadmap-q4.html", res_pres.observation)

        # skill_create via tool_runtime
        res_skill = execute_allowed_tool(
            "skill_create",
            {
                "name": "Audit Dependencies",
                "description": "Check requirements.txt for outdated pins",
                "steps": "1. Run pip list --outdated.\n2. Cross reference release notes.",
            },
            allowed_tools=list(self.policy.allowed_tools),
            approved_tools=set(),
            ctx=self.ctx,
        )
        self.assertTrue(res_skill.ok)
        self.assertIn("skill_create success", res_skill.observation)

    def test_artifacts_api_endpoints(self) -> None:
        try:
            from fastapi.testclient import TestClient
            from langgraph.checkpoint.memory import MemorySaver
            from ai_lab_platform.control_app import create_control_app
            from ai_lab_platform.store import SqliteStore
        except ImportError:
            return

        lib = PresentationLibrary(root=self.root / "presentations")
        lib.write("demo-deck", "Demo Deck", "# Slide 1\nHello\n---\n# Slide 2\nWorld")

        app = create_control_app(
            store=SqliteStore(self.root / "wo.sqlite"),
            checkpointer=MemorySaver(),
            token="test-token",
        )
        client = TestClient(app)

        os.environ["AI_LAB_PRESENTATIONS_ROOT"] = str(self.root / "presentations")
        try:
            resp = client.get("/v1/artifacts", headers={"Authorization": "Bearer test-token"})
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertIn("artifacts", data)
            items = data["artifacts"]
            self.assertTrue(any(i["name"] == "demo-deck.html" for i in items))

            pres_resp = client.get(
                "/v1/artifacts/presentations/demo-deck.html",
                headers={"Authorization": "Bearer test-token"},
            )
            self.assertEqual(pres_resp.status_code, 200)
            self.assertIn("<!DOCTYPE html>", pres_resp.text)
            self.assertIn("Demo Deck", pres_resp.text)
        finally:
            os.environ.pop("AI_LAB_PRESENTATIONS_ROOT", None)


if __name__ == "__main__":
    unittest.main()
