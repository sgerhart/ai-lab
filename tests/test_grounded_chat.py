"""Allowlisted fetch plus a check that product IDs appear in the source."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.chat_grounding import (  # noqa: E402
    finish_grounded_reply,
    lab_notes,
    prepare_grounded_turn,
    retired_identifiers,
    system_for_chat,
)
from ai_lab_platform.conversation import BillingClass  # noqa: E402
from ai_lab_platform.model_router import CompletionRequest, CompletionResponse, ModelRouter  # noqa: E402
from ai_lab_platform.retrieval import FETCHED_LIBRARY, InMemoryStore, RetrievalService  # noqa: E402
from ai_lab_platform.source_fetch import (  # noqa: E402
    FetchDenied,
    FetchedPage,
    catalog_urls,
    clear_fetch_cache,
    factual_query,
    fetch_page,
    load_allowlist,
    search_pages,
    validate_https_url,
)
from ai_lab_platform.store import SqliteStore  # noqa: E402

try:
    from fastapi.testclient import TestClient
    from langgraph.checkpoint.memory import MemorySaver
    from ai_lab_platform.control_app import create_control_app
except Exception as exc:  # pragma: no cover
    TestClient = None  # type: ignore[misc, assignment]
    MemorySaver = None  # type: ignore[misc, assignment]
    create_control_app = None  # type: ignore[misc, assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None

HOSTS = {"www.cisco.com"}
PUBLIC = ["8.8.8.8"]
PAGE = """<html><head>
<meta property="article:modified_time" content="2026-08-15T12:00:00Z">
</head><body>
<p>Supported leaf switches</p>
<p>N9K-C93180YC-EX</p>
<p>No Longer Supported Hardware</p>
<p>N9K-C9336PQ</p>
<script>N9K-C99999</script>
</body></html>"""


class _Resp:
    def __init__(self, body: bytes = b"", status: int = 200, headers: dict | None = None, url: str = ""):
        self._body = body
        self.status = status
        self.headers = headers or {}
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
    def __init__(self, routes: dict[str, _Resp]):
        self.routes = routes
        self.calls: list[str] = []

    def open(self, req, timeout=None):  # noqa: ANN001
        url = req.full_url
        self.calls.append(url)
        if url not in self.routes:
            raise AssertionError(f"unexpected fetch {url}")
        return self.routes[url]


def _fetch(url: str, routes: dict[str, _Resp], **kwargs) -> FetchedPage:
    return fetch_page(
        url,
        opener=_Opener(routes),
        resolve=lambda _host: list(PUBLIC),
        allowlist=HOSTS,
        use_cache=False,
        now="2026-10-02T02:00:00Z",
        **kwargs,
    )


class AllowlistTests(unittest.TestCase):
    def test_catalog_host_is_allowlisted(self) -> None:
        rows = catalog_urls("Which ACI leaf switches are supported?")
        self.assertTrue(rows)
        host = urlsplit(rows[0]["url"]).hostname
        self.assertIn(host, load_allowlist())
        self.assertEqual(catalog_urls("hello"), [])

    def test_rejects_unsafe_urls(self) -> None:
        with self.assertRaises(FetchDenied):
            validate_https_url("http://www.cisco.com/a", allowlist=HOSTS)
        with self.assertRaises(FetchDenied):
            validate_https_url("https://user:placeholder@www.cisco.com/a", allowlist=HOSTS)
        with self.assertRaises(FetchDenied):
            validate_https_url("https://1.2.3.4/a", allowlist=HOSTS)
        with self.assertRaises(FetchDenied):
            validate_https_url("https://www.cisco.com/a?token=placeholder", allowlist=HOSTS)
        with self.assertRaises(FetchDenied):
            validate_https_url("https://evil.example/a", allowlist=HOSTS)

    def test_private_address_is_not_requested(self) -> None:
        opener = _Opener({})
        page = fetch_page(
            "https://www.cisco.com/a",
            opener=opener,
            resolve=lambda _host: ["127.0.0.1"],
            allowlist=HOSTS,
            use_cache=False,
        )
        self.assertIn("not public", page.error)
        self.assertEqual(opener.calls, [])

    def test_redirect_stays_on_the_allowlist(self) -> None:
        clear_fetch_cache()
        start = "https://www.cisco.com/start"
        nxt = "https://www.cisco.com/ok"
        opener = _Opener(
            {
                start: _Resp(status=302, headers={"Location": "/ok"}, url=start),
                nxt: _Resp(
                    body=PAGE.encode(),
                    status=200,
                    headers={"Content-Type": "text/html"},
                    url=nxt,
                ),
            }
        )
        page = fetch_page(
            start,
            opener=opener,
            resolve=lambda _host: list(PUBLIC),
            allowlist=HOSTS,
            use_cache=False,
            now="2026-10-02T02:00:00Z",
        )
        self.assertEqual(opener.calls, [start, nxt])
        self.assertEqual(page.document_date, "2026-08-15")
        self.assertEqual(page.date_kind, "document")
        self.assertIn("N9K-C93180YC-EX", page.text)
        self.assertNotIn("N9K-C99999", page.text)

    def test_redirect_off_allowlist_is_refused(self) -> None:
        start = "https://www.cisco.com/start"
        opener = _Opener({start: _Resp(status=302, headers={"Location": "https://evil.example/x"}, url=start)})
        page = fetch_page(
            start,
            opener=opener,
            resolve=lambda _host: list(PUBLIC),
            allowlist=HOSTS,
            use_cache=False,
        )
        self.assertIn("not on the fetch allowlist", page.error)
        self.assertEqual(opener.calls, [start])


class GroundingTests(unittest.TestCase):
    def test_unknown_product_id_is_removed_and_dated(self) -> None:
        page = _fetch(
            "https://www.cisco.com/notes",
            {
                "https://www.cisco.com/notes": _Resp(
                    body=PAGE.encode(),
                    headers={"Content-Type": "text/html"},
                    url="https://www.cisco.com/notes",
                )
            },
        )
        turn = prepare_grounded_turn(
            query="Which ACI switches are supported? https://www.cisco.com/notes",
            prompt="Which ACI switches are supported?",
            fetch=lambda url, title="": page,
            catalog=[],
        )
        shown, meta = finish_grounded_reply(
            "Supported switches: N9K-C93180YC-EX and N9K-C99999.",
            turn,
        )
        answer, _footer = shown.split("\n\n---\n", 1)
        self.assertIn("N9K-C93180YC-EX", answer)
        self.assertNotIn("N9K-C99999", answer)
        self.assertIn("Removed because they are not in the source: N9K-C99999", shown)
        self.assertIn("Document date: 2026-08-15", shown)
        self.assertIn("Fetched: 2026-10-02T02:00:00Z", shown)
        self.assertEqual(meta["status"], "sourced")
        self.assertIn("N9K-C93180YC-EX", turn.prompt)
        self.assertNotIn("N9K-C99999", turn.corpus)

    def test_retired_id_is_flagged(self) -> None:
        text = "\n".join(
            [
                "Supported leaf switches",
                "N9K-C93180YC-EX",
                "No Longer Supported Hardware",
                "N9K-C9336PQ",
                "Table 4. Other",
                "N9K-C93180YC-FX",
            ]
        )
        self.assertEqual(retired_identifiers(text), {"n9k-c9336pq"})
        page = FetchedPage(
            url="https://www.cisco.com/notes",
            title="Release notes",
            text=text,
            document_date="2026-08-15",
            date_kind="document",
            fetched_at="2026-10-02T02:00:00Z",
        )
        turn = prepare_grounded_turn(
            query="switches",
            prompt="switches",
            fetch=lambda url, title="": page,
            catalog=[{"url": page.url, "title": page.title, "require_any": ["switches"], "also_any": []}],
        )
        shown, _meta = finish_grounded_reply("Use N9K-C93180YC-EX and N9K-C9336PQ.", turn)
        self.assertIn("Named in a no-longer-supported section: N9K-C9336PQ", shown)
        honest, _meta = finish_grounded_reply("N9K-C9336PQ is no longer supported.", turn)
        self.assertNotIn("Named in a no-longer-supported section", honest)

    def test_unsourced_product_id_is_unverified(self) -> None:
        turn = prepare_grounded_turn(query="hello", prompt="hello", fetch=lambda url, title="": None, catalog=[])
        shown, meta = finish_grounded_reply("The switch is N9K-C93180YC-EX.", turn)
        self.assertTrue(shown.startswith("Unverified."))
        self.assertIn("no document date", shown)
        self.assertNotIn("Document date:", shown)
        self.assertEqual(meta["status"], "unverified")

    def test_ordinary_reply_is_unchanged(self) -> None:
        turn = prepare_grounded_turn(query="hello", prompt="hello", catalog=[])
        shown, meta = finish_grounded_reply("Hello.", turn)
        self.assertEqual(shown, "Hello.")
        self.assertEqual(meta["status"], "plain")

    def test_factual_question_uses_search_and_drops_a_guessed_figure(self) -> None:
        self.assertFalse(factual_query("hello"))
        self.assertTrue(factual_query("What is the coastline of Mexico?"))
        page = FetchedPage(
            url="https://en.wikipedia.org/wiki/Geography_of_Mexico",
            title="Geography of Mexico",
            text="Mexico has 9,330 km of coastline.",
            document_date="2026-03-01",
            date_kind="document",
            fetched_at="2026-10-03T16:00:00Z",
        )
        calls: list[tuple[str, bool]] = []

        def fetch(url: str, title: str = "", public: bool = False) -> FetchedPage:
            calls.append((url, public))
            return page

        turn = prepare_grounded_turn(
            query="What is the coastline of Mexico?",
            prompt="What is the coastline of Mexico?",
            catalog=[],
            fetch=fetch,
            search=lambda query: [{"url": page.url, "title": page.title}],
        )
        shown, meta = finish_grounded_reply("The coastline is 9,330 km. Some sources say 12,000 km.", turn)
        answer, _footer = shown.split("\n\n---\n", 1)
        self.assertEqual(calls, [(page.url, True)])
        self.assertIn("9,330 km", answer)
        self.assertNotIn("12,000", answer)
        self.assertIn("Document date: 2026-03-01", shown)
        self.assertEqual(meta["status"], "sourced")


class SearchParseTests(unittest.TestCase):
    def test_search_reads_wikipedia_and_duckduckgo(self) -> None:
        wiki = (
            '["coast",["Geography of Mexico"],[""],'
            '["https://en.wikipedia.org/wiki/Geography_of_Mexico"]]'
        )
        ddg = (
            '<a class="result__a" href="https://duckduckgo.com/l/?uddg='
            'https%3A%2F%2Fwww.cia.gov%2Fthe-world-factbook%2Fcountries%2Fmexico%2F">Mexico</a>'
        )

        class Opener:
            def open(self, req, timeout=None):  # noqa: ANN001
                url = req.full_url
                body = wiki if "wikipedia.org" in url else ddg
                return _Resp(body=body.encode(), status=200, url=url)

        hits = search_pages(
            "What is the coastline of Mexico?",
            opener=Opener(),
            resolve=lambda _host: list(PUBLIC),
        )
        self.assertEqual(
            [row["url"] for row in hits],
            [
                "https://en.wikipedia.org/wiki/Geography_of_Mexico",
                "https://www.cia.gov/the-world-factbook/countries/mexico/",
            ],
        )

    def test_greeting_is_not_searched(self) -> None:
        self.assertEqual(search_pages("hello"), [])


class _FixedBackend:
    billing_class = BillingClass.LOCAL

    def complete(self, request: CompletionRequest) -> CompletionResponse:
        return CompletionResponse(
            model=request.model,
            backend="fake",
            text="Supported switches: N9K-C93180YC-EX and N9K-C99999.",
            billing_class=self.billing_class,
            usage={"input_tokens": 1, "output_tokens": 1, "estimated_cost_usd": 0.0},
        )

    def health(self) -> dict:
        return {"ok": True, "backend": "fake", "billing_class": "local", "models": ["fake-instruct"]}


@unittest.skipIf(IMPORT_ERROR is not None, f"fastapi/langgraph missing: {IMPORT_ERROR}")
class ChatApiTests(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
        tmp.close()
        self.store = SqliteStore(tmp.name)
        self.app = create_control_app(
            store=self.store,
            checkpointer=MemorySaver(),
            token="test-token",
            dispatch=lambda _p: {"ok": True, "detail": "unused"},
            model_router=ModelRouter(backends={"fake": _FixedBackend()}, default_backend="fake"),
            retrieval=RetrievalService(InMemoryStore()),
        )
        self.client = TestClient(self.app)
        self.headers = {"Authorization": "Bearer test-token"}
        self.page = FetchedPage(
            url="https://www.cisco.com/c/en/us/td/docs/dcn/aci/apic/6x/release-notes/cisco-aci-nx-os-release-notes-1623.html",
            title="Release notes",
            text="Supported leaf switches\nN9K-C93180YC-EX\n",
            document_date="2026-08-15",
            date_kind="document",
            fetched_at="2026-10-02T02:00:00Z",
        )

    def test_chat_fetches_catalog_and_drops_unknown_ids(self) -> None:
        created = self.client.post(
            "/v1/conversations",
            headers=self.headers,
            json={"agent": "lab-operations", "title": "aci"},
        )
        conv_id = created.json()["id"]
        calls: list[str] = []

        def fake_fetch(url: str, title: str = "") -> FetchedPage:
            calls.append(url)
            return self.page

        with patch("ai_lab_platform.chat_grounding.fetch_page", fake_fetch):
            msg = self.client.post(
                f"/v1/conversations/{conv_id}/messages",
                headers=self.headers,
                json={"content": "Which ACI switches are supported?", "role": "user", "reply": True},
            )
        self.assertEqual(msg.status_code, 200, msg.text)
        reply = msg.json()["reply"]["content"]
        answer, _footer = reply.split("\n\n---\n", 1)
        self.assertIn("N9K-C93180YC-EX", answer)
        self.assertNotIn("N9K-C99999", answer)
        self.assertNotIn("N9K-C999", msg.json()["title"])
        self.assertIn("Document date: 2026-08-15", reply)
        self.assertIn("Fetched: 2026-10-02T02:00:00Z", reply)
        self.assertEqual(calls, [self.page.url])

    def test_stream_hides_ids_that_are_not_in_the_source(self) -> None:
        created = self.client.post(
            "/v1/conversations",
            headers=self.headers,
            json={"agent": "lab-operations"},
        )
        conv_id = created.json()["id"]

        def fake_fetch(url: str, title: str = "") -> FetchedPage:
            return self.page

        with patch("ai_lab_platform.chat_grounding.fetch_page", fake_fetch):
            res = self.client.post(
                f"/v1/conversations/{conv_id}/messages/stream",
                headers=self.headers,
                json={"content": "Which ACI leaf switches are supported?", "role": "user"},
            )
        self.assertEqual(res.status_code, 200, res.text)
        self.assertIn("Reading the source", res.text)
        self.assertNotIn('"event": "token"', res.text)
        replaced = res.text.split('"event": "replace"', 1)[1]
        answer = replaced.split("Removed because", 1)[0]
        self.assertIn("N9K-C93180YC-EX", answer)
        self.assertNotIn("N9K-C99999", answer)

    def test_fetched_page_is_stored_on_the_project(self) -> None:
        project = self.client.post("/v1/projects", headers=self.headers, json={"name": "ACI"})
        project_id = project.json()["id"]
        created = self.client.post(
            "/v1/conversations",
            headers=self.headers,
            json={"agent": "lab-operations", "project_id": project_id},
        )
        conv_id = created.json()["id"]

        def fake_fetch(url: str, title: str = "") -> FetchedPage:
            return self.page

        with patch("ai_lab_platform.chat_grounding.fetch_page", fake_fetch):
            msg = self.client.post(
                f"/v1/conversations/{conv_id}/messages",
                headers=self.headers,
                json={"content": "Which ACI switches are supported?", "role": "user", "reply": True},
            )
        self.assertEqual(msg.status_code, 200, msg.text)
        docs = self.app.state.retrieval.list_project_documents(project_id)
        self.assertEqual([row["source"] for row in docs], [self.page.url])


class SharedLibraryTests(unittest.TestCase):
    def test_fetched_page_is_reused_without_a_project(self) -> None:
        svc = RetrievalService(InMemoryStore())
        svc.add_project_document(
            project_id="alpha",
            text="Alpha private coastline of Mexico is 1 km.",
            source="secret.md",
        )
        page = FetchedPage(
            url="https://en.wikipedia.org/wiki/Mexico",
            title="Mexico",
            text="Mexico has a coastline of 9,330 km.",
            document_date="2026-01-01",
            date_kind="document",
            fetched_at="2026-10-01T00:00:00Z",
        )

        def fake_fetch(url: str, title: str = "", public: bool = False) -> FetchedPage:
            return page

        first = prepare_grounded_turn(
            query="What is the coastline of Mexico?",
            prompt="user: What is the coastline of Mexico?",
            retrieval=svc,
            fetch=fake_fetch,
            search=lambda _query: [{"url": page.url, "title": "Mexico"}],
            catalog=[],
        )
        self.assertIn("9,330", first.corpus)
        self.assertNotIn("secret.md", first.corpus)
        calls: list[str] = []

        def refuse_fetch(url: str, title: str = "", public: bool = False) -> FetchedPage:
            calls.append(url)
            return FetchedPage(url=url, title=title, error="should not fetch")

        second = prepare_grounded_turn(
            query="What is the coastline of Mexico?",
            prompt="user: What is the coastline of Mexico?",
            retrieval=svc,
            fetch=refuse_fetch,
            search=lambda _query: [],
            catalog=[],
        )
        self.assertEqual(calls, [])
        self.assertIn("9,330", second.corpus)
        self.assertNotIn("secret.md", second.corpus)
        shown, _meta = finish_grounded_reply("The coastline is 12,000 km.", second)
        body = shown.split("\n\n---\n", 1)[0]
        self.assertNotIn("12,000", body)
        self.assertIn("9,330 km", second.corpus)

    def test_lab_health_is_read_without_a_web_search(self) -> None:
        searched: list[str] = []

        def finder(query: str) -> list[dict[str, str]]:
            searched.append(query)
            return [{"url": "https://en.wikipedia.org/wiki/Health", "title": "Health"}]

        with patch("ai_lab_platform.tools.health_read", return_value="127.0.0.1:8088 open\n"):
            turn = prepare_grounded_turn(
                query="What is the lab health right now?",
                prompt="user: What is the lab health right now?",
                search=finder,
                catalog=[],
            )
        self.assertEqual(searched, [])
        self.assertIn("8088 open", turn.corpus)
        self.assertIn("read just now", turn.prompt)

    def test_project_file_list_stays_in_that_project(self) -> None:
        svc = RetrievalService(InMemoryStore())
        svc.add_project_document(project_id="alpha", text="alpha notes", source="alpha.md", filename="alpha.md")
        svc.add_project_document(project_id="beta", text="beta notes", source="beta.md", filename="beta.md")
        turn = prepare_grounded_turn(
            query="What files are in this project?",
            prompt="user: What files are in this project?",
            project_id="alpha",
            retrieval=svc,
            search=lambda _query: [],
            catalog=[],
        )
        self.assertIn("alpha.md", turn.prompt)
        self.assertNotIn("beta.md", turn.prompt)

    def test_general_local_is_not_told_to_be_brief(self) -> None:
        brief = system_for_chat("AI Lab Assistant", model="llama3.2:3b", sourced=False)
        self.assertIn("briefly", brief)
        full = system_for_chat("AI Lab Assistant", model="qwen3.6:35b-a3b", sourced=False)
        self.assertNotIn("briefly", full)
        sourced = system_for_chat("AI Lab Assistant", model="llama3.2:3b", sourced=True)
        self.assertNotIn("briefly", sourced)

    def test_unrelated_question_does_not_read_ports(self) -> None:
        self.assertEqual(lab_notes("What is the coastline of Mexico?"), "")


class _ShoreEmbedder:
    name = "test-embed"

    def embed(self, text: str, *, query: bool = False) -> list[float]:
        low = (text or "").lower()
        if any(word in low for word in ("shore", "coast")):
            return [1.0, 0.0]
        if any(word in low for word in ("switch", "nexus")):
            return [0.0, 1.0]
        return [0.0, 0.0]


class SemanticLibraryTests(unittest.TestCase):
    def test_different_words_still_find_the_saved_page(self) -> None:
        svc = RetrievalService(InMemoryStore(), embedder=_ShoreEmbedder())
        svc.add_project_document(
            project_id="alpha",
            text="Alpha private coastline of Mexico is 1 km.",
            source="secret.md",
        )
        svc.add_project_document(
            project_id=FETCHED_LIBRARY,
            text="Mexico has a coastline of 9,330 km.",
            source="https://en.wikipedia.org/wiki/Mexico",
            extra_meta={"document_date": "2026-01-01", "kind": "fetched_page"},
        )
        shore = svc.fetched_context("How long is that shoreline?")
        self.assertIn("9,330", shore)
        self.assertNotIn("secret.md", shore)
        switches = svc.fetched_context("Which Nexus leaf switches are supported?")
        self.assertNotIn("9,330", switches)

    def test_image_turn_keeps_what_the_picture_shows(self) -> None:
        def explode(_query: str) -> list[dict[str, str]]:
            raise AssertionError("image turn should not search")

        turn = prepare_grounded_turn(
            query="What model number is printed on this switch?",
            prompt="user: What model number is printed on this switch?",
            search=explode,
            catalog=[],
            has_image=True,
        )
        shown, _meta = finish_grounded_reply("The label reads N9K-C93180YC-EX.", turn)
        self.assertIn("N9K-C93180YC-EX", shown)
        self.assertNotIn("Unverified", shown)


if __name__ == "__main__":
    unittest.main()
