"""Catalog grants are real reads. Catalog MCP stays off until authorized."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.capabilities import capability_catalog  # noqa: E402
from ai_lab_platform.tool_catalog import access_for, extra_read_tools  # noqa: E402


class ToolCatalogTests(unittest.TestCase):
    def test_a_build_grants_repo_reads_and_not_edits(self) -> None:
        access = access_for("Implement a patch in the repo.", "build", shape="agent")
        self.assertEqual(access["tools"], ["repo_read", "repo_search", "git_status", "git_diff"])
        self.assertNotIn("apply_patch", extra_read_tools(access["tools"] + ["apply_patch", "git_push", "deploy"]))

    def test_virustotal_match_keeps_url_submit_off_the_grant(self) -> None:
        access = access_for("Read the VirusTotal file reputation.", "learn", shape="agent")
        self.assertEqual(access["mcp_offers"], ["virustotal"])
        self.assertIn("get_file_report", access["mcp_tools"])
        self.assertNotIn("get_url_report", access["mcp_tools"])
        self.assertNotIn("search_vt", access["mcp_tools"])

    def test_catalog_cards_are_off_and_do_not_carry_a_command(self) -> None:
        cat = capability_catalog("coding-assistant")
        raw = json.dumps(cat)
        self.assertNotIn("npx", raw)
        gmail = next(item for item in cat["capabilities"] if item["id"] == "mcp:gmail")
        self.assertEqual(gmail["connection_state"], "off")
        self.assertFalse(gmail["permitted"])
        self.assertIn("search_threads", [tool["name"] for tool in gmail["tools"]])
        self.assertNotIn("create_draft", [tool["name"] for tool in gmail["tools"]])


if __name__ == "__main__":
    unittest.main()
