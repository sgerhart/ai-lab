"""Saved Nexus summaries and the chat/agent shelf block."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.nexus_library import books_for_query  # noqa: E402
from ai_lab_platform.nexus_summaries import (  # noqa: E402
    load_summary,
    save_summary,
    summary_from_excerpt,
    summary_is_current,
)
from ai_lab_platform.tool_runtime import execute_allowed_tool  # noqa: E402


class _Hit:
    def __init__(self) -> None:
        self.title = "Looks Good to Me"
        self.rel_path = "04_Books_Library/Software_Engineering/Looks_Good_to_Me_.pdf"
        self.text = "A review is a conversation about the change, not a gate."
        self.score = 0.9
        self.chapter = "Chapter 1"


class NexusSummaryTests(unittest.TestCase):
    def test_summary_is_saved_once_for_the_same_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "Looks_Good_to_Me_.pdf"
            source.write_bytes(b"pdf")
            rel = "04_Books_Library/Software_Engineering/Looks_Good_to_Me_.pdf"
            save_summary(rel, source, "A short book about code review.", root=root)
            self.assertIn("code review", load_summary(rel, root=root))
            self.assertTrue(summary_is_current(rel, source, root=root))
            source.write_bytes(b"pdf-changed")
            self.assertFalse(summary_is_current(rel, source, root=root))

    def test_model_summary_uses_only_the_returned_text(self) -> None:
        text = summary_from_excerpt(
            "Looks Good to Me",
            "A review is a conversation about the change. " * 4,
            lambda _title, _excerpt: "It explains how to review a change with a teammate.",
        )
        self.assertIn("teammate", text)

    def test_chat_block_includes_the_saved_summary_and_passage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "Looks_Good_to_Me_.pdf"
            source.write_bytes(b"pdf")
            rel = "04_Books_Library/Software_Engineering/Looks_Good_to_Me_.pdf"
            save_summary(rel, source, "Code review as a conversation.", root=root)
            block = books_for_query(
                "how should I review a change",
                root=root,
                searcher=lambda _query, _limit: [_Hit()],
                summary_root=root,
            )
        self.assertIn("Looks Good to Me", block)
        self.assertIn("Code review as a conversation.", block)
        self.assertIn("Passage:", block)

    def test_agent_tool_rejects_a_question_that_is_too_short(self) -> None:
        result = execute_allowed_tool(
            "nexus_search",
            {"query": "hi"},
            allowed_tools=["nexus_search"],
            approved_tools=set(),
        )
        self.assertFalse(result.ok)
        self.assertIn("question", result.observation)


if __name__ == "__main__":
    unittest.main()
