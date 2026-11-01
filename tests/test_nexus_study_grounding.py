"""Unit tests for Steward Nexus Study deep grounding integration (IWO-126).

Verifies:
1. nexus_search classification under SEE_TOOLS in steward.py.
2. Query validation (rejecting empty or short queries).
3. Targeted book lookup with chapter-level deep excerpt extraction.
4. Table of contents and parts structure extraction via nexus_search.
5. General library search appending deep technical excerpts from top book hits.
6. Safe, graceful degradation when no matching passages exist.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.approvals import is_privileged, requires_approval  # noqa: E402
from ai_lab_platform.steward import DRAFT_TOOLS, SEE_TOOLS  # noqa: E402
from ai_lab_platform.tool_runtime import ToolContext, execute_allowed_tool  # noqa: E402


class NexusStudyGroundingTests(unittest.TestCase):
    def test_steward_see_tools_invariants(self) -> None:
        """nexus_search must strictly reside in the SEE class (read-only)."""
        self.assertIn("nexus_search", SEE_TOOLS)
        self.assertNotIn("nexus_search", DRAFT_TOOLS)
        self.assertFalse(is_privileged("nexus_search"))
        self.assertFalse(
            requires_approval(
                "nexus_search",
                allowed_tools=["nexus_search"],
                already_approved=set(),
            )
        )

    def test_query_validation(self) -> None:
        """Reject empty or query strings shorter than 3 characters."""
        res_empty = execute_allowed_tool(
            "nexus_search",
            {},
            allowed_tools=["nexus_search"],
            approved_tools=set(),
        )
        self.assertFalse(res_empty.ok)
        self.assertIn("question", res_empty.observation.lower())

        res_short = execute_allowed_tool(
            "nexus_search",
            {"query": "ab"},
            allowed_tools=["nexus_search"],
            approved_tools=set(),
        )
        self.assertFalse(res_short.ok)
        self.assertIn("question", res_short.observation.lower())

    def test_direct_book_and_chapter_grounding(self) -> None:
        """Targeting a specific book and chapter returns direct chapter text."""
        with tempfile.TemporaryDirectory() as tmp:
            epub_path = Path(tmp) / "Distributed_Systems_Patterns.epub"
            with zipfile.ZipFile(epub_path, "w") as z:
                z.writestr(
                    "OEBPS/Text/chapter-1.html",
                    "<html><body><h1>Chapter 1: Network Fundamentals</h1><p>Latency and throughput trade-offs in distributed topologies.</p></body></html>",
                )
                z.writestr(
                    "OEBPS/Text/chapter-2.html",
                    "<html><body><h1>Chapter 2: Raft Consensus</h1><p>Leader election ensures that exactly one node acts as cluster authority.</p></body></html>",
                )

            res = execute_allowed_tool(
                "nexus_search",
                {
                    "book": str(epub_path),
                    "chapter": "2",
                    "query": "leader election authority",
                },
                allowed_tools=["nexus_search"],
                approved_tools=set(),
            )
            self.assertTrue(res.ok)
            self.assertIn("Distributed Systems Patterns", res.observation)
            self.assertIn("Leader election ensures", res.observation)
            self.assertIn("Chapter 2", res.observation)

    def test_direct_book_table_of_contents(self) -> None:
        """Requesting TOC for a book returns the parts and chapters breakdown."""
        with tempfile.TemporaryDirectory() as tmp:
            epub_path = Path(tmp) / "Modern_Software_Architecture.epub"
            with zipfile.ZipFile(epub_path, "w") as z:
                z.writestr(
                    "OEBPS/Text/contents.html",
                    "<html><body><h1>Table of Contents</h1>"
                    "<p>Part 1: Domain-Driven Design</p>"
                    "<p>1 Strategic Modeling</p>"
                    "<p>Part 2: Event-Driven Systems</p>"
                    "<p>4 Event Sourcing and CQRS</p>"
                    "</body></html>",
                )

            res = execute_allowed_tool(
                "nexus_search",
                {
                    "book": str(epub_path),
                    "toc": True,
                },
                allowed_tools=["nexus_search"],
                approved_tools=set(),
            )
            self.assertTrue(res.ok)
            self.assertIn("Modern Software Architecture", res.observation)
            self.assertIn("Part 1: Domain-Driven Design", res.observation)
            self.assertIn("Part 2: Event-Driven Systems", res.observation)
            self.assertIn("Event Sourcing and CQRS", res.observation)

    def test_general_query_includes_deep_excerpts(self) -> None:
        """General technical queries scan the library shelf and append deep excerpts from top hits."""
        with tempfile.TemporaryDirectory() as tmp:
            nexus_root = Path(tmp)
            book_dir = nexus_root / "04_Books_Library" / "Cloud_Platform_and_eBPF"
            book_dir.mkdir(parents=True, exist_ok=True)
            epub_path = book_dir / "Kernel_Observability_eBPF.epub"

            with zipfile.ZipFile(epub_path, "w") as z:
                z.writestr(
                    "OEBPS/Text/ch1.html",
                    "<html><body><h1>Chapter 1: Intro to BPF</h1><p>Early packet filtering filters network frames inside the kernel space.</p></body></html>",
                )
                z.writestr(
                    "OEBPS/Text/ch2.html",
                    "<html><body><h1>Chapter 2: kprobes and tracepoints</h1><p>Attach programs to arbitrary kernel instruction boundaries for observability.</p></body></html>",
                )

            with patch("ai_lab_platform.nexus_study.find_nexus_root", return_value=nexus_root):
                with patch("ai_lab_platform.nexus_library.find_nexus_root", return_value=nexus_root):
                    res = execute_allowed_tool(
                        "nexus_search",
                        {"query": "observability kprobes kernel"},
                        allowed_tools=["nexus_search"],
                        approved_tools=set(),
                    )
                    self.assertTrue(res.ok)
                    self.assertIn("Kernel Observability eBPF", res.observation)
                    self.assertIn("Deep Excerpts from top match", res.observation)
                    self.assertIn("Attach programs to arbitrary kernel instruction", res.observation)

    def test_nonexistent_book_handling(self) -> None:
        """Searching for a completely unknown volume degrades gracefully."""
        res = execute_allowed_tool(
            "nexus_search",
            {"book": "Nonexistent_Volume_9999", "query": "algorithms"},
            allowed_tools=["nexus_search"],
            approved_tools=set(),
        )
        self.assertTrue(res.ok)
        self.assertIn("No Nexus book, paper, or course matched", res.observation)


if __name__ == "__main__":
    unittest.main()
