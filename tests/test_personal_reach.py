"""Personal agent is a conversation. Ordinary chat stays a conversation."""

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

    from ai_lab_platform.control_app import create_control_app
    from ai_lab_platform.model_router import ModelRouter
    from ai_lab_platform.store import SqliteStore

    _HAS_FASTAPI = True
except ImportError:
    _HAS_FASTAPI = False


class PersonalReachPageTests(unittest.TestCase):
    def test_sidebar_starts_a_personal_conversation(self) -> None:
        html = (ROOT / "platform/src/ai_lab_platform/web/agents.html").read_text()
        self.assertIn('id="new-personal"', html)
        self.assertIn('id="new-conv"', html)
        self.assertIn('agent === "personal" ? "personal" : "lab-operations"', html)
        self.assertIn("function sendPersonalTurn", html)
        self.assertIn("if (isPersonalConversation())", html)
        self.assertIn("/messages/stream", html)
        self.assertIn('id="composer-hint"', html)
        self.assertNotIn("personal conversations answer through an agent run", html.split("sendPersonalTurn")[0])


@unittest.skipUnless(_HAS_FASTAPI, "fastapi not installed")
class PersonalReachApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.app = create_control_app(
            store=SqliteStore(Path(self.tmp.name) / "wo.sqlite"),
            checkpointer=MemorySaver(),
            token="lab-token",
            dispatch=lambda _p: {"ok": True, "detail": "x"},
            model_router=ModelRouter(backends={}),
        )
        self.client = TestClient(self.app)
        self.h = {"Authorization": "Bearer lab-token"}

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_personal_chat_completion_is_refused(self) -> None:
        personal = self.client.post(
            "/v1/conversations", headers=self.h, json={"agent": "personal"}
        ).json()
        self.assertEqual(personal["agent"], "personal")
        refused = self.client.post(
            f"/v1/conversations/{personal['id']}/messages",
            headers=self.h,
            json={"content": "hello", "role": "user", "reply": True},
        )
        self.assertEqual(refused.status_code, 400)
        self.assertIn("agent run", refused.json()["detail"])
        stored = self.client.post(
            f"/v1/conversations/{personal['id']}/messages",
            headers=self.h,
            json={"content": "hello", "role": "user", "reply": False},
        )
        self.assertEqual(stored.status_code, 200)
        streamed = self.client.post(
            f"/v1/conversations/{personal['id']}/messages/stream",
            headers=self.h,
            json={"content": "hello", "role": "user", "reply": True},
        )
        self.assertEqual(streamed.status_code, 400)
        messages = self.client.get(
            f"/v1/conversations/{personal['id']}/messages", headers=self.h
        ).json()["messages"]
        self.assertEqual([item["content"] for item in messages], ["hello"])

    def test_ordinary_chat_still_accepts_a_user_line(self) -> None:
        chat = self.client.post(
            "/v1/conversations", headers=self.h, json={"agent": "lab-operations"}
        ).json()
        stored = self.client.post(
            f"/v1/conversations/{chat['id']}/messages",
            headers=self.h,
            json={"content": "status", "role": "user", "reply": False},
        )
        self.assertEqual(stored.status_code, 200)
        self.assertEqual(stored.json()["content"], "status")
