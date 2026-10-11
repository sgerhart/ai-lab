"""Ollama keeps one resident model. A different request waits."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.agent_loop import run_until_idle
from ai_lab_platform.conversation import AgentRun, AgentRunStatus, BillingClass, RunBudget
from ai_lab_platform.model_router import CompletionRequest, ModelRouter
from ai_lab_platform.agent_loop import _account_tool_block
from ai_lab_platform.model_slot import ModelSlotBusy, ensure_slot, slot_note


class SlotDecisionTests(unittest.TestCase):
    def test_idle_or_matching_model_can_run(self) -> None:
        self.assertIsNone(slot_note("qwen3.6:35b-a3b", []))
        self.assertIsNone(slot_note("qwen3.6:35b-a3b", ["qwen3.6:35b-a3b"]))

    def test_another_loaded_model_waits(self) -> None:
        note = slot_note("qwen3.6:35b-a3b", ["qwen3-coder:30b"])
        self.assertIsNotNone(note)
        assert note is not None
        self.assertIn("qwen3-coder:30b", note)
        self.assertIn("qwen3.6:35b-a3b", note)
        self.assertIn("waits", note)

    def test_reader_blocks_before_a_generate(self) -> None:
        with self.assertRaises(ModelSlotBusy):
            ensure_slot("http://mac-studio:11434", "qwen3.6:35b-a3b", reader=lambda: ["qwen3-coder:30b"])
        ensure_slot("http://mac-studio:11434", "qwen3.6:35b-a3b", reader=lambda: [])


class _BusyBackend:
    def complete(self, _request: CompletionRequest) -> None:
        raise ModelSlotBusy(
            "qwen3-coder:30b is loaded. This waits until Ollama is free, then uses qwen3.6:35b-a3b."
        )


class WaitingRunTests(unittest.TestCase):
    def test_run_stays_queued_while_another_model_is_loaded(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        run = AgentRun.new(
            agent="lab-operations",
            objective="Summarize the notes.",
            model="qwen3.6:35b-a3b",
            billing_class=BillingClass.LOCAL,
            backend="ollama",
            budget=RunBudget(max_steps=4),
        )
        run.status = AgentRunStatus.QUEUED
        saved: list[AgentRun] = []
        router = ModelRouter(backends={"ollama": _BusyBackend()})
        done = run_until_idle(run, router=router, store_put=saved.append)
        self.assertEqual(done.status, AgentRunStatus.QUEUED)
        self.assertIsNone(done.error)
        self.assertEqual(done.usage["model_slot"]["state"], "waiting")
        self.assertEqual(done.traces[-1]["kind"], "model_wait")
        self.assertEqual(saved[-1].status, AgentRunStatus.QUEUED)


class AccountBoundaryTests(unittest.TestCase):
    def test_mail_does_not_search_the_repository(self) -> None:
        note = _account_tool_block("Personal Email Agent", "memory_search")
        self.assertIsNotNone(note)
        assert note is not None
        self.assertIn("repository", note)
        self.assertIsNone(_account_tool_block("Check lab health", "memory_search"))
