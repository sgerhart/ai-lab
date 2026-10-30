"""Tests for local macOS MCP bridge (IWO-112)."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.mac_bridge import (
    MAX_READ_BYTES,
    get_bridge_capabilities,
    handle_call,
    mac_notes_list,
    mac_notes_read,
    mac_notes_search,
    mac_system_status,
)


class MacBridgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.notes_dir = Path(self.tmp.name) / "notes"
        self.notes_dir.mkdir(parents=True, exist_ok=True)
        self.patcher = mock.patch.dict(os.environ, {"STEWARD_MAC_NOTES_DIR": str(self.notes_dir)})
        self.patcher.start()

    def tearDown(self) -> None:
        self.patcher.stop()
        self.tmp.cleanup()

    def test_capabilities_are_all_read_only(self) -> None:
        caps = get_bridge_capabilities()
        self.assertGreaterEqual(len(caps), 4)
        for cap in caps:
            self.assertEqual(cap.get("permission_class"), "read")

    def test_notes_list_empty_and_populated(self) -> None:
        empty = mac_notes_list()
        self.assertEqual(empty["count"], 0)
        self.assertEqual(empty["notes"], [])

        (self.notes_dir / "daily.md").write_text("# Daily Log\nAll good today.", encoding="utf-8")
        sub = self.notes_dir / "research"
        sub.mkdir()
        (sub / "rag.md").write_text("# RAG Research\nNotes on chunking.", encoding="utf-8")
        (sub / "ignore.txt").write_text("Not markdown", encoding="utf-8")

        res = mac_notes_list()
        self.assertEqual(res["count"], 2)
        paths = [item["path"] for item in res["notes"]]
        self.assertIn("daily.md", paths)
        self.assertIn("research/rag.md", paths)
        self.assertNotIn("research/ignore.txt", paths)

    def test_path_traversal_refused_on_list(self) -> None:
        res = mac_notes_list("../../../etc")
        self.assertIn("error", res)
        self.assertEqual(res["notes"], [])

    def test_notes_read_and_path_traversal_guard(self) -> None:
        note_file = self.notes_dir / "plan.md"
        note_file.write_text("Step 1: Build companion.\nStep 2: Connect Steward.", encoding="utf-8")

        res = mac_notes_read("plan.md")
        self.assertEqual(res["path"], "plan.md")
        self.assertIn("Step 1: Build companion", res["content"])
        self.assertFalse(res["truncated"])

        traversal = mac_notes_read("../../etc/passwd")
        self.assertIn("error", traversal)
        self.assertIn("traversal", traversal["error"].lower())

        missing = mac_notes_read("nonexistent.md")
        self.assertIn("error", missing)

    def test_notes_read_truncation(self) -> None:
        large_file = self.notes_dir / "large.md"
        large_text = "A" * (MAX_READ_BYTES + 500)
        large_file.write_text(large_text, encoding="utf-8")

        res = mac_notes_read("large.md")
        self.assertTrue(res["truncated"])
        self.assertEqual(len(res["content"]), MAX_READ_BYTES)

    def test_notes_search(self) -> None:
        (self.notes_dir / "alpha.md").write_text("Exploring quantum algorithms.", encoding="utf-8")
        (self.notes_dir / "beta.md").write_text("Exploring classical algorithms.", encoding="utf-8")

        res = mac_notes_search("quantum")
        self.assertEqual(res["count"], 1)
        self.assertEqual(res["matches"][0]["path"], "alpha.md")
        self.assertTrue(res["matches"][0]["content_match"])

        name_res = mac_notes_search("beta")
        self.assertEqual(name_res["count"], 1)
        self.assertEqual(name_res["matches"][0]["path"], "beta.md")

        empty_q = mac_notes_search("")
        self.assertIn("error", empty_q)

    def test_system_status(self) -> None:
        status = mac_system_status()
        self.assertIn("hostname", status)
        self.assertIn("platform", status)
        self.assertIn("power_source", status)
        self.assertIn("time_utc", status)

    def test_handle_call_dispatcher(self) -> None:
        (self.notes_dir / "call_test.md").write_text("Hello from tool call", encoding="utf-8")

        list_res = handle_call("mac_notes_list", {})
        self.assertEqual(list_res["count"], 1)

        read_res = handle_call("mac_notes_read", {"path": "call_test.md"})
        self.assertEqual(read_res["path"], "call_test.md")
        self.assertIn("Hello from tool call", read_res["content"])

        unknown_res = handle_call("unknown_tool", {})
        self.assertIn("error", unknown_res)


if __name__ == "__main__":
    unittest.main()
