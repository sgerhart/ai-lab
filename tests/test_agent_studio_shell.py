"""Agent Studio shell (IWO-063): studio payload and page structure."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.agent_definitions import AgentDefinition, AgentDefinitionStore

try:
    from fastapi.testclient import TestClient
    from langgraph.checkpoint.memory import MemorySaver

    from ai_lab_platform.control_app import create_control_app
    from ai_lab_platform.model_router import ModelRouter
    from ai_lab_platform.store import SqliteStore

    _HAS_FASTAPI = True
except ImportError:
    _HAS_FASTAPI = False


class StudioPayloadTests(unittest.TestCase):
    def test_studio_payload_roundtrip(self) -> None:
        path = Path(tempfile.mkdtemp()) / "defs.sqlite"
        store = AgentDefinitionStore(path)
        definition = AgentDefinition.new(
            title="Builder",
            agent="coding-assistant",
            studio={"purpose": "build", "tools": ["files", "git"], "memory": {"session": True}},
        )
        store.put(definition)
        got = store.get(definition.id)
        self.assertIsNotNone(got)
        self.assertEqual(got.studio["purpose"], "build")
        self.assertEqual(got.studio["tools"], ["files", "git"])
        self.assertTrue(got.studio["memory"]["session"])


class AgentStudioPageTests(unittest.TestCase):
    def test_page_has_studio_rail_and_canvas(self) -> None:
        html = (ROOT / "platform" / "src" / "ai_lab_platform" / "web" / "agents.html").read_text()
        for needle in (
            'id="studio-rail"',
            'id="studio-canvas"',
            'id="toggle-studio"',
            'id="show-studio"',
            'data-studio="skills"',
            'data-studio="workflows"',
            'data-studio="permissions"',
            "/static/studio.js",
            "/static/studio.css",
        ):
            self.assertIn(needle, html)


@unittest.skipUnless(_HAS_FASTAPI, "fastapi not installed")
class StudioApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        store = SqliteStore(Path(self.tmp.name) / "wo.sqlite")
        self.app = create_control_app(
            store=store,
            checkpointer=MemorySaver(),
            token="lab-token",
            dispatch=lambda _p: {"ok": True, "detail": "x"},
            model_router=ModelRouter(backends={}),
        )
        self.app.state.agent_definition_store = AgentDefinitionStore(Path(self.tmp.name) / "defs.sqlite")
        self.client = TestClient(self.app)
        self.h = {"Authorization": "Bearer lab-token"}

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_put_keeps_studio_fields(self) -> None:
        created = self.client.post(
            "/v1/agent-definitions",
            headers=self.h,
            json={
                "title": "Builder",
                "agent": "coding-assistant",
                "system_prompt": "Purpose: Build",
                "studio": {"purpose": "build", "tools": ["files"]},
            },
        )
        self.assertEqual(created.status_code, 200)
        definition_id = created.json()["id"]
        updated = self.client.put(
            f"/v1/agent-definitions/{definition_id}",
            headers=self.h,
            json={
                "title": "Builder",
                "agent": "coding-assistant",
                "system_prompt": "Purpose: Build",
                "studio": {"purpose": "build", "tools": ["files", "git"], "memory": {"session": True}},
            },
        )
        self.assertEqual(updated.status_code, 200)
        body = updated.json()
        self.assertEqual(body["id"], definition_id)
        self.assertEqual(body["studio"]["tools"], ["files", "git"])
        self.assertEqual(self.client.get("/").text.count('id="studio-rail"'), 1)
