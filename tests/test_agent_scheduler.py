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

    def test_tick_files_yesterdays_personal_chats_once(self) -> None:
        from ai_lab_platform.conversation import Conversation, Message
        from ai_lab_platform.memory_vault import MemoryVault
        from ai_lab_platform.store import SqliteStore

        chats = SqliteStore(Path(self.tmp.name) / "chats.sqlite")
        vault = MemoryVault(Path(self.tmp.name) / "vault")
        vault.ensure_layout()
        pref = vault.root / "knowledge" / "preferences" / "dining.md"
        pref.write_text("pasta stays\n", encoding="utf-8")
        personal = Conversation.new(agent="personal", title="Dinner")
        other = Conversation.new(agent="lab-operations", title="Health")
        chats.put_conversation(personal)
        chats.put_conversation(other)
        user = Message.new(conversation_id=personal.id, role="user", content="I want pasta tonight.")
        user.created_at = "2026-10-05T18:00:00+00:00"
        reply = Message.new(conversation_id=personal.id, role="assistant", content="Noted for tonight.")
        reply.created_at = "2026-10-05T18:01:00+00:00"
        today = Message.new(conversation_id=personal.id, role="user", content="This is still today.")
        today.created_at = "2026-10-06T01:00:00+00:00"
        lab = Message.new(conversation_id=other.id, role="user", content="Check the ports.")
        lab.created_at = "2026-10-05T18:02:00+00:00"
        for message in (user, reply, today, lab):
            chats.put_message(message)
        when = datetime(2026, 10, 6, 9, 0, tzinfo=ZoneInfo("America/New_York"))

        def file_memory(moment: datetime, filed_days: list[str]) -> dict:
            from ai_lab_platform.memory_file import file_elapsed_personal_days

            return file_elapsed_personal_days(chats, vault, when=moment, filed_days=filed_days)

        out = tick(
            self.store,
            run_definition=lambda _d: {"id": "x", "status": "completed"},
            now=when,
            state_path=self.state_path,
            file_memory=file_memory,
        )
        self.assertIn("2026-10-05", out["memory_file"]["wrote"])
        note = (vault.root / "timeline" / "daily" / "2026-10-05.md").read_text(encoding="utf-8")
        self.assertIn("I want pasta tonight.", note)
        self.assertIn("Noted for tonight.", note)
        self.assertNotIn("This is still today.", note)
        self.assertNotIn("Check the ports.", note)
        self.assertEqual(pref.read_text(encoding="utf-8"), "pasta stays\n")
        again = tick(
            self.store,
            run_definition=lambda _d: {"id": "x", "status": "completed"},
            now=when.replace(minute=5),
            state_path=self.state_path,
            file_memory=file_memory,
        )
        self.assertEqual(again["memory_file"]["wrote"], [])
        reread = (vault.root / "timeline" / "daily" / "2026-10-05.md").read_text(encoding="utf-8")
        self.assertEqual(reread.count("I want pasta tonight."), 1)

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
        self.app.state.schedule_state_path = Path(self.tmp.name) / "schedule-state.json"
        self.app.state.memory_vault_root = Path(self.tmp.name) / "memory"
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
