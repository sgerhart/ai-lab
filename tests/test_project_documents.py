"""Project documents stay out of other projects (FEAT-008)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.attachments import document_text  # noqa: E402
from ai_lab_platform.retrieval import (  # noqa: E402
    InMemoryStore,
    RetrievalService,
    qdrant_project_filter,
)


class ProjectDocumentTests(unittest.TestCase):
    def test_search_stays_inside_the_project(self) -> None:
        svc = RetrievalService(InMemoryStore())
        svc.add_project_document(
            project_id="alpha",
            text="Alpha notes mention the lab notebook and agents.",
            source="alpha.md",
        )
        svc.add_project_document(
            project_id="beta",
            text="Beta notes mention the lab notebook and billing.",
            source="beta.md",
        )
        alpha = svc.search("lab notebook", project_id="alpha")
        self.assertEqual([hit["source"] for hit in alpha["matches"]], ["alpha.md"])
        block = svc.project_context("lab notebook", "alpha")
        self.assertIn("alpha.md", block)
        self.assertNotIn("beta.md", block)
        self.assertEqual(svc.project_context("lab notebook", ""), "")

    def test_list_and_delete_are_scoped(self) -> None:
        svc = RetrievalService(InMemoryStore())
        saved = svc.add_project_document(project_id="alpha", text="keep me", source="keep.md")
        other = svc.add_project_document(project_id="beta", text="leave me", source="leave.md")
        self.assertEqual(
            [row["filename"] for row in svc.list_project_documents("alpha")],
            ["keep.md"],
        )
        self.assertFalse(svc.delete_document(other["id"], project_id="alpha"))
        self.assertTrue(svc.delete_document(saved["id"], project_id="alpha"))
        self.assertEqual(svc.list_project_documents("alpha"), [])
        self.assertEqual(len(svc.list_project_documents("beta")), 1)

    def test_markdown_text_and_qdrant_filter(self) -> None:
        source, text = document_text("notes.md", b"Work orders stay in the project.")
        self.assertEqual(source, "notes.md")
        self.assertIn("Work orders", text)
        self.assertEqual(
            qdrant_project_filter("alpha"),
            {"must": [{"key": "meta.project_id", "match": {"value": "alpha"}}]},
        )


if __name__ == "__main__":
    unittest.main()
