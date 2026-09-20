"""Studio worker executes catalog plans. Skipped without FastAPI extras."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

try:
    from fastapi.testclient import TestClient
    from langgraph.checkpoint.memory import MemorySaver
    from ai_lab_platform.studio_worker import create_worker_app
    from ai_lab_platform.slice_graph import build_slice_graph, thread_config
    from ai_lab_platform.store import SqliteStore
    from ai_lab_platform.work_order import Status, WorkOrder
except Exception as exc:  # pragma: no cover
    TestClient = None  # type: ignore[misc, assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


@unittest.skipIf(IMPORT_ERROR is not None, f"fastapi extras missing: {IMPORT_ERROR}")
class StudioWorkerPlanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.artifacts = Path(tempfile.mkdtemp())
        self.app = create_worker_app(workspace_root=ROOT, artifact_root=self.artifacts)
        self.client = TestClient(self.app)

    def test_health_declares_no_llm(self) -> None:
        body = self.client.get("/health").json()
        self.assertTrue(body["ok"])
        self.assertEqual(body["role"], "studio-worker")
        self.assertFalse(body["llm"])
        self.assertFalse(body["deployed"])

    def test_lab_operations_task(self) -> None:
        created = self.client.post(
            "/v1/tasks",
            json={"work_order_id": "wo-ops", "agent": "lab-operations", "objective": "health"},
        )
        body = created.json()
        self.assertTrue(body["ok"])
        self.assertIn("health_read", body["tools_run"])
        self.assertIn("127.0.0.1:5432", body["detail"])

    def test_research_task_writes_artifact(self) -> None:
        created = self.client.post(
            "/v1/tasks",
            json={"work_order_id": "wo-r", "agent": "research", "objective": "summarize X"},
        )
        body = created.json()
        self.assertTrue(body["ok"])
        self.assertTrue(body["artifacts"])
        text = Path(body["artifacts"][0]).read_text(encoding="utf-8")
        self.assertIn("citations were not invented", text)

    def test_unknown_agent_does_not_raise_away_the_job(self) -> None:
        created = self.client.post(
            "/v1/tasks",
            json={"work_order_id": "wo-x", "agent": "malware-lab", "objective": "no"},
        )
        body = created.json()
        self.assertEqual(created.status_code, 200)
        self.assertFalse(body["ok"])
        self.assertIn("unknown agent", body["detail"])

    def test_graph_persists_plan_failure(self) -> None:
        tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
        tmp.close()
        store = SqliteStore(tmp.name)
        order = WorkOrder.new(objective="bad agent", agent="lab-operations", allowed_tools=["health_read"])
        store.put(order)
        store.set_status(order.id, Status.QUEUED)

        def dispatch(_payload: dict) -> dict:
            return {"ok": False, "detail": "tool exploded", "artifacts": []}

        graph = build_slice_graph(store, dispatch, MemorySaver())
        graph.invoke(
            {
                "work_order_id": order.id,
                "objective": order.objective,
                "agent": order.agent,
                "studio_ok": False,
                "studio_detail": "",
                "error": "",
                "approval": "",
            },
            thread_config(order.id),
        )
        current = store.get(order.id)
        assert current is not None
        self.assertEqual(current.status, Status.FAILED)
        self.assertIn("plan_failed", current.log_refs)
        self.assertIsNotNone(store.get(order.id))

    def test_graph_copies_artifacts_then_pauses(self) -> None:
        tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
        tmp.close()
        store = SqliteStore(tmp.name)
        order = WorkOrder.new(objective="report", agent="research", allowed_tools=["write_report_artifact"])
        store.put(order)
        store.set_status(order.id, Status.QUEUED)

        def dispatch(payload: dict) -> dict:
            resp = self.client.post("/v1/tasks", json=payload)
            return resp.json()

        graph = build_slice_graph(store, dispatch, MemorySaver())
        result = graph.invoke(
            {
                "work_order_id": order.id,
                "objective": order.objective,
                "agent": order.agent,
                "studio_ok": False,
                "studio_detail": "",
                "error": "",
                "approval": "",
            },
            thread_config(order.id),
        )
        self.assertTrue(result.get("__interrupt__"))
        paused = store.get(order.id)
        assert paused is not None
        self.assertEqual(paused.status, Status.AWAITING_APPROVAL)
        self.assertTrue(paused.artifacts)


if __name__ == "__main__":
    unittest.main()
