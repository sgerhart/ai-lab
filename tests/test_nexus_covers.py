"""Cover extraction and Nexus book suggestions."""

from __future__ import annotations

import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.nexus_covers import book_file_for_cover, embedded_image, epub_cover  # noqa: E402
from ai_lab_platform.nexus_library import suggest_books  # noqa: E402

PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010802000000907753de"
    "0000000c4944415408d763f8ffff3f0005fe02fea7d6a2c10000000049454e44ae426082"
)
JPEG = bytes.fromhex(
    "ffd8ffe000104a46494600010100000100010000ffdb004300080606070605080707"
    "070909080a0c140d0c0b0b0c1912130f141d1a1f1e1d1a1c1c20242e2720222c231c"
    "1c2837292c30313434341f27393d38323c2e333432ffc0000b080001000101011100"
    "ffc4001f0000010501010101010100000000000000000102030405060708090a0bff"
    "da00080001000100003f00fbffd9"
)


class _Hit:
    def __init__(self, title: str, rel_path: str, text: str, score: float, chapter: str = "Chapter 2") -> None:
        self.title = title
        self.rel_path = rel_path
        self.text = text
        self.score = score
        self.chapter = chapter


class NexusCoverTests(unittest.TestCase):
    def test_epub_cover_comes_from_the_opf(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "Blue_Team.epub"
            with zipfile.ZipFile(path, "w") as zf:
                zf.writestr(
                    "META-INF/container.xml",
                    '<?xml version="1.0"?><container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">'
                    '<rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>',
                )
                zf.writestr(
                    "OEBPS/content.opf",
                    '<?xml version="1.0"?><package xmlns="http://www.idpf.org/2007/opf"><metadata>'
                    '<meta name="cover" content="cover-img"/></metadata><manifest>'
                    '<item id="cover-img" href="images/cover.png" media-type="image/png"/>'
                    "</manifest></package>",
                )
                zf.writestr("OEBPS/images/cover.png", PNG)
            found = epub_cover(path)
        self.assertIsNotNone(found)
        assert found is not None
        self.assertEqual(found[1], "image/png")
        self.assertTrue(found[0].startswith(b"\x89PNG"))

    def test_pdf_cover_is_the_embedded_jpeg(self) -> None:
        found = embedded_image(b"preamble" + JPEG + b"trailer")
        self.assertIsNotNone(found)
        assert found is not None
        self.assertEqual(found[1], "image/jpeg")
        self.assertTrue(found[0].startswith(b"\xff\xd8"))

    def test_cover_path_cannot_leave_the_library(self) -> None:
        self.assertIsNone(book_file_for_cover("../secrets.epub"))
        self.assertIsNone(book_file_for_cover("..\\secrets.pdf"))

    def test_suggest_books_uses_index_hits_before_titles(self) -> None:
        def searcher(query: str, limit: int) -> list[_Hit]:
            self.assertIn("observability", query)
            self.assertGreaterEqual(limit, 4)
            return [
                _Hit(
                    "Learning eBPF",
                    "04_Books_Library/Cloud_Platform_and_eBPF/Learning_eBPF.pdf",
                    "Kernel probes show network observability.",
                    0.81,
                )
            ]

        hits = suggest_books("how does kernel observability work", searcher=searcher)
        self.assertEqual(hits[0]["title"], "Learning eBPF")
        self.assertIn("observability", str(hits[0]["snippet"]))

    def test_suggest_books_matches_titles_when_the_index_is_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / "04_Books_Library" / "Cybersecurity"
            folder.mkdir(parents=True)
            (folder / "Blue_Team_Handbook.epub").write_bytes(b"epub")
            hits = suggest_books(
                "what does the blue team handbook cover",
                root=root,
                searcher=lambda _query, _limit: [],
            )
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["title"], "Blue Team Handbook")
        self.assertEqual(hits[0]["snippet"], "The title matches what you asked.")


if __name__ == "__main__":
    unittest.main()
