"""Unit tests for nexus_study book search and grounding."""

from __future__ import annotations

import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.nexus_study import _search_epub, format_book_title  # noqa: E402


class NexusStudyTests(unittest.TestCase):
    def test_search_epub_by_chapter_number(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            epub_path = Path(tmp) / "Test_Book.epub"
            with zipfile.ZipFile(epub_path, "w") as z:
                z.writestr(
                    "OEBPS/Text/chapter-1.html",
                    "<html><body><h1>Chapter 1: Foundations</h1><p>Code reviews improve software quality.</p></body></html>",
                )
                z.writestr(
                    "OEBPS/Text/chapter-2.html",
                    "<html><body><h1>Chapter 2: Git Workflows</h1><p>About 94% of organizations use Git.</p></body></html>",
                )

            res = _search_epub(epub_path, "Summarize chapter 1 of this book")
            self.assertIn("Code reviews improve software quality", res)
            self.assertIn("Chapter 1", res)

    def test_search_epub_by_keywords(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            epub_path = Path(tmp) / "Test_Book.epub"
            with zipfile.ZipFile(epub_path, "w") as z:
                z.writestr(
                    "OEBPS/Text/chapter-1.html",
                    "<p>General introduction to engineering teams and sprint planning.</p>",
                )
                z.writestr(
                    "OEBPS/Text/chapter-2.html",
                    "<p>According to surveys, about 94% of organizations use Git as their version control system.</p>",
                )

            res = _search_epub(epub_path, "How many organizations use Git as their version control system")
            self.assertIn("94% of organizations use Git", res)
            self.assertIn("version control system", res)

    def test_extract_table_of_contents_and_parts(self) -> None:
        from ai_lab_platform.nexus_study import _extract_table_of_contents

        with tempfile.TemporaryDirectory() as tmp:
            epub_path = Path(tmp) / "Looks_Good_to_Me.epub"
            with zipfile.ZipFile(epub_path, "w") as z:
                z.writestr(
                    "OEBPS/Text/contents.html",
                    "<html><body><h1>contents</h1>"
                    "<p>Part 1 Code review foundations</p>"
                    "<p>1 The significance of code reviews</p>"
                    "<p>Part 2 Elevated code review essentials</p>"
                    "<p>4 The Team Working Agreement</p>"
                    "</body></html>",
                )

            res = _extract_table_of_contents(epub_path)
            self.assertIn("Part 1 Code review foundations", res)
            self.assertIn("Part 2 Elevated code review essentials", res)
            self.assertIn("1 The significance of code reviews", res)


class BookTitleFormatTests(unittest.TestCase):
    def test_readable_filenames_keep_small_words_and_acronyms(self) -> None:
        self.assertEqual(format_book_title("Looks_Good_to_Me_.epub"), "Looks Good to Me")
        self.assertEqual(format_book_title("Test_Leadership.epub"), "Test Leadership")
        self.assertEqual(format_book_title("AI_for_Everyday_IT.pdf"), "AI for Everyday IT")
        self.assertEqual(format_book_title("AI-Powered_Search.epub"), "AI-Powered Search")
        self.assertEqual(
            format_book_title("Human-in-the-Loop_Machine_Learning.epub"),
            "Human-in-the-Loop Machine Learning",
        )

    def test_concatenated_slugs_become_titles(self) -> None:
        self.assertEqual(
            format_book_title("blueteamhandbook_incidentresponse.epub"),
            "Blue Team Handbook: Incident Response",
        )
        self.assertEqual(
            format_book_title("defensivesecurityhandbook2ndedition.pdf"),
            "Defensive Security Handbook, 2nd Edition",
        )
        self.assertEqual(
            format_book_title("cybersecuritymanagersguide.epub"),
            "Cybersecurity Manager's Guide",
        )
        self.assertEqual(
            format_book_title("developersplaybookforlargelanguagemodelsecurity.pdf"),
            "Developer's Playbook for Large Language Model Security",
        )

    def test_noise_and_compounds_are_cleaned(self) -> None:
        self.assertEqual(
            format_book_title("NumPy_guide_for_beginners__1734359174.pdf"),
            "NumPy Guide for Beginners",
        )
        self.assertEqual(
            format_book_title("Build_a_Large_Language_Model_(From_Scrat.epub"),
            "Build a Large Language Model (From Scratch)",
        )
        self.assertEqual(format_book_title("Learning-eBPF - Full book.pdf"), "Learning eBPF")
        self.assertEqual(format_book_title("2501.12948v1.pdf"), "2501.12948v1")
        self.assertEqual(format_book_title("C2_W1.pdf"), "C2 W1")
        self.assertEqual(
            format_book_title("the-illusion-of-thinking.pdf"),
            "The Illusion of Thinking",
        )
        self.assertEqual(
            format_book_title("Newwhitepaper_Solving Domain-Specific problems using LLMs.pdf"),
            "New Whitepaper: Solving Domain-Specific Problems Using LLMs",
        )


class StudyAgentPolicyAndApiTests(unittest.TestCase):
    def test_study_agent_policy_definition(self) -> None:
        from ai_lab_platform.policy import load_policy

        policy = load_policy("study")
        self.assertEqual(policy.id, "study")
        self.assertTrue(policy.read_only)
        self.assertEqual(policy.isolation_tier, 0)
        self.assertIn("nexus_search", policy.allowed_tools)
        self.assertIn("memory_search", policy.allowed_tools)
        self.assertEqual(policy.privileged_tools, ())
        self.assertEqual(policy.citation_policy, "no-fabrication")

    def test_create_study_conversation_endpoint(self) -> None:
        from ai_lab_platform.control_app import create_control_app
        from ai_lab_platform.store import SqliteStore
        from langgraph.checkpoint.memory import MemorySaver
        from starlette.testclient import TestClient

        with tempfile.NamedTemporaryFile(suffix=".sqlite") as tmp:
            store = SqliteStore(tmp.name)
            app = create_control_app(
                store=store,
                checkpointer=MemorySaver(),
                token="test-token",
                dispatch=lambda _p: {"ok": True, "detail": "unused"},
            )
            client = TestClient(app)
            headers = {"Authorization": "Bearer test-token"}

            res = client.post(
                "/v1/conversations",
                headers=headers,
                json={"agent": "study", "title": "Study: Foundation of LLM"},
            )
            self.assertEqual(res.status_code, 200, res.text)
            data = res.json()
            self.assertEqual(data["agent"], "study")
            self.assertEqual(data["title"], "Study: Foundation of LLM")


if __name__ == "__main__":
    unittest.main()
