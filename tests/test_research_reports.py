"""Personal-agent research and reports. The model does not choose the URL."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.agent_loop import run_until_idle  # noqa: E402
from ai_lab_platform.conversation import AgentRun, AgentRunStatus, BillingClass  # noqa: E402
from ai_lab_platform.model_router import ModelRouter, ScriptedToolBackend  # noqa: E402
from ai_lab_platform.research_reports import ReportError, ReportLibrary  # noqa: E402
from ai_lab_platform.store import SqliteStore  # noqa: E402
from ai_lab_platform.tool_runtime import build_tool_context  # noqa: E402
from ai_lab_platform.web_lookup import research_pages  # noqa: E402

PUBLIC = ["8.8.8.8"]
WIKI = (
    '["coast",["Geography of Mexico"],[""],'
    '["https://en.wikipedia.org/wiki/Geography_of_Mexico"]]'
)
DDG = (
    '<a class="result__a" href="https://en.wikipedia.org/wiki/Coast">Coast</a>'
)
PAGES = {
    "https://en.wikipedia.org/wiki/Geography_of_Mexico": (
        "<html><head><title>Geography of Mexico</title></head>"
        "<body><p>The coastline is 9,330 km.</p></body></html>"
    ),
    "https://en.wikipedia.org/wiki/Coast": (
        "<html><head><title>Coast</title></head>"
        "<body><p>A coast is the zone where land meets sea.</p></body></html>"
    ),
}


class _Resp:
    def __init__(self, body: bytes, url: str):
        self._body = body
        self.status = 200
        self.headers = {"Content-Type": "text/html; charset=utf-8"}
        self._url = url

    def read(self, n: int = -1) -> bytes:
        if n < 0:
            data, self._body = self._body, b""
            return data
        data, self._body = self._body[:n], self._body[n:]
        return data

    def geturl(self) -> str:
        return self._url

    def close(self) -> None:
        return None


class _Opener:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def open(self, req, timeout=None):  # noqa: ANN001
        url = req.full_url
        self.calls.append(url)
        if "wikipedia.org/w/api.php" in url:
            return _Resp(WIKI.encode(), url)
        if "duckduckgo.com" in url:
            return _Resp(DDG.encode(), url)
        for page, body in PAGES.items():
            if url.startswith(page):
                return _Resp(body.encode(), url)
        raise AssertionError(url)


class ResearchPagesTests(unittest.TestCase):
    def test_gather_keeps_two_pages_the_lab_chose(self) -> None:
        opener = _Opener()
        brief, sources = research_pages(
            "What is the coastline of Mexico?",
            opener=opener,
            resolve=lambda _host: list(PUBLIC),
        )
        self.assertIn("hits=2", brief)
        self.assertIn("9,330 km", brief)
        self.assertIn("land meets sea", brief)
        self.assertEqual(len(sources), 2)
        self.assertTrue(all(item["url"].startswith("https://") for item in sources))

    def test_a_url_in_the_question_is_not_fetched(self) -> None:
        opener = _Opener()
        brief, sources = research_pages(
            "Read https://en.wikipedia.org/wiki/Geography_of_Mexico for the coastline",
            opener=opener,
            resolve=lambda _host: list(PUBLIC),
        )
        self.assertEqual(sources, [])
        self.assertIn("does not open a URL", brief)
        self.assertEqual(opener.calls, [])


class ReportLibraryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.library = ReportLibrary(Path(self.tmp.name) / "reports")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_write_then_revise(self) -> None:
        first = self.library.write("Mexico Coast", "The coast is long and sandy.")
        self.assertIn("mexico-coast.md", first)
        revised = "The revised conclusion is 9,330 km of coastline."
        self.library.write("mexico-coast.md", revised)
        text = self.library.read("Mexico Coast")
        self.assertIn(revised, text)
        self.assertNotIn("sandy", text)

    def test_escape_and_symlink_stay_inside(self) -> None:
        outside = Path(self.tmp.name) / "outside.md"
        outside.write_text("secret")
        with self.assertRaises(ReportError):
            self.library.write("../outside.md", "nope")
        self.assertEqual(outside.read_text(encoding="utf-8"), "secret")
        self.library.root.mkdir(parents=True, exist_ok=True)
        link = self.library.root / "mexico.md"
        link.symlink_to(outside)
        with self.assertRaises(ReportError):
            self.library.write("mexico", "replaced")
        self.assertEqual(outside.read_text(encoding="utf-8"), "secret")
        listed = self.library.list_reports()
        self.assertNotIn("secret", listed)

    def test_dossier_appends_a_deeper_query(self) -> None:
        source = {
            "url": "https://en.wikipedia.org/wiki/Geography_of_Mexico",
            "title": "Geography of Mexico",
            "document_date": "",
            "body": "The coastline is 9,330 km.",
            "error": "",
        }
        self.library.add_dossier("mexico", "What is the coastline of Mexico?", [source])
        self.library.add_dossier("mexico", "How was that coastline measured?", [source])
        text = (self.library.root / "mexico.sources.md").read_text(encoding="utf-8")
        self.assertIn("What is the coastline of Mexico?", text)
        self.assertIn("How was that coastline measured?", text)
        self.assertIn("9,330 km", text)

    def test_empty_report_is_refused(self) -> None:
        with self.assertRaises(ReportError):
            self.library.write("mexico", "   ")


class PersonalResearchRunTests(unittest.TestCase):
    def test_research_then_report_then_revise(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        reports = Path(tmp.name) / "reports"
        previous_reports = os.environ.get("AI_LAB_REPORTS_ROOT")
        previous_vault = os.environ.get("AI_LAB_MEMORY_VAULT")
        os.environ["AI_LAB_REPORTS_ROOT"] = str(reports)
        os.environ["AI_LAB_MEMORY_VAULT"] = str(Path(tmp.name) / "memory")
        self.addCleanup(self._restore_env, previous_reports, previous_vault)
        opener = _Opener()
        store = SqliteStore(Path(tmp.name) / "wo.sqlite")
        scripted = ScriptedToolBackend(
            [
                {
                    "type": "tool",
                    "name": "research",
                    "args": {"query": "What is the coastline of Mexico?", "name": "mexico"},
                },
                {
                    "type": "tool",
                    "name": "report_write",
                    "args": {
                        "name": "mexico",
                        "body": "Mexico has about 9,330 km of coastline. The coast is where land meets sea.",
                    },
                },
                {
                    "type": "tool",
                    "name": "report_write",
                    "args": {
                        "name": "mexico",
                        "body": "Revised report: the cited coastline is 9,330 km.",
                    },
                },
                {"type": "final", "text": "Revised report saved."},
            ]
        )
        router = ModelRouter(backends={"scripted": scripted}, default_backend="scripted")
        run = AgentRun.new(
            agent="personal",
            objective="Research the coastline of Mexico and write a report.",
            backend="scripted",
            billing_class=BillingClass.LOCAL,
        )
        run.budget.max_steps = 16
        store.put_agent_run(run)
        ctx = build_tool_context()
        ctx.vault_root = Path(tmp.name) / "memory"
        ctx.web_opener = opener
        ctx.web_resolve = lambda _host: list(PUBLIC)
        done = run_until_idle(run, router=router, store_put=store.put_agent_run, ctx=ctx)
        self.assertEqual(done.status, AgentRunStatus.COMPLETED, done.error)
        report = (reports / "mexico.md").read_text(encoding="utf-8")
        dossier = (reports / "mexico.sources.md").read_text(encoding="utf-8")
        self.assertIn("Revised report: the cited coastline is 9,330 km.", report)
        self.assertNotIn("land meets sea", report)
        self.assertIn("9,330 km", dossier)
        self.assertIn("https://en.wikipedia.org/wiki/Geography_of_Mexico", dossier)

    def _restore_env(self, reports: str | None, vault: str | None) -> None:
        if reports is None:
            os.environ.pop("AI_LAB_REPORTS_ROOT", None)
        else:
            os.environ["AI_LAB_REPORTS_ROOT"] = reports
        if vault is None:
            os.environ.pop("AI_LAB_MEMORY_VAULT", None)
        else:
            os.environ["AI_LAB_MEMORY_VAULT"] = vault
