"""IWO-004/005/006/007 — router, model/tool loop, recovery, action approvals."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.agent_loop import (  # noqa: E402
    cancel_agent_run,
    loop_system_prompt,
    parse_model_turn,
    reconcile_stuck_running,
    resolve_pending_action,
    retry_agent_run,
    run_until_idle,
)
from ai_lab_platform.conversation import AgentRun, AgentRunStatus, BillingClass  # noqa: E402
from ai_lab_platform.model_router import (  # noqa: E402
    CompletionRequest,
    DisabledCloudBackend,
    ModelRouter,
    ScriptedToolBackend,
)
from ai_lab_platform.policy import load_policy  # noqa: E402
from ai_lab_platform.store import SqliteStore  # noqa: E402

try:
    from fastapi.testclient import TestClient
    from langgraph.checkpoint.memory import MemorySaver
    from ai_lab_platform.control_app import create_control_app
except Exception as exc:  # pragma: no cover
    TestClient = None  # type: ignore[misc, assignment]
    MemorySaver = None  # type: ignore[misc, assignment]
    create_control_app = None  # type: ignore[misc, assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


def _store() -> SqliteStore:
    tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
    tmp.close()
    return SqliteStore(tmp.name)


class ModelRouterBillingTests(unittest.TestCase):
    def test_cloud_disabled_and_no_silent_fallback(self) -> None:
        router = ModelRouter()
        providers = {p["id"]: p for p in router.list_providers()}
        self.assertFalse(providers["openai"]["enabled"])
        self.assertEqual(providers["openai"]["billing_class"], "usage_billed_api")
        with self.assertRaises(PermissionError):
            router.complete(CompletionRequest(model="gpt", prompt="x", backend="openai"))
        # No silent switch to fake
        self.assertEqual(router.allow_fallback, False)

    def test_fake_usage_recorded(self) -> None:
        router = ModelRouter()
        resp = router.complete(CompletionRequest(model="fake-instruct", prompt="hi", backend="fake"))
        self.assertEqual(resp.billing_class, BillingClass.LOCAL)
        self.assertTrue(router.usage_log())


class ParseModelTurnTests(unittest.TestCase):
    def test_exact_tool_and_final(self) -> None:
        self.assertEqual(
            parse_model_turn('TOOL health_read {}'),
            {"type": "tool", "name": "health_read", "args": {}},
        )
        self.assertEqual(parse_model_turn("FINAL all good"), {"type": "final", "text": "all good"})

    def test_tool_line_inside_prose(self) -> None:
        text = "Sure, I will check.\nTOOL health_read {}\nThanks"
        turn = parse_model_turn(text)
        self.assertEqual(turn["type"], "tool")
        self.assertEqual(turn["name"], "health_read")

    def test_final_wins_when_both_present(self) -> None:
        text = "TOOL health_read {}\nFINAL ports look fine"
        self.assertEqual(
            parse_model_turn(text),
            {"type": "final", "text": "ports look fine"},
        )

    def test_tool_without_args_braces(self) -> None:
        self.assertEqual(
            parse_model_turn("TOOL health_read"),
            {"type": "tool", "name": "health_read", "args": {}},
        )

    def test_json_tool_blob(self) -> None:
        turn = parse_model_turn('{"type": "tool", "name": "repo_read", "args": {"limit": 5}}')
        self.assertEqual(turn["type"], "tool")
        self.assertEqual(turn["name"], "repo_read")
        self.assertEqual(turn["args"], {"limit": 5})

    def test_loop_system_prompt_lists_tools(self) -> None:
        prompt = loop_system_prompt(load_policy("lab-operations"))
        self.assertIn("health_read", prompt)
        self.assertIn("TOOL", prompt)
        self.assertIn("FINAL", prompt)


class AgentLoopTests(unittest.TestCase):
    def test_two_tool_steps_then_final(self) -> None:
        store = _store()
        scripted = ScriptedToolBackend(
            [
                {"type": "tool", "name": "health_read", "args": {}},
                {"type": "tool", "name": "repo_read", "args": {"limit": 5}},
                {"type": "final", "text": "ports checked"},
            ]
        )
        router = ModelRouter(backends={"scripted": scripted}, default_backend="scripted")
        run = AgentRun.new(
            agent="lab-operations",
            objective="check health",
            backend="scripted",
            billing_class=BillingClass.LOCAL,
        )
        run.budget.max_steps = 8
        store.put_agent_run(run)
        done = run_until_idle(run, router=router, store_put=store.put_agent_run)
        self.assertEqual(done.status, AgentRunStatus.COMPLETED)
        tool_results = [t for t in done.traces if t.get("kind") == "tool_result"]
        self.assertGreaterEqual(len(tool_results), 2)
        self.assertIn("ports checked", done.final_result or "")

    def test_disallowed_tool_fails(self) -> None:
        store = _store()
        scripted = ScriptedToolBackend([{"type": "tool", "name": "rm_rf", "args": {}}])
        router = ModelRouter(backends={"scripted": scripted})
        run = AgentRun.new(agent="lab-operations", objective="x", backend="scripted")
        store.put_agent_run(run)
        done = run_until_idle(run, router=router, store_put=store.put_agent_run)
        self.assertEqual(done.status, AgentRunStatus.FAILED)
        self.assertIn("tool_denied", done.error or "")

    def test_budget_exhaustion(self) -> None:
        store = _store()
        scripted = ScriptedToolBackend(
            [{"type": "tool", "name": "health_read", "args": {}} for _ in range(20)]
        )
        router = ModelRouter(backends={"scripted": scripted})
        run = AgentRun.new(agent="lab-operations", objective="x", backend="scripted")
        run.budget.max_steps = 2
        store.put_agent_run(run)
        done = run_until_idle(run, router=router, store_put=store.put_agent_run)
        self.assertEqual(done.status, AgentRunStatus.FAILED)
        self.assertIn("budget_exhausted", done.error or "")

    def test_provider_unavailable_visible(self) -> None:
        store = _store()
        router = ModelRouter(backends={"openai": DisabledCloudBackend("openai")})
        run = AgentRun.new(agent="lab-operations", objective="x", backend="openai")
        store.put_agent_run(run)
        done = run_until_idle(run, router=router, store_put=store.put_agent_run)
        self.assertEqual(done.status, AgentRunStatus.FAILED)
        self.assertIn("provider_unavailable", done.error or "")

    def test_cancel_and_safe_retry(self) -> None:
        store = _store()
        run = AgentRun.new(agent="lab-operations", objective="x", backend="fake")
        run.status = AgentRunStatus.RUNNING
        store.put_agent_run(run)
        cancel_agent_run(run, store.put_agent_run)
        self.assertEqual(store.get_agent_run(run.id).status, AgentRunStatus.CANCELLED)  # type: ignore[union-attr]
        retried = retry_agent_run(store.get_agent_run(run.id), store.put_agent_run)  # type: ignore[arg-type]
        self.assertEqual(retried.status, AgentRunStatus.QUEUED)

    def test_reconcile_stuck_running(self) -> None:
        store = _store()
        run = AgentRun.new(agent="lab-operations", objective="x")
        run.status = AgentRunStatus.RUNNING
        store.put_agent_run(run)
        reconcile_stuck_running(run, store.put_agent_run)
        self.assertEqual(store.get_agent_run(run.id).status, AgentRunStatus.FAILED)  # type: ignore[union-attr]

    def test_privileged_action_gate_and_deny(self) -> None:
        store = _store()
        scripted = ScriptedToolBackend([{"type": "tool", "name": "git_push", "args": {"ref": "main"}}])
        router = ModelRouter(backends={"scripted": scripted})
        run = AgentRun.new(agent="development", objective="push", backend="scripted")
        store.put_agent_run(run)
        paused = run_until_idle(run, router=router, store_put=store.put_agent_run)
        self.assertEqual(paused.status, AgentRunStatus.AWAITING_APPROVAL)
        self.assertIsNotNone(paused.pending_action)
        self.assertEqual(paused.pending_action["tool"], "git_push")  # type: ignore[index]
        denied = resolve_pending_action(
            paused, decision="denied", router=router, store_put=store.put_agent_run
        )
        self.assertEqual(denied.status, AgentRunStatus.FAILED)
        self.assertIn("action_denied", denied.error or "")
        # Ensure the privileged tool never "succeeded"
        self.assertFalse(any(t.get("kind") == "tool_result" and t.get("ok") for t in denied.traces))


@unittest.skipIf(IMPORT_ERROR is not None, f"fastapi missing: {IMPORT_ERROR}")
class MiniApiLoopTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = _store()
        scripted = ScriptedToolBackend(
            [
                {"type": "tool", "name": "health_read", "args": {}},
                {"type": "final", "text": "ok"},
            ]
        )
        self.app = create_control_app(
            store=self.store,
            checkpointer=MemorySaver(),
            token="t",
            dispatch=lambda _p: {"ok": True, "detail": "x"},
            model_router=ModelRouter(backends={"scripted": scripted, "fake": scripted}),
        )
        self.client = TestClient(self.app)
        self.h = {"Authorization": "Bearer t"}

    def test_agents_page_and_execute_run(self) -> None:
        page = self.client.get("/agents")
        self.assertEqual(page.status_code, 200)
        self.assertIn("API bearer token", page.text)
        models = self.client.get("/v1/models", headers=self.h)
        self.assertEqual(models.status_code, 200)
        self.assertTrue(any(p["id"] == "fake" or p["billing_class"] for p in models.json()["providers"]))
        conv = self.client.post("/v1/conversations", headers=self.h, json={"agent": "lab-operations"}).json()
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
        )
        self.assertEqual(run.status_code, 200, run.text)
        body = run.json()
        self.assertIn(body["status"], {"completed", "awaiting_approval", "failed"})
        self.assertTrue(any(t.get("kind") == "tool_result" for t in body["traces"]))

    def test_unauthenticated_mutate(self) -> None:
        denied = self.client.post("/v1/conversations", json={"agent": "lab-operations"})
        self.assertEqual(denied.status_code, 401)


if __name__ == "__main__":
    unittest.main()
