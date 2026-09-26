"""MCP intake: own server and third-party stdio records stay denied until listed."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.mcp import McpDenied
from ai_lab_platform.mcp_client import (
    authorize_mcp_server,
    bind_mcp_agent,
    binding_allows,
    cve_lookup_mcp_candidate,
    intake_candidates,
    lab_mcp_candidate,
    submit_mcp_intake,
    virustotal_mcp_candidate,
)
from ai_lab_platform.tool_runtime import execute_allowed_tool


class IntakeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.path = Path(tempfile.mkdtemp()) / "mcp-servers.json"
        self.env = mock.patch.dict(os.environ, {"AI_LAB_MCP_SERVERS": str(self.path)})
        self.env.start()

    def tearDown(self) -> None:
        self.env.stop()

    def test_lab_server_is_a_stdio_process(self) -> None:
        candidate = lab_mcp_candidate()
        self.assertEqual(candidate["runs_in"], "stdio-process")
        self.assertTrue(str(candidate["command"]).endswith("scripts/lab-mcp-server.sh"))
        self.assertFalse(candidate["listed"])

    def test_lab_intake_stays_denied_until_authorized(self) -> None:
        saved = submit_mcp_intake(server_id="ai-lab", origin="lab")
        self.assertFalse(saved["listed"])
        self.assertEqual(saved["runs_in"], "stdio-process")
        from ai_lab_platform.mcp_client import require_mcp_servers

        with self.assertRaises(McpDenied):
            require_mcp_servers(["ai-lab"])
        listed = authorize_mcp_server("ai-lab")
        self.assertTrue(listed["listed"])
        require_mcp_servers(["ai-lab"])

    def test_third_party_command_cannot_wrap_the_docker_socket(self) -> None:
        with self.assertRaises(ValueError):
            submit_mcp_intake(
                server_id="files",
                origin="third-party",
                command="npx",
                args=["server", "/var/run/docker.sock"],
                capabilities=[{"name": "list_dir", "permission_class": "read"}],
            )

    def test_privileged_tool_needs_approval_before_a_process_starts(self) -> None:
        submit_mcp_intake(
            server_id="files",
            origin="third-party",
            command="python3",
            args=["-c", "raise SystemExit(1)"],
            capabilities=[{"name": "write_file", "permission_class": "privileged"}],
            credential_ref="files token",
        )
        authorize_mcp_server("files")
        bind_mcp_agent("files", "coding-assistant", ["write_file"])
        self.assertTrue(binding_allows("files", "coding-assistant", "write_file"))
        name = "mcp/files/write_file"
        denied = execute_allowed_tool(name, {}, allowed_tools=[name], approved_tools=set())
        self.assertTrue(denied.denied)
        self.assertIn("approval", denied.observation)

    def test_lookup_candidates_stay_unlisted_until_authorized(self) -> None:
        candidates = {item["id"]: item for item in intake_candidates()}
        self.assertEqual(set(candidates), {"ai-lab", "virustotal", "cve-lookup"})
        for item in candidates.values():
            self.assertFalse(item["listed"])
            self.assertEqual(item["runs_in"], "stdio-process")
        virus = candidates["virustotal"]
        cve = candidates["cve-lookup"]
        self.assertEqual(virus["network_policy"], "public-https")
        self.assertEqual(cve["network_policy"], "public-https")
        self.assertEqual(virus["credential_ref"], "virustotal api key")
        self.assertNotIn("=", virus["credential_ref"])
        self.assertNotIn("get_url_report", virus["first_binding"])
        self.assertNotIn("search_vt", virus["first_binding"])
        for name in ("exploit_search", "shodan_ip_vulns", "nuclei_check", "msf_check"):
            self.assertNotIn(name, {cap["name"] for cap in cve["capabilities"]})
            self.assertNotIn(name, cve["first_binding"])
        saved = submit_mcp_intake(
            server_id="virustotal",
            origin="third-party",
            label=virus["label"],
            command=virus["command"],
            args=list(virus["args"]),
            network_policy=virus["network_policy"],
            credential_ref=virus["credential_ref"],
            capabilities=virus["capabilities"],
        )
        self.assertFalse(saved["listed"])
        from ai_lab_platform.mcp_client import require_mcp_servers

        with self.assertRaises(McpDenied):
            require_mcp_servers(["virustotal"])
        listed = authorize_mcp_server("virustotal")
        self.assertTrue(listed["listed"])
        bind_mcp_agent("virustotal", "security", list(virustotal_mcp_candidate()["first_binding"]))
        self.assertFalse(binding_allows("virustotal", "security", "get_url_report"))
        self.assertFalse(binding_allows("virustotal", "security", "search_vt"))
        self.assertTrue(binding_allows("virustotal", "security", "get_file_report"))

    def test_public_https_is_a_network_class(self) -> None:
        saved = submit_mcp_intake(
            server_id="cve-lookup",
            origin="third-party",
            command=cve_lookup_mcp_candidate()["command"],
            args=list(cve_lookup_mcp_candidate()["args"]),
            network_policy="public-https",
            capabilities=cve_lookup_mcp_candidate()["capabilities"],
        )
        self.assertEqual(saved["network_policy"], "public-https")
        self.assertFalse(saved["listed"])
        with self.assertRaises(ValueError):
            submit_mcp_intake(
                server_id="elsewhere",
                origin="third-party",
                command="npx",
                args=["-y", "cve-mcp"],
                network_policy="internet",
                capabilities=[{"name": "nvd_get", "permission_class": "read"}],
            )

    def test_credential_ref_rejects_a_raw_secret(self) -> None:
        with self.assertRaises(ValueError):
            submit_mcp_intake(
                server_id="files",
                origin="third-party",
                command="npx",
                args=["server"],
                capabilities=[{"name": "list_dir", "permission_class": "read"}],
                credential_ref="sk-live-secretvalue",
            )


if __name__ == "__main__":
    unittest.main()
