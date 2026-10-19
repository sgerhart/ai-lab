"""Unit tests for nexus_rag book chunking and Qdrant RAG store."""

from __future__ import annotations

import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.nexus_rag import (  # noqa: E402
    NexusBookChunk,
    NexusRagStore,
    chunk_epub,
    index_book,
)
from ai_lab_platform.nexus_study import extract_book_context  # noqa: E402


class NexusRagTests(unittest.TestCase):
    def test_chunk_epub_creates_structured_segments(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            epub_path = Path(tmp) / "Test_Leadership.epub"
            with zipfile.ZipFile(epub_path, "w") as z:
                z.writestr(
                    "OEBPS/Text/chapter-1.html",
                    "<html><body><h1>Chapter 1: Foundations</h1>"
                    + "<p>" + ("Code reviews improve software architecture and quality. " * 30) + "</p>"
                    + "</body></html>",
                )
                z.writestr(
                    "OEBPS/Text/chapter-2.html",
                    "<html><body><h1>Chapter 2: Git Workflows</h1>"
                    + "<p>" + ("About 94% of organizations use Git as their version control system. " * 20) + "</p>"
                    + "</body></html>",
                )

            chunks = chunk_epub(epub_path, "04_Books_Library/Test_Leadership.epub", "Test Leadership")
            self.assertGreater(len(chunks), 1)
            self.assertEqual(chunks[0].title, "Test Leadership")
            self.assertIn("Chapter 1", chunks[0].chapter)
            self.assertIn("Code reviews improve", chunks[0].text)

            ch2_chunks = [c for c in chunks if "Chapter 2" in c.chapter]
            self.assertTrue(len(ch2_chunks) > 0)
            self.assertIn("94% of organizations", ch2_chunks[0].text)

    def test_nexus_rag_store_search(self) -> None:
        mock_response = {
            "result": [
                {
                    "id": "11111111-2222-3333-4444-555555555555",
                    "score": 0.88,
                    "payload": {
                        "title": "Looks Good to Me",
                        "rel_path": "04_Books_Library/Looks_Good_to_Me.pdf",
                        "chapter": "Chapter 2",
                        "text": "About 94% of organizations use Git as their version control system.",
                        "chunk_index": 5,
                    },
                }
            ]
        }
        store = NexusRagStore(url="http://fake-qdrant:6333", api_key="secret")
        store._ensured = True

        with patch.object(store, "_request", return_value=mock_response):
            results = store.search("Git version control", rel_path="04_Books_Library/Looks_Good_to_Me.pdf")
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].title, "Looks Good to Me")
            self.assertIn("94% of organizations", results[0].text)
            self.assertAlmostEqual(results[0].score, 0.88)

    def test_extract_book_context_uses_qdrant_when_available(self) -> None:
        mock_chunk = NexusBookChunk(
            id="test-id",
            title="Looks Good to Me",
            rel_path="04_Books_Library/Looks_Good_to_Me.pdf",
            chapter="Chapter 2",
            text="94% of organizations use Git as version control.",
            chunk_index=0,
            score=0.92,
        )

        with patch("ai_lab_platform.nexus_rag.NexusRagStore.search", return_value=[mock_chunk]):
            with tempfile.TemporaryDirectory() as tmp:
                dummy_pdf = Path(tmp) / "Looks_Good_to_Me.pdf"
                dummy_pdf.write_bytes(b"%PDF-1.4 dummy content")
                with patch("ai_lab_platform.nexus_study.resolve_book_file", return_value=dummy_pdf):
                    res = extract_book_context("04_Books_Library/Looks_Good_to_Me.pdf", "Git version control")
                    self.assertIn('[Excerpt from "Looks Good to Me" (Chapter 2)]', res)
                    self.assertIn("94% of organizations use Git", res)


if __name__ == "__main__":
    unittest.main()
