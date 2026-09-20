import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

try:
    from fastapi.testclient import TestClient
    from langgraph.checkpoint.memory import MemorySaver
    from langgraph.types import Command
    from ai_lab_platform.dispatch import StudioUnavailable
    from ai_lab_platform.slice_graph import build_slice_graph, thread_config
except Exception as exc:  # pragma: no cover - stdlib-only CI without extras
    TestClient = None  # type: ignore[misc, assignment]
    MemorySaver = None  # type: ignore[misc, assignment]
    Command = None  # type: ignore[misc, assignment]
    StudioUnavailable = Exception  # type: ignore[misc, assignment]
    build_slice_graph = None  # type: ignore[misc, assignment]
    thread_config = None  # type: ignore[misc, assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None

from ai_lab_platform.store import SqliteStore
from ai_lab_platform.work_order import Status, WorkOrder


def _store() -> SqliteStore:
    tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
    tmp.close()
    return SqliteStore(tmp.name)


def _order(store: SqliteStore) -> WorkOrder:
    order = WorkOrder.new(
        objective="slice demo",
        agent="lab-operations",
        allowed_tools=["health_read"],
    )
    store.put(order)
    store.set_status(order.id, Status.QUEUED)
    return store.get(order.id)  # type: ignore[return-value]


@unittest.skipIf(IMPORT_ERROR is not None, f"langgraph/fastapi not installed: {IMPORT_ERROR}")
class LangGraphSliceTests(unittest.TestCase):
    def test_submit_worker_approval_resume_complete(self) -> None:
        store = _store()
        order = _order(store)

        def dispatch(payload: dict) -> dict:
            self.assertEqual(payload["work_order_id"], order.id)
            return {"ok": True, "detail": "studio-ok"}

        saver = MemorySaver()
        graph = build_slice_graph(store, dispatch, saver)
        cfg = thread_config(order.id)
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
            cfg,
        )
        self.assertTrue(result.get("__interrupt__"))
        paused = store.get(order.id)
        assert paused is not None
        self.assertEqual(paused.status, Status.AWAITING_APPROVAL)

        graph.invoke(Command(resume="approved"), cfg)
        done = store.get(order.id)
        assert done is not None
        self.assertEqual(done.status, Status.COMPLETED)
        self.assertIn("studio-ok", done.final_result or "")

    def test_recovery_after_control_plane_restart(self) -> None:
        store = _store()
        order = _order(store)
        saver = MemorySaver()

        def dispatch(_payload: dict) -> dict:
            return {"ok": True, "detail": "from-studio"}

        graph1 = build_slice_graph(store, dispatch, saver)
        cfg = thread_config(order.id)
        graph1.invoke(
            {
                "work_order_id": order.id,
                "objective": order.objective,
                "agent": order.agent,
                "studio_ok": False,
                "studio_detail": "",
                "error": "",
                "approval": "",
            },
            cfg,
        )
        self.assertEqual(store.get(order.id).status, Status.AWAITING_APPROVAL)  # type: ignore[union-attr]

        graph2 = build_slice_graph(store, dispatch, saver)
        snapshot = graph2.get_state(cfg)
        self.assertIn("await_approval", snapshot.next)
        graph2.invoke(Command(resume="approved"), cfg)
        self.assertEqual(store.get(order.id).status, Status.COMPLETED)  # type: ignore[union-attr]

    def test_studio_unavailable_does_not_drop_work_order(self) -> None:
        store = _store()
        order = _order(store)

        def dispatch(_payload: dict) -> dict:
            raise StudioUnavailable("connection refused")

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
        self.assertEqual(current.status, Status.QUEUED)
        self.assertIn("studio_unavailable", current.log_refs)
        self.assertIsNotNone(store.get(order.id))


@unittest.skipIf(IMPORT_ERROR is not None, f"langgraph/fastapi not installed: {IMPORT_ERROR}")
class ControlPlaneApiTests(unittest.TestCase):
    def test_http_slice_and_approve(self) -> None:
        from ai_lab_platform.control_app import create_control_app

        store = _store()

        def dispatch(_payload: dict) -> dict:
            return {"ok": True, "detail": "api-studio"}

        app = create_control_app(store=store, dispatch=dispatch, checkpointer=MemorySaver(), token="t")
        client = TestClient(app)
        denied = client.post("/v1/work-orders", json={"agent": "lab-operations", "objective": "x"})
        self.assertEqual(denied.status_code, 401)
        created = client.post(
            "/v1/work-orders",
            json={"agent": "lab-operations", "objective": "x"},
            headers={"Authorization": "Bearer t"},
        )
        self.assertEqual(created.status_code, 200)
        body = created.json()
        self.assertTrue(body["interrupted"])
        self.assertEqual(body["status"], "awaiting_approval")
        approved = client.post(
            f"/v1/work-orders/{body['id']}/approve",
            json={"decision": "approved"},
            headers={"Authorization": "Bearer t"},
        )
        self.assertEqual(approved.json()["status"], "completed")

    def test_http_studio_down(self) -> None:
        from ai_lab_platform.control_app import create_control_app

        store = _store()

        def dispatch(_payload: dict) -> dict:
            raise StudioUnavailable("timeout")

        app = create_control_app(store=store, dispatch=dispatch, checkpointer=MemorySaver())
        client = TestClient(app)
        created = client.post("/v1/work-orders", json={"agent": "lab-operations", "objective": "x"})
        self.assertEqual(created.json()["status"], "queued")
        self.assertIn("studio_unavailable", created.json()["log_refs"])


if __name__ == "__main__":
    unittest.main()
