"""FEAT-002 / IWO-031 — background agent-run worker."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.agent_loop import run_until_idle
from ai_lab_platform.agent_worker import drain_queued_runs, list_queued_runs
from ai_lab_platform.conversation import AgentRun, AgentRunStatus, BillingClass, Conversation, RunBudget
from ai_lab_platform.model_router import ModelRouter
from ai_lab_platform.settings import Settings
from ai_lab_platform.store import SqliteStore

from tests.test_agent_loop import ScriptedToolBackend


class WorkerDrainTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.store = SqliteStore(Path(self.tmp.name) / "wo.sqlite")
        scripted = ScriptedToolBackend(
            [
                {"type": "tool", "name": "health_read", "args": {}},
                {"type": "final", "text": "ok"},
            ]
        )
        self.router = ModelRouter(backends={"scripted": scripted, "fake": scripted})

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_drain_queued(self) -> None:
        conv = Conversation.new(agent="lab-operations", title="w")
        self.store.put_conversation(conv)
        run = AgentRun.new(
            agent="lab-operations",
            objective="health",
            conversation_id=conv.id,
            model="scripted",
            billing_class=BillingClass.LOCAL,
            backend="scripted",
            budget=RunBudget(max_steps=6),
        )
        run.status = AgentRunStatus.QUEUED
        self.store.put_agent_run(run)
        self.assertEqual(len(list_queued_runs(self.store)), 1)
        out = drain_queued_runs(self.store, self.router, limit=1)
        self.assertEqual(len(out["processed"]), 1)
        self.assertEqual(out["queued_remaining"], 0)
        done = self.store.get_agent_run(run.id)
        assert done is not None
        self.assertEqual(done.status, AgentRunStatus.COMPLETED)

    def test_settings_worker_default(self) -> None:
        with unittest.mock.patch.dict("os.environ", {"DATABASE_URL": "", "AI_LAB_AGENT_WORKER": ""}, clear=False):
            # Clear DATABASE_URL for this call
            import os

            env = {k: v for k, v in os.environ.items() if k not in {"DATABASE_URL", "AI_LAB_AGENT_WORKER"}}
            with unittest.mock.patch.dict("os.environ", env, clear=True):
                s = Settings.from_env()
                self.assertFalse(s.agent_worker)


# avoid importing mock at top if unused — use unittest.mock
import unittest.mock  # noqa: E402


try:
    from fastapi.testclient import TestClient
    from langgraph.checkpoint.memory import MemorySaver

    from ai_lab_platform.control_app import create_control_app

    _HAS = True
except ImportError:  # pragma: no cover
    _HAS = False


@unittest.skipUnless(_HAS, "fastapi not installed")
class WorkerApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        scripted = ScriptedToolBackend(
            [
                {"type": "tool", "name": "health_read", "args": {}},
                {"type": "final", "text": "ok"},
            ]
        )
        self.app = create_control_app(
            store=SqliteStore(Path(self.tmp.name) / "wo.sqlite"),
            checkpointer=MemorySaver(),
            token="t",
            dispatch=lambda _p: {"ok": True, "detail": "x"},
            model_router=ModelRouter(backends={"scripted": scripted, "fake": scripted}),
            settings=Settings(api_token="t", agent_worker=False),
        )
        self.client = TestClient(self.app)
        self.h = {"Authorization": "Bearer t"}

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_execute_queues_then_worker_tick(self) -> None:
        conv = self.client.post(
            "/v1/conversations", headers=self.h, json={"agent": "lab-operations"}
        ).json()
        run = self.client.post(
            f"/v1/conversations/{conv['id']}/runs",
            headers=self.h,
            json={
                "objective": "health",
                "backend": "scripted",
                "billing_class": "local",
                "execute": True,
                "max_steps": 6,
            },
        ).json()
        self.assertEqual(run["status"], "queued")
        tick = self.client.post("/v1/agent-runs/worker/tick", headers=self.h)
        self.assertEqual(tick.status_code, 200)
        self.assertEqual(len(tick.json()["processed"]), 1)
        final = self.client.get(f"/v1/agent-runs/{run['id']}", headers=self.h).json()
        self.assertEqual(final["status"], "completed")


if __name__ == "__main__":
    unittest.main()
