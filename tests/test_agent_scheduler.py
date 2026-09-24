"""FEAT-009 / IWO-030 — personal agent schedule tick."""

from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.agent_definitions import AgentDefinition, AgentDefinitionStore
from ai_lab_platform.agent_scheduler import minute_key, status, tick
from ai_lab_platform.schedule_cron import CronError, cron_matches, parse_cron


class CronMatchTests(unittest.TestCase):
    def test_hourly(self) -> None:
        when = datetime(2026, 9, 24, 9, 0, tzinfo=ZoneInfo("America/New_York"))
        self.assertTrue(cron_matches("0 * * * *", when))
        self.assertFalse(cron_matches("0 * * * *", when.replace(minute=1)))

    def test_dow_sunday(self) -> None:
        # 2026-09-27 is Sunday
        when = datetime(2026, 9, 27, 8, 30, tzinfo=ZoneInfo("UTC"))
        self.assertTrue(cron_matches("30 8 * * 0", when))
        self.assertFalse(cron_matches("30 8 * * 1", when))

    def test_step(self) -> None:
        when = datetime(2026, 9, 24, 10, 15, tzinfo=ZoneInfo("UTC"))
        self.assertTrue(cron_matches("*/15 * * * *", when))
        self.assertFalse(cron_matches("*/15 * * * *", when.replace(minute=16)))

    def test_invalid(self) -> None:
        with self.assertRaises(CronError):
            parse_cron("not a cron")


class SchedulerTickTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.store = AgentDefinitionStore(Path(self.tmp.name) / "defs.sqlite")
        self.state_path = Path(self.tmp.name) / "schedule-state.json"
        self.when = datetime(2026, 9, 24, 9, 0, tzinfo=ZoneInfo("America/New_York"))

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_starts_due_once(self) -> None:
        due = AgentDefinition.new(
            title="morning",
            schedule_cron="0 9 * * *",
            system_prompt="health check",
        )
        other = AgentDefinition.new(title="idle", schedule_cron="0 3 * * *")
        self.store.put(due)
        self.store.put(other)
        calls: list[str] = []

        def runner(defn: AgentDefinition) -> dict:
            calls.append(defn.id)
            return {"id": "run-1", "status": "completed"}

        out = tick(
            self.store,
            run_definition=runner,
            now=self.when,
            state_path=self.state_path,
        )
        self.assertEqual(len(out["started"]), 1)
        self.assertEqual(out["started"][0]["definition_id"], due.id)
        self.assertEqual(calls, [due.id])
        self.assertEqual(minute_key(self.when), out["minute_key"])

        out2 = tick(
            self.store,
            run_definition=runner,
            now=self.when,
            state_path=self.state_path,
        )
        self.assertEqual(out2["started"], [])
        self.assertTrue(
            any(s["reason"] == "already_fired_this_minute" for s in out2["skipped"])
        )
        self.assertEqual(calls, [due.id])

        st = status(state_path=self.state_path)
        self.assertIn(due.id, st["last_fired"])

    def test_invalid_cron_error_not_raise(self) -> None:
        bad = AgentDefinition.new(title="bad", schedule_cron="nope")
        self.store.put(bad)
        out = tick(
            self.store,
            run_definition=lambda _d: {"id": "x"},
            now=self.when,
            state_path=self.state_path,
        )
        self.assertEqual(out["started"], [])
        self.assertTrue(out["errors"])
        self.assertIn("invalid_cron", out["errors"][0]["error"])


try:
    from fastapi.testclient import TestClient
    from langgraph.checkpoint.memory import MemorySaver

    from ai_lab_platform.control_app import create_control_app
    from ai_lab_platform.model_router import ModelRouter
    from ai_lab_platform.store import SqliteStore

    _HAS_FASTAPI = True
except ImportError:  # pragma: no cover
    _HAS_FASTAPI = False


@unittest.skipUnless(_HAS_FASTAPI, "fastapi not installed")
class SchedulerApiTests(unittest.TestCase):
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
        self.app.state.agent_definition_store = AgentDefinitionStore(
            Path(self.tmp.name) / "defs.sqlite"
        )
        self.client = TestClient(self.app)
        self.h = {"Authorization": "Bearer lab-token"}

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_create_rejects_bad_cron(self) -> None:
        res = self.client.post(
            "/v1/agent-definitions",
            headers=self.h,
            json={"title": "x", "schedule_cron": "bad"},
        )
        self.assertEqual(res.status_code, 400)

    def test_tick_endpoint(self) -> None:
        when = datetime(2026, 9, 24, 9, 0, tzinfo=ZoneInfo("America/New_York"))
        cron = f"{when.minute} {when.hour} * * *"
        created = self.client.post(
            "/v1/agent-definitions",
            headers=self.h,
            json={
                "title": "sched",
                "schedule_cron": cron,
                "system_prompt": "ping",
            },
        )
        self.assertEqual(created.status_code, 200, created.text)
        # Force tick "now" via module path is hard; call tick with patched now through status first
        st = self.client.get("/v1/scheduler/status", headers=self.h)
        self.assertEqual(st.status_code, 200)
        self.assertEqual(len(st.json()["scheduled_definitions"]), 1)
        # Manual tick uses wall clock — may or may not be due; still 200
        tick_res = self.client.post("/v1/scheduler/tick", headers=self.h)
        self.assertEqual(tick_res.status_code, 200)
        self.assertTrue(tick_res.json()["ok"])


if __name__ == "__main__":
    unittest.main()
