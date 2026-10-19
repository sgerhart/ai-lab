"""FEAT-022 / IWO-107 — Steward access manifest and standing goals."""

from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.agent_definitions import AgentDefinitionStore
from ai_lab_platform.agent_scheduler import tick
from ai_lab_platform.policy import load_policy
from ai_lab_platform.steward import (
    StewardError,
    access_manifest,
    background_tools,
    classify_tool,
    close_goal,
    create_goal,
    list_activity,
    list_goals,
    note_wake_finished,
    pause_goal,
    wake_due,
)


class ManifestTests(unittest.TestCase):
    def test_personal_tools_are_classified(self) -> None:
        policy = load_policy("personal")
        classes = access_manifest(policy)
        named = [name for names in classes.values() for name in names]
        self.assertCountEqual(named, list(policy.allowed_tools))
        self.assertIn("vault_read", classes["see"])
        self.assertIn("vault_write", classes["draft"])
        self.assertIn("schedule_create", classes["approval"])
        self.assertIn("consult_frontier", classes["approval"])
        self.assertNotIn("vault_write", classes["see"])

    def test_unknown_tool_is_never(self) -> None:
        self.assertEqual(classify_tool("send_mail"), "never")
        self.assertEqual(classify_tool("home_read"), "never")


class GoalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "steward" / "goals.json"
        self.when = datetime(2026, 10, 18, 9, 0, tzinfo=ZoneInfo("America/New_York"))

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _goal(self, **kwargs):
        body = {
            "title": "Classroom notes",
            "intent": "Keep the classroom notes current.",
            "wake_cron": "0 9 * * *",
            "see_tools": ["vault_read", "files_read"],
            "path": self.path,
        }
        body.update(kwargs)
        return create_goal(**body)

    def test_create_and_list(self) -> None:
        created = self._goal()
        listed = list_goals(path=self.path)
        self.assertEqual(len(listed), 1)
        goal = listed[0]
        self.assertEqual(goal["id"], created["id"])
        self.assertEqual(goal["title"], "Classroom notes")
        self.assertEqual(goal["intent"], "Keep the classroom notes current.")
        self.assertEqual(goal["status"], "active")
        self.assertEqual(goal["see_tools"], ["vault_read", "files_read"])
        mode = self.path.stat().st_mode & 0o777
        self.assertEqual(mode, 0o600)

    def test_refuses_draft_approval_and_unknown_tools(self) -> None:
        with self.assertRaises(StewardError) as caught:
            self._goal(
                see_tools=["vault_read", "vault_write", "schedule_create", "consult_frontier", "send_mail"]
            )
        message = str(caught.exception)
        self.assertIn("refused", message)
        for name in ("vault_write", "schedule_create", "consult_frontier", "send_mail"):
            self.assertIn(name, message)
        self.assertEqual(list_goals(path=self.path), [])

    def test_background_tools_stay_on_the_see_list(self) -> None:
        goal = self._goal(see_tools=["files_read", "nexus_search", "vault_read"])
        allowed = background_tools(goal)
        see = set(access_manifest()["see"])
        draft = set(access_manifest()["draft"])
        approval = set(access_manifest()["approval"])
        self.assertTrue(set(allowed) <= see)
        self.assertTrue(set(allowed).isdisjoint(draft))
        self.assertTrue(set(allowed).isdisjoint(approval))
        widened = dict(goal)
        widened["see_tools"] = ["vault_read", "vault_write", "schedule_create", "send_mail"]
        self.assertEqual(background_tools(widened), ["vault_read"])

    def test_tick_marks_due_goal_once_without_a_model_run(self) -> None:
        from ai_lab_platform.steward import mark_due

        goal = self._goal()
        calls: list[str] = []

        def runner(definition) -> dict:
            calls.append(definition.id)
            return {"id": "run-1", "status": "queued"}

        def mark(when: datetime) -> list[dict]:
            return mark_due(when, path=self.path)

        store = AgentDefinitionStore(Path(self.tmp.name) / "defs.sqlite")
        first = tick(
            store,
            run_definition=runner,
            now=self.when,
            state_path=Path(self.tmp.name) / "schedule-state.json",
            mark_goals=mark,
        )
        self.assertEqual(calls, [])
        self.assertEqual(len(first["steward_marked"]), 1)
        self.assertEqual(first["steward_marked"][0]["id"], goal["id"])
        marked_at = list_goals(path=self.path)[0]["last_due_at"]
        self.assertTrue(marked_at)

        second = tick(
            store,
            run_definition=runner,
            now=self.when,
            state_path=Path(self.tmp.name) / "schedule-state.json",
            mark_goals=mark,
        )
        self.assertEqual(second["steward_marked"], [])
        self.assertEqual(list_goals(path=self.path)[0]["last_due_at"], marked_at)
        self.assertEqual(calls, [])

    def test_paused_and_closed_goals_are_not_marked(self) -> None:
        from ai_lab_platform.steward import mark_due

        paused = self._goal(title="Paused")
        closed = self._goal(title="Closed", see_tools=["report_read"])
        pause_goal(paused["id"], path=self.path)
        close_goal(closed["id"], path=self.path)
        listed = list_goals(path=self.path)
        self.assertEqual(sorted(item["status"] for item in listed), ["done", "paused"])
        self.assertEqual(mark_due(self.when, path=self.path), [])
        self.assertTrue(all(item["last_due_at"] is None for item in list_goals(path=self.path)))


