"""Projects group chats. Titles come from a short model reply."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.chat_title import clean_model_title, propose_chat_title, title_is_generic  # noqa: E402
from ai_lab_platform.conversation import Conversation, Project  # noqa: E402
from ai_lab_platform.model_router import CompletionRequest, CompletionResponse  # noqa: E402
from ai_lab_platform.conversation import BillingClass  # noqa: E402
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


class _Named:
    def complete(self, request: CompletionRequest) -> CompletionResponse:
        return CompletionResponse(
            model=request.model,
            backend=request.backend,
            text="Studio disk space",
            billing_class=BillingClass.LOCAL,
        )


class TitleTests(unittest.TestCase):
    def test_generic_titles(self) -> None:
        self.assertTrue(title_is_generic("chat"))
        self.assertTrue(title_is_generic(""))
        self.assertFalse(title_is_generic("Studio disk space"))

    def test_clean_title(self) -> None:
        self.assertEqual(clean_model_title('Title: "Lab health"'), "Lab health")
        self.assertEqual(clean_model_title("<think>hmm</think>\nQdrant memory"), "Qdrant memory")
        self.assertEqual(clean_model_title("[fake:ollama:x] prompt"), "")

    def test_propose_uses_model_text(self) -> None:
        self.assertEqual(
            propose_chat_title(_Named(), backend="ollama", model="llama3.2:3b", user_text="disk?", assistant_text="812 GB free"),
            "Studio disk space",
        )


class ProjectStoreTests(unittest.TestCase):
    def test_round_trip_and_chat_link(self) -> None:
        tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
        tmp.close()
        store = SqliteStore(tmp.name)
        project = Project.new(name="Notebook", description="Jupyter questions")
        store.put_project(project)
        loaded = store.get_project(project.id)
        assert loaded is not None
        self.assertEqual(loaded.description, "Jupyter questions")
        chat = Conversation.new(agent="lab-operations", title="chat")
        chat.project_id = project.id
        store.put_conversation(chat)
        again = store.get_conversation(chat.id)
        assert again is not None
        self.assertEqual(again.project_id, project.id)
        self.assertTrue(store.delete_project(project.id))
        self.assertIsNone(store.get_project(project.id))


@unittest.skipIf(IMPORT_ERROR is not None, f"fastapi/langgraph missing: {IMPORT_ERROR}")
class ProjectApiTests(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
        tmp.close()
        self.store = SqliteStore(tmp.name)
        app = create_control_app(
            store=self.store,
            checkpointer=MemorySaver(),
            token="test-token",
            dispatch=lambda _p: {"ok": True, "detail": "unused"},
        )
        self.client = TestClient(app)
        self.headers = {"Authorization": "Bearer test-token"}

    def test_create_and_add_chat(self) -> None:
        created = self.client.post(
            "/v1/projects",
            headers=self.headers,
            json={"name": "Status page", "description": "Dashboard layout"},
        )
        self.assertEqual(created.status_code, 200, created.text)
        project_id = created.json()["id"]
        chat = self.client.post(
            "/v1/conversations",
            headers=self.headers,
            json={"agent": "lab-operations", "project_id": project_id},
        )
        self.assertEqual(chat.status_code, 200, chat.text)
        self.assertEqual(chat.json()["project_id"], project_id)
        moved = self.client.patch(
            f"/v1/conversations/{chat.json()['id']}",
            headers=self.headers,
            json={"project_id": ""},
        )
        self.assertEqual(moved.status_code, 200, moved.text)
        self.assertEqual(moved.json()["project_id"], "")
        empty = self.client.post("/v1/projects", headers=self.headers, json={"name": "  "})
        self.assertEqual(empty.status_code, 400)


if __name__ == "__main__":
    unittest.main()
