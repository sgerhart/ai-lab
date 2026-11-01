"""Unit and contract tests for Security Center expansion (IWO-069).

Validates unified security overview aggregation, missing provider resilience,
finding & evidence correlation links, and zero-secret redaction invariants.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from starlette.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.control_app import create_control_app
from ai_lab_platform.security.events import EvidenceRef, SecurityEvent
from ai_lab_platform.settings import Settings
from ai_lab_platform.store import SqliteStore


class SecurityCenterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
        self.tmp.close()
        self.store = SqliteStore(self.tmp.name)
        self.settings = Settings(
            api_token="security-test-token",
            antares_job_url="",  # Unconfigured by default
        )
        self.app = create_control_app(
            store=self.store,
            token="security-test-token",
            settings=self.settings,
        )
        self.client = TestClient(self.app)
        self.headers = {"Authorization": "Bearer security-test-token"}

    def tearDown(self) -> None:
        Path(self.tmp.name).unlink(missing_ok=True)

    def test_security_overview_requires_authentication(self) -> None:
        """AC: Security overview endpoint must be protected by bearer token."""
        unauth = self.client.get("/v1/security/overview")
        self.assertEqual(unauth.status_code, 401)

        auth = self.client.get("/v1/security/overview", headers=self.headers)
        self.assertEqual(auth.status_code, 200)
        body = auth.json()
        self.assertTrue(body.get("ok"))

    def test_security_overview_aggregates_all_providers_resiliently(self) -> None:
        """AC 1 & 2: Aggregates provider/status data; missing providers show unavailable/stale without breaking."""
        resp = self.client.get("/v1/security/overview", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        # Check providers list
        providers = data.get("providers") or []
        provider_ids = {p["id"] for p in providers}
        self.assertIn("defenseclaw", provider_ids)
        self.assertIn("antares", provider_ids)
        self.assertIn("vise", provider_ids)
        self.assertIn("mcp", provider_ids)
        self.assertIn("hypervisor", provider_ids)

        # DefenseClaw without report shows "no-report"
        dc = next(p for p in providers if p["id"] == "defenseclaw")
        self.assertEqual(dc["status"], "no-report")
        self.assertIn("No report", dc["status_label"])

        # Antares without URL shows "not-configured" / unavailable without throwing
        antares = next(p for p in providers if p["id"] == "antares")
        self.assertEqual(antares["status"], "not-configured")
        self.assertIn("Not configured", antares["status_label"])

        # Vise shows "ready" (contract ready)
        vise = next(p for p in providers if p["id"] == "vise")
        self.assertEqual(vise["status"], "ready")

        # MCP shows "active" with deny-unlisted
        mcp = next(p for p in providers if p["id"] == "mcp")
        self.assertEqual(mcp["status"], "active")

        # Hypervisor shows "unconfigured" refusing calls per ADR 0043
        hyp = next(p for p in providers if p["id"] == "hypervisor")
        self.assertEqual(hyp["status"], "unconfigured")
        self.assertIn("Refusing calls", hyp["status_label"])

    def test_metrics_and_fleet_posture_aggregation(self) -> None:
        """Overview provides metrics, fleet tier counts, and system security policies."""
        resp = self.client.get("/v1/security/overview", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        metrics = data.get("metrics") or {}
        self.assertIn("events_total", metrics)
        self.assertIn("severity_counts", metrics)
        self.assertIn("classification_counts", metrics)
        self.assertIn("vise_jobs_total", metrics)
        self.assertIn("fleet_summary", metrics)

        fleet = metrics["fleet_summary"]
        self.assertGreaterEqual(fleet.get("total_agents", 0), 5)
        self.assertIn("tier_0_count", fleet)
        self.assertIn("tier_1_count", fleet)
        self.assertIn("tier_2_count", fleet)

        # System policies must be present with enforced: True
        policies = data.get("system_policies") or []
        self.assertGreaterEqual(len(policies), 5)
        self.assertTrue(all(p["enforced"] is True for p in policies))

    def test_findings_and_evidence_correlation_links(self) -> None:
        """AC 3: Findings/evidence link to correlated job/run IDs."""
        # Post a security event with job_id, run_id, and evidence refs
        evidence_item = {
            "evidence_id": "ev-sec-101",
            "locator": "quarantine://hypervisor/datastore/sample-01",
            "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "media_type": "application/x-executable",
            "byte_length": 4096,
        }
        event_body = {
            "schema_version": 1,
            "event_id": "evt-corr-01",
            "occurred_at": "2026-11-01T15:30:00Z",
            "provider": "vise",
            "severity": "high",
            "classification": "finding",
            "agent_id": "lab-operations",
            "resource_id": "vise-sandbox-vm-01",
            "run_id": "run-test-999",
            "job_id": "job-vise-444",
            "tool": "behavioral_trace",
            "approval_id": "apr-op-12",
            "summary": "Suspicious process spawn detected in isolated VM",
            "evidence": [evidence_item],
            "retention": "until-operator-purge",
            "details": {"action": "quarantine", "trace_id": "tr-77"},
        }
        post_resp = self.client.post("/v1/security/events", headers=self.headers, json=event_body)
        self.assertEqual(post_resp.status_code, 200)

        # Fetch security overview
        resp = self.client.get("/v1/security/overview", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        overview = resp.json()

        recent = overview.get("recent_events") or []
        matched = next((e for e in recent if e.get("event_id") == "evt-corr-01"), None)
        self.assertIsNotNone(matched)
        self.assertEqual(matched["job_id"], "job-vise-444")
        self.assertEqual(matched["run_id"], "run-test-999")
        self.assertEqual(matched["severity"], "high")
        self.assertEqual(matched["classification"], "finding")
        
        # Evidence ref is intact with safe sha256 hash and locator
        self.assertEqual(len(matched["evidence"]), 1)
        ev = matched["evidence"][0]
        self.assertEqual(ev["evidence_id"], "ev-sec-101")
        self.assertEqual(ev["sha256"], "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
        self.assertEqual(ev["byte_length"], 4096)

    def test_no_secret_values_rendered_or_accepted(self) -> None:
        """AC 4: No secret values rendered. Passwords, tokens, and raw payloads are scrubbed."""
        secret_event = {
            "schema_version": 1,
            "event_id": "evt-leak-attempt",
            "occurred_at": "2026-11-01T15:35:00Z",
            "provider": "platform",
            "severity": "medium",
            "classification": "policy",
            "agent_id": "coding-assistant",
            "resource_id": "vault",
            "run_id": "run-sec-02",
            "job_id": "",
            "tool": "check_keys",
            "approval_id": "",
            "summary": "Key policy check",
            "evidence": [],
            "retention": "until-operator-purge",
            "details": {
                "token": "secret-token-value-12345",
                "api_key": "openai-sk-live-should-redact",
                "safe_note": "inspection completed",
            },
        }
        post_resp = self.client.post("/v1/security/events", headers=self.headers, json=secret_event)
        self.assertEqual(post_resp.status_code, 200)

        # Retrieve overview and inspect details
        resp = self.client.get("/v1/security/overview", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        overview = resp.json()

        recent = overview.get("recent_events") or []
        matched = next((e for e in recent if e.get("event_id") == "evt-leak-attempt"), None)
        self.assertIsNotNone(matched)
        details = matched["details"]
        self.assertEqual(details.get("token"), "[redacted]")
        self.assertEqual(details.get("api_key"), "[redacted]")
        self.assertEqual(details.get("safe_note"), "inspection completed")

        # Verify that raw malware payload fields are strictly refused (400)
        payload_attempt = {
            "schema_version": 1,
            "event_id": "evt-malware-raw",
            "occurred_at": "2026-11-01T15:36:00Z",
            "provider": "vise",
            "severity": "critical",
            "classification": "finding",
            "agent_id": "lab-operations",
            "resource_id": "quarantine",
            "run_id": "",
            "job_id": "job-1",
            "tool": "ingest",
            "approval_id": "",
            "summary": "Raw payload test",
            "evidence": [],
            "retention": "until-operator-purge",
            "details": {"payload": "MZ\\x90\\x00\\x03"},
        }
        refused = self.client.post("/v1/security/events", headers=self.headers, json=payload_attempt)
        self.assertEqual(refused.status_code, 400)


if __name__ == "__main__":
    unittest.main()
