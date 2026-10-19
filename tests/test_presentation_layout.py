"""Slide decks show one full page at a time, and the editor can revise the open deck."""

from __future__ import annotations

import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.conversation import BillingClass  # noqa: E402
from ai_lab_platform.model_router import CompletionRequest, CompletionResponse, ModelRouter  # noqa: E402
from ai_lab_platform.presentations import (  # noqa: E402
    PresentationLibrary,
    _render_html,
    interpret_deck_reply,
)
from ai_lab_platform.tool_runtime import build_tool_context, execute_allowed_tool  # noqa: E402


def _css_block(html: str, selector: str) -> str:
    match = re.search(rf"{re.escape(selector)}\s*\{{([^}}]*)\}}", html)
    if not match:
        raise AssertionError(f"missing css rule {selector}")
    return match.group(1)


class PresentationLayoutTests(unittest.TestCase):
    def test_each_slide_is_its_own_page(self) -> None:
        html = _render_html(
            "Layout Check",
            [
                {"index": "1", "title": "Opening", "body": "Cover copy that must stay on page one."},
                {"index": "2", "title": "Details", "body": "- First point\n- Second point\n- Third point"},
                {"index": "3", "title": "Close", "body": "Closing notes that must not share the cover page."},
            ],
        )
        hero = _css_block(html, ".hero-slide")
        self.assertNotIn("display", hero)
        self.assertIn(".slide:not(.active)", html)
        self.assertIn("display: none !important", _css_block(html, ".slide:not(.active)"))
        self.assertEqual(html.count('class="slide hero-slide active"'), 1)
        self.assertNotIn('class="slide split-slide active"', html)
        self.assertNotIn('class="slide standard-slide active"', html)

    def test_slide_page_scrolls_instead_of_clipping(self) -> None:
        html = _render_html(
            "Long Deck",
            [
                {"index": "1", "title": "Opening", "body": "Short cover."},
                {"index": "2", "title": "Long", "body": "\n".join(f"- Point {n} with enough text to fill a page." for n in range(12))},
            ],
        )
        slide = _css_block(html, ".slide")
        self.assertIn("overflow: auto", slide)
        self.assertNotIn("overflow: hidden", slide)
        self.assertNotIn("min(620px, 86vh)", html)
        self.assertIn("overflow: visible", _css_block(html, ".slide-body"))
        self.assertIn("break-after: page", html)
        self.assertIn("aiLabDeck", html)
        self.assertIn("initialSlide", html)


class DeckEditReplyTests(unittest.TestCase):
    def test_edit_block_replaces_the_deck(self) -> None:
        message, revised = interpret_deck_reply(
            "EDIT\n# Renamed\nNew point\n---\n# Close\nDone",
            instruction="rename the first slide",
        )
        self.assertIn("Updated the slides", message)
        self.assertIn("# Renamed", revised or "")

    def test_answer_leaves_the_deck_alone(self) -> None:
        message, revised = interpret_deck_reply(
            "ANSWER\nSlide two is about delivery.",
            instruction="what does slide two say?",
        )
        self.assertIsNone(revised)
        self.assertIn("delivery", message)

    def test_preamble_before_edit_still_replaces_the_deck(self) -> None:
        _message, revised = interpret_deck_reply(
            "Here is the revised deck:\nEDIT\n# Renamed\nNew point\n---\n# Close\nDone",
            instruction="rename the first slide",
        )
        self.assertIn("# Renamed", revised or "")

    def test_incomplete_edit_does_not_replace_the_deck(self) -> None:
        message, revised = interpret_deck_reply("EDIT\njust a note", instruction="rewrite everything")
        self.assertIsNone(revised)
        self.assertIn("left unchanged", message)


class _EditBackend:
    billing_class = BillingClass.LOCAL

    def __init__(self, text: str) -> None:
        self.text = text

    def complete(self, request: CompletionRequest) -> CompletionResponse:
        return CompletionResponse(
            model=request.model,
            backend="fake",
            text=self.text,
            billing_class=self.billing_class,
        )

    def health(self) -> dict:
        return {"ok": True, "backend": "fake", "enabled": True, "models": ["fake-instruct"]}


class DeckReviseApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.pres = self.root / "presentations"
        os.environ["AI_LAB_PRESENTATIONS_ROOT"] = str(self.pres)
        PresentationLibrary(self.pres).write(
            "demo-deck",
            "Demo Deck",
            "# Opening\nHello\n---\n# Close\nWorld",
        )

    def tearDown(self) -> None:
        os.environ.pop("AI_LAB_PRESENTATIONS_ROOT", None)
        self.tmp.cleanup()

    def _client(self, reply: str):
        from fastapi.testclient import TestClient
        from langgraph.checkpoint.memory import MemorySaver

        from ai_lab_platform.control_app import create_control_app
        from ai_lab_platform.store import SqliteStore

        app = create_control_app(
            store=SqliteStore(self.root / "wo.sqlite"),
            checkpointer=MemorySaver(),
            token="test-token",
            model_router=ModelRouter({"fake": _EditBackend(reply)}, default_backend="fake"),
        )
        return TestClient(app)

    def test_revise_rewrites_the_open_deck(self) -> None:
        client = self._client("EDIT\n# Renamed opening\nHello there\n---\n# Close\nWorld")
        resp = client.post(
            "/v1/artifacts/presentations/demo-deck.html/revise",
            headers={"Authorization": "Bearer test-token"},
            json={"instruction": "rename the first slide", "backend": "fake", "model": "fake-instruct"},
        )
        self.assertEqual(resp.status_code, 200, resp.text)
        body = resp.json()
        self.assertTrue(body["updated"])
        self.assertEqual(body["name"], "demo-deck.html")
        html = (self.pres / "demo-deck.html").read_text(encoding="utf-8")
        self.assertIn("Renamed opening", html)
        self.assertIn(".slide:not(.active)", html)

    def test_question_does_not_rewrite_the_deck(self) -> None:
        before = (self.pres / "demo-deck.html").read_text(encoding="utf-8")
        client = self._client("ANSWER\nThe second slide says World.")
        resp = client.post(
            "/v1/artifacts/presentations/demo-deck.html/revise",
            headers={"Authorization": "Bearer test-token"},
            json={"instruction": "what is on the last slide?", "backend": "fake", "model": "fake-instruct"},
        )
        self.assertEqual(resp.status_code, 200, resp.text)
        self.assertFalse(resp.json()["updated"])
        self.assertEqual((self.pres / "demo-deck.html").read_text(encoding="utf-8"), before)

    def test_presentation_read_returns_markdown(self) -> None:
        result = execute_allowed_tool(
            "presentation_read",
            {"name": "demo-deck.html"},
            allowed_tools=["presentation_read"],
            approved_tools=set(),
            ctx=build_tool_context(),
        )
        self.assertTrue(result.ok)
        self.assertIn("Opening", result.observation)
        self.assertIn("World", result.observation)


if __name__ == "__main__":
    unittest.main()