class WakeTests(unittest.TestCase):
    def setUp(self) -> None:
        from ai_lab_platform.store import SqliteStore

        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "steward" / "goals.json"
        self.store = SqliteStore(Path(self.tmp.name) / "wo.sqlite")
        self.when = datetime(2026, 10, 18, 9, 0, tzinfo=ZoneInfo("America/New_York"))

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _goal(self) -> dict:
        return create_goal(
            title="Classroom notes",
            intent="Keep the classroom notes current.",
            wake_cron="0 9 * * *",
            see_tools=["files_read", "vault_read"],
            path=self.path,
        )

    def test_due_goal_enqueues_one_read_only_run_and_activity(self) -> None:
        goal = self._goal()
        first = wake_due(
            self.when,
            store=self.store,
            path=self.path,
            model="fake-instruct",
            backend="fake",
        )
        self.assertEqual(len(first), 1)
        self.assertEqual(first[0]["activity_status"], "queued")
        runs = self.store.list_agent_runs(None)
        self.assertEqual(len(runs), 1)
        run = runs[0]
        self.assertEqual(run.status.value, "queued")
        self.assertEqual(run.agent, "personal")
        self.assertEqual(run.billing_class.value, "local")
        self.assertEqual(run.steward_goal_id, goal["id"])
        self.assertEqual(run.mcp_server_ids, [])
        self.assertEqual(run.tool_ceiling, ["files_read", "vault_read"])
        for forbidden in ("vault_write", "schedule_create", "consult_frontier", "research"):
            self.assertNotIn(forbidden, run.tool_ceiling)
        activity = list_activity(path=self.path)
        self.assertEqual(activity[0]["run_id"], run.id)
        self.assertEqual(activity[0]["status"], "queued")
        mode = (self.path.with_name("activity.json")).stat().st_mode & 0o777
        self.assertEqual(mode, 0o600)

        second = wake_due(
            self.when,
            store=self.store,
            path=self.path,
            model="fake-instruct",
            backend="fake",
        )
        self.assertEqual(second, [])
        self.assertEqual(len(self.store.list_agent_runs(None)), 1)

    def test_wake_denies_a_draft_tool_and_records_the_result(self) -> None:
        from ai_lab_platform.agent_loop import step_agent_run
        from ai_lab_platform.model_router import CompletionResponse, ModelRouter
        from ai_lab_platform.model_router import BillingClass
        from ai_lab_platform.tool_runtime import ToolContext

        goal = self._goal()
        wake_due(
            self.when,
            store=self.store,
            path=self.path,
            model="fake-instruct",
            backend="capture",
        )
        run = self.store.list_agent_runs(None)[0]
        run.tool_ceiling = ["vault_read", "vault_write", "consult_frontier"]
        captured: dict = {}

        class CaptureBackend:
            billing_class = BillingClass.LOCAL

            def complete(self, request):
                captured["system"] = request.system
                return CompletionResponse(
                    model=request.model,
                    backend="capture",
                    text='TOOL vault_write {"category": "facts", "slug": "no", "body": "no"}',
                    billing_class=BillingClass.LOCAL,
                )

            def health(self) -> dict:
                return {"ok": True, "backend": "capture"}

        ctx = ToolContext(
            workspace_root=Path(self.tmp.name) / "work",
            artifact_root=Path(self.tmp.name) / "work" / "artifacts",
            vault_root=Path(self.tmp.name) / "vault",
        )
        finished = step_agent_run(
            run,
            router=ModelRouter(backends={"capture": CaptureBackend()}, default_backend="capture"),
            store_put=self.store.put_agent_run,
            ctx=ctx,
        )
        self.assertEqual(finished.status.value, "failed")
        self.assertEqual(finished.error, "tool_denied:vault_write")
        self.assertNotIn("vault_write", captured["system"])
        self.assertIn("vault_read", captured["system"])
        noted = note_wake_finished(finished, path=self.path)
        self.assertIsNotNone(noted)
        self.assertEqual(noted["status"], "failed")
        self.assertIn("vault_write", noted["note"])


