"""FEAT-005 / IWO-042 — lab MCP server for IDEs."""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.lab_api_client import LabApiClient, LabApiError
from ai_lab_platform.lab_mcp_server import handle_message, read_message, write_message
from ai_lab_platform.retrieval import InMemoryStore, RetrievalService


class FakeHttpClient(LabApiClient):
    """LabApiClient that serves from an in-process FastAPI app when available."""

    def __init__(self, app) -> None:  # noqa: ANN001
        super().__init__(base_url="http://test", token="t")
        from fastapi.testclient import TestClient

        self._tc = TestClient(app)

    def request(self, method, path, *, body=None, auth=True):  # noqa: ANN001
        headers = {}
        if auth and self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if method == "GET":
            res = self._tc.get(path, headers=headers)
        else:
            res = self._tc.request(method, path, headers=headers, json=body or {})
        if res.status_code >= 400:
            raise LabApiError(f"HTTP {res.status_code}: {res.text[:400]}", status=res.status_code)
        return res.json() if res.content else {}


class McpHandlerTests(unittest.TestCase):
    def test_initialize_and_list(self) -> None:
        client = LabApiClient(base_url="http://127.0.0.1:9", token="")
        init = handle_message({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}, client)
        assert init is not None
        self.assertEqual(init["result"]["serverInfo"]["name"], "ai-lab")
        listed = handle_message({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}, client)
        assert listed is not None
        names = {t["name"] for t in listed["result"]["tools"]}
        self.assertEqual(
            names,
            {"lab_health", "lab_memory_search", "lab_memory_upsert", "lab_scheduler_status"},
        )

    def test_framing_roundtrip(self) -> None:
        buf = io.BytesIO()
        write_message({"jsonrpc": "2.0", "id": 1, "result": {"ok": True}}, buf)
        buf.seek(0)
        msg = read_message(buf)
        self.assertEqual(msg["id"], 1)


try:
    from fastapi.testclient import TestClient
    from langgraph.checkpoint.memory import MemorySaver

    from ai_lab_platform.control_app import create_control_app
    from ai_lab_platform.model_router import ModelRouter
    from ai_lab_platform.settings import Settings
    from ai_lab_platform.store import SqliteStore

    _HAS = True
except ImportError:  # pragma: no cover
    _HAS = False


@unittest.skipUnless(_HAS, "fastapi not installed")
class LabMcpIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.svc = RetrievalService(InMemoryStore())
        self.app = create_control_app(
            store=SqliteStore(Path(self.tmp.name) / "wo.sqlite"),
            checkpointer=MemorySaver(),
            token="t",
            dispatch=lambda _p: {"ok": True, "detail": "x"},
            model_router=ModelRouter(backends={}),
            settings=Settings(api_token="t", agent_worker=False),
            retrieval=self.svc,
        )
        self.client = FakeHttpClient(self.app)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_health_and_memory_tools(self) -> None:
        health = handle_message(
            {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "lab_health", "arguments": {}}},
            self.client,
        )
        assert health is not None
        body = json.loads(health["result"]["content"][0]["text"])
        self.assertTrue(body.get("ok"))

        up = handle_message(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "lab_memory_upsert",
                    "arguments": {"text": "IDE MCP talks to mini", "source": "IWO-042"},
                },
            },
            self.client,
        )
        assert up is not None
        self.assertFalse(up["result"]["isError"])

        search = handle_message(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "lab_memory_search",
                    "arguments": {"query": "IDE MCP", "limit": 3},
                },
            },
            self.client,
        )
        assert search is not None
        payload = json.loads(search["result"]["content"][0]["text"])
        self.assertTrue(payload["matches"])
        self.assertEqual(payload["matches"][0]["source"], "IWO-042")


if __name__ == "__main__":
    unittest.main()
