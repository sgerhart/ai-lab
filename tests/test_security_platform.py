"""Security platform foundation, event envelope, and MCP registry."""

from __future__ import annotations

import ast
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.approvals import requires_approval
from ai_lab_platform.mcp import McpDenied
from ai_lab_platform.security.events import (
    EVENT_SCHEMA,
    EmbeddedPayloadRefused,
    EvidenceRef,
    SecurityEvent,
)
from ai_lab_platform.security.mcp_registry import McpRegistry
from ai_lab_platform.security.policy_eval import evaluate_tool
from ai_lab_platform.security.providers import default_providers
from ai_lab_platform.security.store import SqliteEventLog


def _evidence() -> EvidenceRef:
    return EvidenceRef(
        evidence_id="ev-1",
        locator="quarantine://operator-supplied/object",
        sha256="0" * 64,
        media_type="application/octet-stream",
        byte_length=12,
    )


def _event(**overrides: object) -> SecurityEvent:
    fields: dict[str, object] = {
        "provider": "antares",
        "severity": "low",
        "classification": "finding",
        "summary": "file needs review",
        "agent_id": "lab-operations",
        "resource_id": "snapshot",
        "run_id": "run-1",
        "job_id": "job-1",
        "tool": "localize",
        "approval_id": "apr-1",
        "evidence": (_evidence(),),
        "details": {"path": "app.py"},
    }
    fields.update(overrides)
    return SecurityEvent.create(**fields)  # type: ignore[arg-type]


