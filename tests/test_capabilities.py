"""Capability catalog stays truthful and redacted."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.capabilities import capability_catalog


class CapabilityCatalogTests(unittest.TestCase):
    def test_lab_assistant_reads_are_connected_and_writes_are_absent(self) -> None:
        cat = capability_catalog("lab-operations")
        self.assertTrue(cat["ok"])
        self.assertEqual(cat["assistant_name"], "AI Lab Assistant")
        self.assertEqual(cat["restart_recovery"], "not_yet_verified")
        by_id = {c["id"]: c for c in cat["capabilities"] if c["origin"] == "built_in"}
        self.assertEqual(by_id["built_in:health_read"]["connection_state"], "connected")
        self.assertTrue(by_id["built_in:health_read"]["permitted"])
        self.assertFalse(by_id["built_in:health_read"]["used"])
        self.assertNotIn("built_in:apply_patch", by_id)

    def test_privileged_tool_is_not_permitted_by_presence(self) -> None:
        cat = capability_catalog("coding-assistant")
        patch = next(c for c in cat["capabilities"] if c["id"] == "built_in:apply_patch")
        self.assertEqual(patch["connection_state"], "permission_required")
        self.assertFalse(patch["permitted"])

    def test_mcp_command_is_not_a_connection_or_a_secret_leak(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mcp-servers.json"
            path.write_text(
                json.dumps(
                    {
                        "servers": [
                            {
                                "id": "github",
                                "label": "GitHub <script>",
                                "transport": "stdio",
                                "command": "npx",
                                "args": ["--token", "super-secret-token"],
                                "enabled": True,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            old = os.environ.get("AI_LAB_MCP_SERVERS")
            os.environ["AI_LAB_MCP_SERVERS"] = str(path)
            try:
                cat = capability_catalog("lab-operations")
            finally:
                if old is None:
                    os.environ.pop("AI_LAB_MCP_SERVERS", None)
                else:
                    os.environ["AI_LAB_MCP_SERVERS"] = old
        raw = json.dumps(cat)
        self.assertNotIn("super-secret-token", raw)
        self.assertNotIn("npx", raw)
        mcp = next(c for c in cat["capabilities"] if c["id"] == "mcp:github")
        self.assertEqual(mcp["connection_state"], "configured")
        self.assertIsNone(mcp["last_checked_at"])
        self.assertFalse(mcp["permitted"])
        self.assertEqual(mcp["name"], "GitHub <script>")


if __name__ == "__main__":
    unittest.main()
