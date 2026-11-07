"""Unit tests for Staff Scientist peer agent dialogue and tools (IWO-129)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.scientist_agent import (  # noqa: E402
    SCIENTIST_SYSTEM_PROMPT,
    scientist_chat,
    search_nexus_books,
    search_web_literature,
)

try:
    from fastapi.testclient import TestClient

    from ai_lab_platform.control_app import create_control_app
    from ai_lab_platform.settings import Settings
    from ai_lab_platform.store import SqliteStore
except Exception as exc:  # pragma: no cover
    TestClient = None  # type: ignore[misc, assignment]
    create_control_app = None  # type: ignore[misc, assignment]
    Settings = None  # type: ignore[misc, assignment]
    SqliteStore = None  # type: ignore[misc, assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


class ScientistAgentLogicTests(unittest.TestCase):
    def test_system_prompt_persona(self) -> None:
        self.assertIn("Staff Scientist", SCIENTIST_SYSTEM_PROMPT)
        self.assertIn("laboratory bench", SCIENTIST_SYSTEM_PROMPT)
        self.assertIn("back-and-forth dialogue", SCIENTIST_SYSTEM_PROMPT)
        self.assertIn("192 books", SCIENTIST_SYSTEM_PROMPT)

    def test_search_nexus_books(self) -> None:
        hits = search_nexus_books("attention", limit=2)
        # Even if offline or running without qdrant, returns structured list
        self.assertIsInstance(hits, list)

    def test_search_web_literature(self) -> None:
        hits = search_web_literature("DeepSeek reasoning")
        self.assertIsInstance(hits, list)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["source"], "web_literature")

    def test_scientist_chat_with_concept(self) -> None:
        res = scientist_chat(
            "Why do we need 1/sqrt(d_k) in self-attention?",
            concept_id="self-attention",
        )
        self.assertIn("reply", res)
        self.assertIn("Scaled Dot-Product Self-Attention", res["reply"])
        self.assertIn("citations", res)
        self.assertGreater(len(res["citations"]), 0)
        self.assertEqual(res["concept"], "self-attention")

    def test_scientist_chat_math_derivation(self) -> None:
        res = scientist_chat(
            "Show me the mathematical variance proof and numbers",
            concept_id="attention-variance-proof",
        )
        self.assertIn("reply", res)
        self.assertIn("Variance", res["reply"])

    def test_scientist_chat_with_completion_fn(self) -> None:
        mock_complete = lambda p: "Peer review: here is the tensor verification."
        res = scientist_chat(
            "Let's test this model",
            concept_id="self-attention",
            complete_fn=mock_complete,
        )
        self.assertEqual(res["reply"], "Peer review: here is the tensor verification.")


@unittest.skipUnless(TestClient is not None, f"fastapi testclient unavailable: {IMPORT_ERROR}")
class ScientistAgentApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
        self.tmp.close()
        settings = Settings(api_token="lab-token")
        app = create_control_app(
            store=SqliteStore(self.tmp.name),
            token="lab-token",
            settings=settings,
        )
        self.client = TestClient(app)
        self.headers = {"Authorization": "Bearer lab-token"}

    def test_scientist_chat_requires_auth(self) -> None:
        res = self.client.post(
            "/v1/lab/scientist/chat",
            json={"message": "Hello from the bench"},
        )
        self.assertEqual(res.status_code, 401)

    def test_scientist_chat_authenticated_turn(self) -> None:
        res = self.client.post(
            "/v1/lab/scientist/chat",
            headers=self.headers,
            json={
                "message": "Let's review the attention variance proof and check our library",
                "concept_id": "self-attention",
                "history": [],
            },
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("reply", data)
        self.assertIn("citations", data)
        self.assertIn("tools_used", data)
        self.assertEqual(data["concept"], "self-attention")

