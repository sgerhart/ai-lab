"""IWO-002: conversation + agent-run contract (FakeBackend only)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.conversation import (  # noqa: E402
    AgentRun,
    AgentRunStatus,
    BillingClass,
    Conversation,
    Message,
    MessageRole,
)
from ai_lab_platform.model_router import CompletionRequest, FakeBackend  # noqa: E402
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


class ConversationStoreTests(unittest.TestCase):
    def test_conversation_message_run_round_trip(self) -> None:
        store = _store()
        conv = Conversation.new(agent="lab-operations", title="ops")
        store.put_conversation(conv)
        self.assertEqual(store.get_conversation(conv.id).agent, "lab-operations")  # type: ignore[union-attr]

        msg = Message.new(conversation_id=conv.id, role=MessageRole.USER, content="health?")
        store.put_message(msg)
        messages = store.list_messages(conv.id)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].content, "health?")
        self.assertEqual(messages[0].meta.get("kind"), None)

        run = AgentRun.new(
            agent="lab-operations",
            conversation_id=conv.id,
            objective="snapshot",
            billing_class=BillingClass.LOCAL,
            backend="fake",
        )
        fake = FakeBackend().complete(
            CompletionRequest(model=run.model, prompt=run.objective, backend="fake")
        )
        run.traces.append({"kind": "placeholder_model_call", "response": fake.text})
        run.status = AgentRunStatus.CREATED
        store.put_agent_run(run)

        loaded = store.get_agent_run(run.id)
        assert loaded is not None
        self.assertEqual(loaded.billing_class, BillingClass.LOCAL)
        self.assertEqual(len(loaded.traces), 1)
        self.assertIn("fake:", loaded.traces[0]["response"])
        self.assertEqual(len(store.list_agent_runs(conv.id)), 1)

    def test_chat_message_is_not_work_order(self) -> None:
        """Ordinary messages must not appear as work_orders rows."""
        store = _store()
        conv = Conversation.new(agent="lab-operations")
        store.put_conversation(conv)
        store.put_message(Message.new(conversation_id=conv.id, role="user", content="hi"))
        self.assertEqual(store.list(), [])
        self.assertEqual(len(store.list_messages(conv.id)), 1)


@unittest.skipIf(IMPORT_ERROR is not None, f"fastapi/langgraph missing: {IMPORT_ERROR}")
class ConversationApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = _store()
        self.app = create_control_app(
            store=self.store,
            checkpointer=MemorySaver(),
            token="test-token",
            dispatch=lambda _p: {"ok": True, "detail": "unused"},
        )
        self.client = TestClient(self.app)
        self.headers = {"Authorization": "Bearer test-token"}

    def test_unauthorized_conversation_create(self) -> None:
        resp = self.client.post("/v1/conversations", json={"agent": "lab-operations"})
        self.assertEqual(resp.status_code, 401)

    def test_conversation_chat_and_run_api(self) -> None:
        created = self.client.post(
            "/v1/conversations",
            headers=self.headers,
            json={"agent": "lab-operations", "title": "t"},
        )
        self.assertEqual(created.status_code, 200, created.text)
        conv_id = created.json()["id"]

        msg = self.client.post(
            f"/v1/conversations/{conv_id}/messages",
            headers=self.headers,
            json={"content": "ping", "role": "user"},
        )
        self.assertEqual(msg.status_code, 200, msg.text)
        self.assertEqual(msg.json()["meta"]["kind"], "chat_turn")

        listed = self.client.get(f"/v1/conversations/{conv_id}/messages", headers=self.headers)
        self.assertEqual(listed.status_code, 200)
        self.assertIn("not runtime work orders", listed.json()["note"])

        run = self.client.post(
            f"/v1/conversations/{conv_id}/runs",
            headers=self.headers,
            json={
                "objective": "lab health snapshot",
                "model": "fake-instruct",
                "billing_class": "local",
                "backend": "fake",
            },
        )
        self.assertEqual(run.status_code, 200, run.text)
        body = run.json()
        self.assertEqual(body["kind"], "agent_run")
        self.assertEqual(body["billing_class"], "local")
        self.assertEqual(len(body["traces"]), 1)
        self.assertIn("fake:", body["traces"][0]["response"])

        got = self.client.get(f"/v1/agent-runs/{body['id']}", headers=self.headers)
        self.assertEqual(got.status_code, 200)
        self.assertEqual(got.json()["id"], body["id"])

        # Chat did not create a work order
        self.assertEqual(self.store.list(), [])

    def test_usage_billed_non_fake_rejected(self) -> None:
        created = self.client.post(
            "/v1/conversations",
            headers=self.headers,
            json={"agent": "lab-operations"},
        )
        conv_id = created.json()["id"]
        denied = self.client.post(
            f"/v1/conversations/{conv_id}/runs",
            headers=self.headers,
            json={
                "objective": "x",
                "billing_class": "usage_billed_api",
                "backend": "openai",
            },
        )
        self.assertEqual(denied.status_code, 400)


if __name__ == "__main__":
    unittest.main()