try:
    from fastapi.testclient import TestClient
    from langgraph.checkpoint.memory import MemorySaver

    from ai_lab_platform.control_app import create_control_app
    from ai_lab_platform.model_router import ModelRouter
    from ai_lab_platform.settings import Settings
    from ai_lab_platform.store import SqliteStore

    _HAS_FASTAPI = True
except ImportError:  # pragma: no cover
    _HAS_FASTAPI = False


@unittest.skipUnless(_HAS_FASTAPI, "fastapi not installed")
class StewardApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        app = create_control_app(
            store=SqliteStore(Path(self.tmp.name) / "wo.sqlite"),
            checkpointer=MemorySaver(),
            token="lab-token",
            settings=Settings(auth_mode="token", agent_worker=False),
            dispatch=lambda _payload: {"ok": True, "detail": "unused"},
            model_router=ModelRouter(backends={}),
        )
        app.state.steward_goals_path = Path(self.tmp.name) / "steward" / "goals.json"
        self.client = TestClient(app)
        self.headers = {"Authorization": "Bearer lab-token"}

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_page_links_goals_and_activity(self) -> None:
        page = self.client.get("/steward")
        self.assertEqual(page.status_code, 200)
        for needle in (
            'id="goal-form"',
            'id="goal-title"',
            'id="see-tools"',
            'id="goals"',
            'id="activity"',
            "/static/steward.js",
        ):
            self.assertIn(needle, page.text)
        script = self.client.get("/static/steward.js")
        self.assertEqual(script.status_code, 200)
        self.assertIn("/v1/steward/goals/", script.text)
        self.assertIn('"pause"', script.text)
        self.assertIn('"close"', script.text)
        self.assertIn("/v1/steward/activity", script.text)
        self.assertIn("textContent", script.text)
        self.assertNotIn("innerHTML", script.text)
        home = self.client.get("/")
        self.assertIn('id="nav-steward"', home.text)
        self.assertIn('href="/steward"', home.text)
        chrome = self.client.get("/static/chrome.js")
        self.assertIn('href: "/steward"', chrome.text)

    def test_routes_require_auth_and_round_trip_a_goal(self) -> None:
        denied = self.client.get("/v1/steward/goals")
        self.assertEqual(denied.status_code, 401)
        activity = self.client.get("/v1/steward/activity", headers=self.headers)
        self.assertEqual(activity.status_code, 200)
        self.assertEqual(activity.json()["activity"], [])
        access = self.client.get("/v1/steward/access", headers=self.headers)
        self.assertEqual(access.status_code, 200)
        self.assertIn("vault_read", access.json()["classes"]["see"])
        self.assertNotIn("vault_write", access.json()["classes"]["see"])

        created = self.client.post(
            "/v1/steward/goals",
            headers=self.headers,
            json={
                "title": "Watch the notes",
                "intent": "Notice when the notes change.",
                "wake_cron": "15 8 * * *",
                "see_tools": ["files_read"],
            },
        )
        self.assertEqual(created.status_code, 200, created.text)
        body = created.json()
        self.assertEqual(body["status"], "active")
        self.assertEqual(body["see_tools"], ["files_read"])
        listed = self.client.get("/v1/steward/goals", headers=self.headers)
        self.assertEqual(listed.json()["goals"][0]["title"], "Watch the notes")

        refused = self.client.post(
            "/v1/steward/goals",
            headers=self.headers,
            json={
                "title": "Too wide",
                "intent": "no",
                "wake_cron": "15 8 * * *",
                "see_tools": ["vault_write"],
            },
        )
        self.assertEqual(refused.status_code, 400)

        paused = self.client.post(f"/v1/steward/goals/{body['id']}/pause", headers=self.headers)
        self.assertEqual(paused.status_code, 200)
        self.assertEqual(paused.json()["status"], "paused")
        closed = self.client.post(f"/v1/steward/goals/{body['id']}/close", headers=self.headers)
        self.assertEqual(closed.status_code, 200)
        self.assertEqual(closed.json()["status"], "done")
        again = self.client.get("/v1/steward/goals", headers=self.headers)
        self.assertEqual(len(again.json()["goals"]), 1)


if __name__ == "__main__":
    unittest.main()
