"""Personal Agent Studio APIs (IWO-024–028) — list, attachments, definitions, MCP."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.agent_definitions import AgentDefinition, AgentDefinitionStore
from ai_lab_platform.attachments import AttachmentError, AttachmentStore
from ai_lab_platform.conversation import Conversation
from ai_lab_platform.mcp_client import (
    call_mcp_tool,
    list_mcp_tools,
    mcp_client_status,
    mcp_tool_name,
    require_mcp_servers,
    upsert_local_server,
)
from ai_lab_platform.mcp import McpDenied
from ai_lab_platform.store import SqliteStore
from ai_lab_platform.tool_runtime import execute_allowed_tool

FAKE_MCP = ROOT / "tests" / "fixtures" / "fake_mcp_server.py"


class ListConversationsTests(unittest.TestCase):
    def test_list_order(self) -> None:
        tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
        tmp.close()
        store = SqliteStore(tmp.name)
        a = Conversation.new(agent="lab-operations", title="a")
        b = Conversation.new(agent="lab-operations", title="b")
        store.put_conversation(a)
        store.put_conversation(b)
        listed = store.list_conversations(limit=10)
        self.assertGreaterEqual(len(listed), 2)
        ids = {c.id for c in listed}
        self.assertIn(a.id, ids)
        self.assertIn(b.id, ids)

    def test_delete_conversation(self) -> None:
        tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
        tmp.close()
        store = SqliteStore(tmp.name)
        c = Conversation.new(agent="lab-operations", title="gone")
        store.put_conversation(c)
        self.assertTrue(store.delete_conversation(c.id))
        self.assertIsNone(store.get_conversation(c.id))
        self.assertFalse(store.delete_conversation(c.id))


class AttachmentStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.store = AttachmentStore(self.root)
        self.cid = "11111111-2222-3333-4444-555555555555"

    def test_save_md_and_extract(self) -> None:
        meta = self.store.save(
            conversation_id=self.cid,
            filename="notes.md",
            data=b"# Hello\nworld",
            content_type="text/markdown",
        )
        self.assertEqual(meta["filename"], "notes.md")
        text = self.store.extract_text_for_prompt(self.cid, [meta["id"]])
        self.assertIn("Hello", text)

    def test_rejects_exe(self) -> None:
        with self.assertRaises(AttachmentError):
            self.store.save(
                conversation_id=self.cid,
                filename="x.exe",
                data=b"MZ",
            )


class AgentDefinitionStoreTests(unittest.TestCase):
    def test_roundtrip(self) -> None:
        path = Path(tempfile.mkdtemp()) / "defs.sqlite"
        store = AgentDefinitionStore(path)
        d = AgentDefinition.new(title="Morning", agent="lab-operations", system_prompt="check")
        store.put(d)
        got = store.get(d.id)
        self.assertIsNotNone(got)
        self.assertEqual(got.title, "Morning")
        self.assertEqual(len(store.list()), 1)


class McpClientTests(unittest.TestCase):
    def test_status_deny_unlisted(self) -> None:
        path = Path(tempfile.mkdtemp()) / "mcp-servers.json"
        with mock.patch.dict(os.environ, {"AI_LAB_MCP_SERVERS": str(path)}):
            status = mcp_client_status()
        self.assertEqual(status["policy"], "deny-unlisted")
        self.assertEqual(status["listed_servers"], [])
        self.assertEqual(status["local_servers"], [])

    def test_require_unlisted_denied(self) -> None:
        path = Path(tempfile.mkdtemp()) / "mcp-servers.json"
        with mock.patch.dict(os.environ, {"AI_LAB_MCP_SERVERS": str(path)}):
            with self.assertRaises(McpDenied):
                require_mcp_servers(["filesystem"])

    def test_local_upsert_allows(self) -> None:
        path = Path(tempfile.mkdtemp()) / "mcp-servers.json"
        with mock.patch.dict(os.environ, {"AI_LAB_MCP_SERVERS": str(path)}):
            upsert_local_server(
                server_id="filesystem",
                label="FS",
                command="npx -y @modelcontextprotocol/server-filesystem /tmp",
            )
            status = mcp_client_status()
            self.assertIn("filesystem", status["listed_servers"])
            self.assertIn(status["transport"], {"stdio", "stdio-ready"})
            require_mcp_servers(["filesystem"])

    def test_stdio_list_and_call(self) -> None:
        path = Path(tempfile.mkdtemp()) / "mcp-servers.json"
        cmd = f"{sys.executable} {FAKE_MCP}"
        with mock.patch.dict(os.environ, {"AI_LAB_MCP_SERVERS": str(path)}):
            upsert_local_server(server_id="fake", label="Fake", command=cmd, transport="stdio")
            tools = list_mcp_tools("fake")
            self.assertTrue(any(t["name"] == "echo" for t in tools))
            self.assertEqual(tools[0]["agent_tool"], "mcp/fake/echo")
            result = call_mcp_tool("fake", "echo", {"text": "hi"})
            self.assertTrue(result["ok"])
            self.assertIn("echo:hi", result["observation"])

    def test_tool_runtime_mcp_route(self) -> None:
        path = Path(tempfile.mkdtemp()) / "mcp-servers.json"
        cmd = f"{sys.executable} {FAKE_MCP}"
        with mock.patch.dict(os.environ, {"AI_LAB_MCP_SERVERS": str(path)}):
            upsert_local_server(server_id="fake", label="Fake", command=cmd)
            name = mcp_tool_name("fake", "echo")
            result = execute_allowed_tool(
                name,
                {"text": "lab"},
                allowed_tools=[name],
                approved_tools=set(),
            )
            self.assertTrue(result.ok)
            self.assertIn("echo:lab", result.observation)


if __name__ == "__main__":
    unittest.main()
