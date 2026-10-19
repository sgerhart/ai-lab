"""Tests for Nexus library discovery and iCloud copy."""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.nexus_library import category_for, scan_library, sync_tree  # noqa: E402


class NexusLibraryTests(unittest.TestCase):
    def test_category_follows_the_library_folder(self) -> None:
        self.assertEqual(
            category_for("04_Books_Library/Cybersecurity/Blue_Team.epub"),
            "cyber-books",
        )
        self.assertEqual(
            category_for("04_Books_Library/Cloud_Platform_and_eBPF/Learning_eBPF.pdf"),
            "cloud-books",
        )
        self.assertEqual(
            category_for("04_Books_Library/Software_Engineering/Looks_Good_to_Me_.pdf"),
            "ai-books",
        )
        self.assertEqual(category_for("02_Python_and_Data_Science/pandas.pdf"), "python-ds")
        self.assertEqual(
            category_for("01_AI_and_GenAI/05_Research_Papers/2501.12948v1.pdf"),
            "papers",
        )

    def test_scan_groups_epub_and_pdf_and_skips_other_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            book = root / "04_Books_Library" / "Cybersecurity"
            book.mkdir(parents=True)
            (book / "Blue_Team_Handbook.epub").write_bytes(b"epub")
            (book / "Blue_Team_Handbook.pdf").write_bytes(b"pdf")
            (book / "notes.txt").write_text("skip", encoding="utf-8")
            hidden = root / ".hidden"
            hidden.mkdir()
            (hidden / "Secret.pdf").write_bytes(b"no")

            books = scan_library(root)

        self.assertEqual(len(books), 1)
        self.assertEqual(books[0]["title"], "Blue Team Handbook")
        self.assertEqual(books[0]["category"], "cyber-books")
        formats = books[0]["formats"]
        assert isinstance(formats, list)
        self.assertEqual([item["format"] for item in formats], ["EPUB", "PDF"])

    @unittest.skipUnless(shutil.which("rsync"), "rsync is not installed")
    def test_sync_dry_run_lists_books_without_copying(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "icloud"
            dest = base / "mirror"
            folder = source / "04_Books_Library" / "AI_and_Machine_Learning"
            folder.mkdir(parents=True)
            (folder / "New_Book.epub").write_bytes(b"book")
            dest.mkdir()

            planned = sync_tree(source, dest, folders=("04_Books_Library",), apply=False)
            self.assertTrue(planned["ok"])
            self.assertEqual(planned["copied"], ["04_Books_Library/AI_and_Machine_Learning/New_Book.epub"])
            self.assertFalse((dest / "04_Books_Library").exists())

            applied = sync_tree(source, dest, folders=("04_Books_Library",), apply=True)
            self.assertTrue(applied["ok"])
            self.assertTrue((dest / "04_Books_Library" / "AI_and_Machine_Learning" / "New_Book.epub").is_file())

    def test_sync_of_the_same_folder_copies_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = sync_tree(root, root, apply=True)
        self.assertTrue(result["ok"])
        self.assertEqual(result["copied"], [])


if __name__ == "__main__":
    unittest.main()
