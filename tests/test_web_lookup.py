"""Personal-agent web lookup. The model does not choose the URL."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.agent_loop import run_until_idle  # noqa: E402
from ai_lab_platform.conversation import AgentRun, AgentRunStatus, BillingClass  # noqa: E402
from ai_lab_platform.model_router import ModelRouter, ScriptedToolBackend  # noqa: E402
from ai_lab_platform.store import SqliteStore  # noqa: E402
from ai_lab_platform.tool_runtime import build_tool_context, execute_allowed_tool  # noqa: E402
from ai_lab_platform.web_lookup import web_search  # noqa: E402

PUBLIC = ["8.8.8.8"]
WIKI = (
    '["coast",["Geography of Mexico"],[""],'
    '["https://en.wikipedia.org/wiki/Geography_of_Mexico"]]'
)
PAGE = "<html><head><title>Geography of Mexico</title></head><body><p>The coastline is 9,330 km.</p></body></html>"


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
            return _Resp(b"", url)
        if url.startswith("https://en.wikipedia.org/wiki/"):
            return _Resp(PAGE.encode(), url)
        raise AssertionError(url)


class WebLookupTests(unittest.TestCase):
    def test_search_returns_the_page_the_lab_chose(self) -> None:
        opener = _Opener()
        text = web_search(
            "What is the coastline of Mexico?",
            opener=opener,
            resolve=lambda _host: list(PUBLIC),
        )
        self.assertIn("hits=1", text)
        self.assertIn("https://en.wikipedia.org/wiki/Geography_of_Mexico", text)
        self.assertIn("9,330 km", text)
        self.assertTrue(any("wikipedia.org/w/api.php" in url for url in opener.calls))

    def test_a_url_in_the_question_is_not_fetched(self) -> None:
        opener = _Opener()
        text = web_search(
            "What is at https://127.0.0.1/secret today?",
            opener=opener,
            resolve=lambda _host: list(PUBLIC),
        )
        self.assertIn("does not open a URL", text)
        self.assertEqual(opener.calls, [])

    def test_tool_ignores_a_url_argument(self) -> None:
        opener = _Opener()
        ctx = build_tool_context()
        ctx.web_opener = opener
        ctx.web_resolve = lambda _host: list(PUBLIC)
        result = execute_allowed_tool(
            "web_search",
            {"url": "https://127.0.0.1/secret", "query": "ignored"},
            allowed_tools=["web_search"],
            approved_tools=set(),
            ctx=ctx,
        )
        self.assertIn("does not open a URL", result.observation)
        self.assertEqual(opener.calls, [])

    def test_personal_run_can_search_twice(self) -> None:
        opener = _Opener()
        store_path = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
        store_path.close()
        store = SqliteStore(store_path.name)
        scripted = ScriptedToolBackend(
            [
                {"type": "tool", "name": "web_search", "args": {"query": "What is the coastline of Mexico?"}},
                {"type": "tool", "name": "web_search", "args": {"query": "Where is the coastline of Mexico?"}},
                {"type": "final", "text": "9,330 km"},
            ]
        )
        router = ModelRouter(backends={"scripted": scripted}, default_backend="scripted")
        run = AgentRun.new(
            agent="personal",
            objective="Look up the coastline.",
            backend="scripted",
            billing_class=BillingClass.LOCAL,
        )
        run.budget.max_steps = 12
        store.put_agent_run(run)
        ctx = build_tool_context()
        ctx.vault_root = Path(tempfile.mkdtemp())
        ctx.web_opener = opener
        ctx.web_resolve = lambda _host: list(PUBLIC)
        done = run_until_idle(run, router=router, store_put=store.put_agent_run, ctx=ctx)
        self.assertEqual(done.status, AgentRunStatus.COMPLETED, done.final_result)
        self.assertIn("9,330 km", done.final_result or "")
        tools = [trace.get("tool") for trace in done.traces if trace.get("kind") == "tool_result"]
        self.assertEqual(tools, ["web_search", "web_search"])


if __name__ == "__main__":
    unittest.main()
