"""The agent builder asks about the job and chooses the model itself."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.agent_builder import choose_model, interview, interviewer_model  # noqa: E402


INSTALLED = ["qwen3.6:35b-a3b", "qwen3-coder:30b", "llama3.2:3b"]


class AgentBuilderTests(unittest.TestCase):
    def test_opening_asks_what_it_should_do(self) -> None:
        out = interview([], installed=INSTALLED)
        self.assertFalse(out["ready"])
        self.assertIn("do", out["question"].lower())

    def test_coding_task_gets_the_coding_model_without_asking(self) -> None:
        out = interview(
            [
                {"role": "assistant", "content": "What do you want this agent to do?"},
                {"role": "user", "content": "Implement a patch in the repo and wait for approval."},
                {"role": "assistant", "content": "What should it hand you when it is finished?"},
                {"role": "user", "content": "A diff I can review."},
                {"role": "user", "content": "build it"},
            ],
            installed=INSTALLED,
            roles={"coding-local": "qwen3-coder:30b", "general-local": "qwen3.6:35b-a3b"},
        )
        self.assertTrue(out["ready"])
        draft = out["draft"]
        self.assertEqual(draft["purpose"], "build")
        self.assertEqual(draft["kind"], "agent")
        self.assertEqual(draft["model"], "qwen3-coder:30b")
        self.assertEqual(draft["backend"], "ollama")
        self.assertNotIn("temperature", draft)

    def test_teaching_task_gets_the_general_model(self) -> None:
        backend, model, note = choose_model(
            "learn",
            "Teach me how attention works.",
            INSTALLED,
            {"general-local": "qwen3.6:35b-a3b", "coding-local": "qwen3-coder:30b"},
        )
        self.assertEqual(backend, "ollama")
        self.assertEqual(model, "qwen3.6:35b-a3b")
        self.assertIn("general", note)

    def test_model_cannot_force_a_followup_about_temperature(self) -> None:
        def complete(_prompt: str) -> str:
            return '{"ready": false, "question": "What temperature and quant should I use?"}'

        out = interview(
            [{"role": "user", "content": "Summarize my weekly notes."}],
            installed=INSTALLED,
            complete=complete,
        )
        self.assertFalse(out["ready"])
        self.assertNotIn("temperature", out["question"].lower())
        self.assertNotIn("quant", out["question"].lower())
        self.assertIn("often", interview(
            [
                {"role": "user", "content": "Summarize my weekly notes."},
                {"role": "assistant", "content": "What should it hand you when it is finished?"},
                {"role": "user", "content": "A short note."},
            ],
            installed=INSTALLED,
        )["question"].lower())

    def test_known_steps_become_a_workflow(self) -> None:
        first = interview(
            [{"role": "user", "content": "Every morning, check the disk, then write a one-line note."}],
            installed=INSTALLED,
        )
        self.assertFalse(first["ready"])
        self.assertIn("order", first["question"].lower())
        done = interview(
            [
                {"role": "user", "content": "Every morning, check the disk, then write a one-line note."},
                {"role": "user", "content": "The note."},
            ],
            installed=INSTALLED,
        )
        self.assertFalse(done["ready"])
        built = interview(
            [
                {"role": "user", "content": "Every morning, check the disk, then write a one-line note."},
                {"role": "user", "content": "The note."},
                {"role": "user", "content": "build it"},
            ],
            installed=INSTALLED,
        )
        self.assertTrue(built["ready"])
        draft = built["draft"]
        self.assertEqual(draft["kind"], "workflow")
        self.assertGreaterEqual(len(draft["steps"]), 2)
        self.assertEqual(draft["model"], "")
        self.assertEqual(draft["tools"], [])

    def test_mail_asks_how_to_reach_the_account_before_a_draft(self) -> None:
        first = interview(
            [{"role": "user", "content": "Read my Gmail and draft a reply."}],
            installed=INSTALLED,
        )
        self.assertFalse(first["ready"])
        self.assertIn("gmail", first["question"].lower())
        second = interview(
            [
                {"role": "user", "content": "Read my Gmail and draft a reply."},
                {"role": "user", "content": "Yes, add it."},
            ],
            installed=INSTALLED,
        )
        self.assertFalse(second["ready"])
        done = interview(
            [
                {"role": "user", "content": "Read my Gmail and draft a reply."},
                {"role": "user", "content": "Yes, add it."},
                {"role": "user", "content": "A draft I can send myself."},
            ],
            installed=INSTALLED,
        )
        self.assertFalse(done["ready"])
        built = interview(
            [
                {"role": "user", "content": "Read my Gmail and draft a reply."},
                {"role": "user", "content": "Yes, add it."},
                {"role": "user", "content": "A draft I can send myself."},
                {"role": "user", "content": "everything is good, build it"},
            ],
            installed=INSTALLED,
        )
        self.assertTrue(built["ready"])
        draft = built["draft"]
        self.assertEqual(draft["tools"], ["search_threads", "get_thread", "list_labels", "list_drafts"])
        self.assertEqual(draft["skills"], ["Draft a reply"])
        self.assertEqual(draft["model"], "qwen3.6:35b-a3b")
        self.assertIn("registered", draft["model_note"].lower())
        self.assertEqual(draft["mcp_offer"], "gmail")
        self.assertIn("repository", draft["instructions"].lower())

    def test_a_cve_job_records_the_lookup_server(self) -> None:
        built = interview(
            [
                {"role": "user", "content": "Look up CVE-2024-1234 and tell me if KEV lists it."},
                {"role": "user", "content": "build it"},
            ],
            installed=INSTALLED,
        )
        self.assertTrue(built["ready"])
        draft = built["draft"]
        self.assertEqual(draft["mcp_offers"], ["cve-lookup"])
        self.assertIn("nvd_get", draft["mcp_tools"])
        self.assertNotIn("exploit_search", draft["mcp_tools"])
        self.assertNotIn("nuclei_check", draft["mcp_tools"])
        self.assertEqual(draft["skills"], ["Look up a CVE"])
        self.assertNotIn("apply_patch", draft["tools"])

    def test_a_decision_stays_an_agent(self) -> None:
        first = interview(
            [{"role": "user", "content": "Figure out which note I should study."}],
            installed=INSTALLED,
        )
        self.assertIn("hand you", first["question"].lower())

    def test_draft_conversation_uses_the_general_model(self) -> None:
        self.assertEqual(interviewer_model(INSTALLED), "qwen3.6:35b-a3b")
        self.assertEqual(interviewer_model(["llama3.2:3b"]), "llama3.2:3b")
