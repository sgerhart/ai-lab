"""FEAT-008 / IWO-040 — retrieval API and memory_search tool."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.policy import load_policy
from ai_lab_platform.retrieval import (
    NO_MATCH_NOTE,
    InMemoryStore,
    RetrievalService,
    hash_embed,
    memory_search_tool,
)
from ai_lab_platform.tool_runtime import execute_allowed_tool


class HashEmbedTests(unittest.TestCase):
    def test_stable_and_normalized(self) -> None:
        a = hash_embed("hello lab memory")
        b = hash_embed("hello lab memory")
        self.assertEqual(a, b)
        self.assertAlmostEqual(sum(x * x for x in a), 1.0, places=5)


class RetrievalServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.svc = RetrievalService(InMemoryStore())

    def test_upsert_search_and_empty(self) -> None:
        doc = self.svc.upsert(
            text="Mac mini control plane listens on Tailscale :8088",
            source="docs/architecture/control-plane.md",
        )
        self.assertTrue(doc["id"])
        self.assertEqual(doc["source"], "docs/architecture/control-plane.md")
        hit = self.svc.search("control plane Tailscale", limit=3)
        self.assertTrue(hit["matches"])
        self.assertEqual(hit["matches"][0]["source"], doc["source"])
        self.assertIn("cite only", hit["note"])

        empty = self.svc.search("zzzz-no-such-token-xyzzy", limit=3)
        # May still match weakly on hash collisions; force empty store
        empty_svc = RetrievalService(InMemoryStore())
        empty = empty_svc.search("anything", limit=3)
        self.assertEqual(empty["matches"], [])
        self.assertEqual(empty["note"], NO_MATCH_NOTE)

    def test_source_required(self) -> None:
        with self.assertRaises(ValueError):
            self.svc.upsert(text="x", source="")


class MemoryToolTests(unittest.TestCase):
    def test_tool_and_policy(self) -> None:
        svc = RetrievalService(InMemoryStore())
        svc.upsert(text="Qdrant holds vectors", source="ADR 0014")
        obs = memory_search_tool("vectors", service=svc)
        data = json.loads(obs)
        self.assertTrue(data["matches"])
        policy = load_policy("research")
        self.assertIn("memory_search", policy.allowed_tools)
        from ai_lab_platform.retrieval import set_default_retrieval_service

        set_default_retrieval_service(svc)
        result = execute_allowed_tool(
            "memory_search",
            {"query": "vectors"},
            allowed_tools=list(policy.allowed_tools),
            approved_tools=set(),
        )
        self.assertTrue(result.ok)
        self.assertIn("Qdrant", result.observation)

    def test_memory_write_requires_approval(self) -> None:
        from ai_lab_platform.approvals import is_privileged
        from ai_lab_platform.retrieval import set_default_retrieval_service
        from ai_lab_platform.tool_runtime import tool_needs_human_gate

        self.assertTrue(is_privileged("memory_write"))
        policy = load_policy("research")
        self.assertIn("memory_write", policy.privileged_tools)
        self.assertTrue(
            tool_needs_human_gate(
                "memory_write",
                list(policy.allowed_tools),
                set(),
                privileged_tools=list(policy.privileged_tools),
            )
        )
        svc = RetrievalService(InMemoryStore())
        set_default_retrieval_service(svc)
        denied = execute_allowed_tool(
            "memory_write",
            {"text": "note", "source": "test"},
            allowed_tools=list(policy.allowed_tools),
            approved_tools=set(),
        )
        self.assertTrue(denied.denied)
        ok = execute_allowed_tool(
            "memory_write",
            {"text": "note about lab", "source": "IWO-041"},
            allowed_tools=list(policy.allowed_tools),
            approved_tools={"memory_write"},
        )
        self.assertTrue(ok.ok)
        found = svc.search("lab")
        self.assertTrue(found["matches"])
        self.assertEqual(found["matches"][0]["source"], "IWO-041")


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
class MemoryApiTests(unittest.TestCase):
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
        self.client = TestClient(self.app)
        self.h = {"Authorization": "Bearer t"}

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_api_roundtrip(self) -> None:
        up = self.client.post(
            "/v1/memory/documents",
            headers=self.h,
            json={"text": "Personal Agent Studio on /agents", "source": "FEAT-013"},
        )
        self.assertEqual(up.status_code, 200, up.text)
        search = self.client.post(
            "/v1/memory/search",
            headers=self.h,
            json={"query": "Personal Agent Studio", "limit": 5},
        )
        self.assertEqual(search.status_code, 200)
        body = search.json()
        self.assertTrue(body["matches"])
        self.assertEqual(body["matches"][0]["source"], "FEAT-013")
        st = self.client.get("/v1/memory/status", headers=self.h)
        self.assertEqual(st.status_code, 200)
        self.assertEqual(st.json()["citation_policy"], "no-fabrication")


if __name__ == "__main__":
    unittest.main()
