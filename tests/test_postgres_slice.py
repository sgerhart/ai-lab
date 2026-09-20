"""Postgres-backed slice tests. Skipped unless DATABASE_URL is set.

CI and scripts/test-postgres-slice.sh provide an ephemeral database.
This is not a deploy onto the M1 mini.
"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

DSN = os.environ.get("DATABASE_URL", "").strip()

try:
    from fastapi.testclient import TestClient
    from langgraph.checkpoint.postgres import PostgresSaver
    from langgraph.types import Command
except Exception as exc:  # pragma: no cover
    TestClient = None  # type: ignore[misc, assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


def _have_pg() -> bool:
    return bool(DSN) and IMPORT_ERROR is None


@unittest.skipUnless(_have_pg(), "DATABASE_URL not set or langgraph extras missing")
class PostgresSliceTests(unittest.TestCase):
    def setUp(self) -> None:
        from ai_lab_platform.postgres_store import PostgresStore

        self.store = PostgresStore(DSN)
        self.pg_cm = PostgresSaver.from_conn_string(DSN)
        self.saver = self.pg_cm.__enter__()
        self.saver.setup()

    def tearDown(self) -> None:
        self.pg_cm.__exit__(None, None, None)

    def test_postgres_store_roundtrip_and_graph_resume(self) -> None:
        from ai_lab_platform.slice_graph import build_slice_graph, thread_config
        from ai_lab_platform.work_order import Status, WorkOrder

        order = WorkOrder.new(
            objective="pg slice",
            agent="lab-operations",
            allowed_tools=["health_read"],
        )
        self.store.put(order)
        self.store.set_status(order.id, Status.QUEUED)

        def dispatch(_payload: dict) -> dict:
            return {"ok": True, "detail": "pg-studio"}

        graph = build_slice_graph(self.store, dispatch, self.saver)
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
        paused = self.store.get(order.id)
        assert paused is not None
        self.assertEqual(paused.status, Status.AWAITING_APPROVAL)

        # Simulate control-plane restart: new graph, same Postgres checkpointer connection.
        graph2 = build_slice_graph(self.store, dispatch, self.saver)
        graph2.invoke(Command(resume="approved"), cfg)
        done = self.store.get(order.id)
        assert done is not None
        self.assertEqual(done.status, Status.COMPLETED)

    def test_fastapi_uses_postgres_when_dsn_set(self) -> None:
        from ai_lab_platform.control_app import create_control_app
        from ai_lab_platform.postgres_store import PostgresStore
        from ai_lab_platform.settings import Settings

        settings = Settings(database_url=DSN, studio_worker_url="http://127.0.0.1:9")
        store = PostgresStore(DSN)

        def dispatch(_payload: dict) -> dict:
            return {"ok": True, "detail": "from-api"}

        app = create_control_app(
            store=store,
            dispatch=dispatch,
            checkpointer=self.saver,
            settings=settings,
        )
        client = TestClient(app)
        health = client.get("/health").json()
        self.assertEqual(health["work_order_store"], "PostgresStore")
        self.assertEqual(health["checkpoints"], "postgres")
        created = client.post(
            "/v1/work-orders",
            json={"agent": "lab-operations", "objective": "pg api"},
        )
        self.assertEqual(created.json()["status"], "awaiting_approval")
        order_id = created.json()["id"]
        done = client.post(f"/v1/work-orders/{order_id}/approve", json={"decision": "approved"})
        self.assertEqual(done.json()["status"], "completed")


if __name__ == "__main__":
    unittest.main()