class ImportBoundaryTests(unittest.TestCase):
    def test_security_package_does_not_import_network_modules(self) -> None:
        root = ROOT / "platform" / "src" / "ai_lab_platform" / "security"
        banned = {"socket", "http", "urllib", "httpx", "requests"}
        for path in root.glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                names: list[str] = []
                if isinstance(node, ast.Import):
                    names = [alias.name.split(".")[0] for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    names = [node.module.split(".")[0]]
                for name in names:
                    self.assertNotIn(name, banned, f"{path.name} imports {name}")


class ProviderTests(unittest.TestCase):
    def test_default_providers_cover_antares_defenseclaw_and_vise(self) -> None:
        described = {row["kind"] for row in default_providers().list()}
        self.assertEqual(described, {"antares", "defenseclaw", "vise"})
        for row in default_providers().list():
            self.assertEqual(row["network"], "none")
            self.assertNotIn("http", row["title"])


class PolicyHandoffTests(unittest.TestCase):
    def test_matches_existing_approval_gate(self) -> None:
        cases = [
            ("repo_read", ["repo_read"], set()),
            ("git_push", ["git_push"], set()),
            ("git_push", ["git_push"], {"git_push"}),
            ("rm_rf", ["repo_read"], set()),
        ]
        for tool, allowed, approved in cases:
            decision = evaluate_tool(tool=tool, allowed_tools=allowed, already_approved=approved)
            needs = requires_approval(tool, allowed, approved)
            self.assertEqual(decision["needs_approval"], needs)
            self.assertEqual(decision["allowed"], not needs)
            self.assertEqual(decision["authority"], "approvals.requires_approval")


class EventTests(unittest.TestCase):
    def test_round_trip_correlates_agent_run_tool_and_job(self) -> None:
        original = _event()
        again = SecurityEvent.from_dict(original.to_dict())
        self.assertEqual(again.agent_id, "lab-operations")
        self.assertEqual(again.run_id, "run-1")
        self.assertEqual(again.job_id, "job-1")
        self.assertEqual(again.tool, "localize")
        self.assertEqual(again.approval_id, "apr-1")
        self.assertEqual(again.evidence[0].locator, "quarantine://operator-supplied/object")
        self.assertNotIn("content", again.to_dict()["evidence"][0])

    def test_redacts_secret_keys_and_refuses_embedded_bytes(self) -> None:
        event = _event(details={"api_key": "not a real credential", "path": "app.py"})
        self.assertEqual(event.to_dict()["details"]["api_key"], "[redacted]")
        self.assertEqual(event.to_dict()["details"]["path"], "app.py")
        with self.assertRaises(EmbeddedPayloadRefused):
            _event(details={"sample": "MZ"})

    def test_sqlite_round_trip_filters_by_run(self) -> None:
        tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
        tmp.close()
        log = SqliteEventLog(tmp.name)
        log.append(_event())
        log.append(_event(run_id="run-2", job_id="job-2"))
        matched = log.list(run_id="run-1")
        self.assertEqual(len(matched), 1)
        self.assertEqual(matched[0].job_id, "job-1")

    def test_schema_keys_match_the_envelope(self) -> None:
        body = _event().to_dict()
        self.assertEqual(set(body), set(EVENT_SCHEMA["required"]))
        self.assertEqual(body["schema_version"], 1)


class McpRegistryTests(unittest.TestCase):
    def _allowlist(self, servers: list[dict[str, object]]) -> Path:
        tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        tmp.close()
        path = Path(tmp.name)
        path.write_text(json.dumps({"policy": "deny-unlisted", "servers": servers}), encoding="utf-8")
        return path

    def test_unlisted_capability_stays_denied_and_emits_an_event(self) -> None:
        registry = McpRegistry(allowlist_path=self._allowlist([]))
        catalog = registry.catalog()
        self.assertEqual(catalog[0]["id"], "ai-lab")
        self.assertFalse(catalog[0]["authorized"])
        with self.assertRaises(McpDenied):
            registry.bind("lab-operations", "ai-lab", ["lab_health"])
        decision, event = registry.decide(agent_id="lab-operations", server_id="ai-lab", capability="lab_health", run_id="run-9")
        self.assertFalse(decision.allowed)
        self.assertEqual(event.run_id, "run-9")
        self.assertEqual(event.details["decision"], "deny")

    def test_explicit_binding_allows_only_that_capability(self) -> None:
        registry = McpRegistry(allowlist_path=self._allowlist([{"id": "ai-lab", "purpose": "lab health"}]))
        registry.bind("lab-operations", "ai-lab", ["lab_health"])
        allowed, _event = registry.decide(agent_id="lab-operations", server_id="ai-lab", capability="lab_health")
        denied, denied_event = registry.decide(agent_id="lab-operations", server_id="ai-lab", capability="lab_status")
        self.assertTrue(allowed.allowed)
        self.assertFalse(denied.allowed)
        self.assertEqual(denied_event.classification, "mcp")
        self.assertEqual(len(registry.bindings()), 1)


class SecurityApiTests(unittest.TestCase):
    def setUp(self) -> None:
        from fastapi.testclient import TestClient
        from ai_lab_platform.control_app import create_control_app
        from ai_lab_platform.settings import Settings
        from ai_lab_platform.store import SqliteStore

        self.tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
        self.tmp.close()
        settings = Settings(api_token="lab-token")
        app = create_control_app(store=SqliteStore(self.tmp.name), token="lab-token", settings=settings)
        self.client = TestClient(app)
        self.headers = {"Authorization": "Bearer lab-token"}

    def test_providers_and_event_post_require_auth(self) -> None:
        self.assertEqual(self.client.get("/v1/security/providers").status_code, 401)
        listed = self.client.get("/v1/security/providers", headers=self.headers)
        self.assertEqual(listed.status_code, 200)
        kinds = {row["kind"] for row in listed.json()["providers"]}
        self.assertEqual(kinds, {"antares", "defenseclaw", "vise"})
        body = _event().to_dict()
        saved = self.client.post("/v1/security/events", headers=self.headers, json=body)
        self.assertEqual(saved.status_code, 200)
        self.assertEqual(saved.json()["run_id"], "run-1")
        refused = self.client.post(
            "/v1/security/events",
            headers=self.headers,
            json={**body, "details": {"sample": "MZ"}},
        )
        self.assertEqual(refused.status_code, 400)
        mcp = self.client.get("/v1/security/mcp", headers=self.headers)
        self.assertEqual(mcp.status_code, 200)
        self.assertEqual(mcp.json()["policy"], "deny-unlisted")
        self.assertEqual(mcp.json()["servers"], [])


if __name__ == "__main__":
    unittest.main()
