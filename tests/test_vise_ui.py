"""Unit and contract tests for Cybersecurity Vise Operator UI (IWO-075).

Validates all 4 Acceptance Criteria:
1. UI exposes preflight and cleanup proof.
2. Start-execution action is disabled until approval/isolation are satisfied.
3. Evidence is viewable without direct guest trust (safe LLM brief & quarantine:// references).
4. Provider errors are explicit (ProviderNotConfigured, IsolationError fail-closed).
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
from ai_lab_platform.settings import Settings
from ai_lab_platform.store import SqliteStore


class ViseOperatorUITests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
        self.tmp.close()
        self.store = SqliteStore(self.tmp.name)
        self.settings = Settings(
            api_token="vise-ui-test-token",
        )
        self.app = create_control_app(
            store=self.store,
            token="vise-ui-test-token",
            settings=self.settings,
        )
        self.client = TestClient(self.app)
        self.headers = {"Authorization": "Bearer vise-ui-test-token"}
        self.safe_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    def tearDown(self) -> None:
        Path(self.tmp.name).unlink(missing_ok=True)

    def test_ac1_preflight_and_cleanup_proof_lifecycle(self) -> None:
        """AC 1: UI exposes preflight proof (manifest & isolated network) and cleanup proof (residual guest check)."""
        create_resp = self.client.post(
            "/v1/security/vise/jobs",
            headers=self.headers,
            json={
                "sha256": self.safe_hash,
                "label": "benign-diagnostic-probe.bin",
                "byte_length": 16384,
                "profile": "linux-static",
                "provider": "fake",
                "template_id": "fixture-linux",
                "execution_class": "benign",
            },
        )
        self.assertEqual(create_resp.status_code, 200)
        job = create_resp.json()
        job_id = job["job_id"]
        self.assertEqual(job["state"], "submitted")

        # 1. Preflight proof generation
        pf_resp = self.client.post(
            f"/v1/security/vise/jobs/{job_id}/advance",
            headers=self.headers,
            json={"state": "preflight", "actor": "operator"},
        )
        self.assertEqual(pf_resp.status_code, 200)
        pf_job = pf_resp.json()
        self.assertEqual(pf_job["state"], "preflight")
        iso = pf_job.get("isolation") or {}
        self.assertTrue(iso.get("template", {}).get("ok"))
        self.assertTrue(iso.get("network", {}).get("ok"))
        self.assertTrue(iso.get("network", {}).get("denylist_cleared"))
        self.assertTrue(iso.get("evidence", {}).get("locator", "").startswith("quarantine://evidence/isolation/"))

        # 2. Advance to ready
        ready_resp = self.client.post(
            f"/v1/security/vise/jobs/{job_id}/advance",
            headers=self.headers,
            json={"state": "ready", "actor": "operator"},
        )
        self.assertEqual(ready_resp.status_code, 200)

        # 3. Advance to running
        run_resp = self.client.post(
            f"/v1/security/vise/jobs/{job_id}/advance",
            headers=self.headers,
            json={"state": "running", "actor": "operator"},
        )
        self.assertEqual(run_resp.status_code, 200)
        run_job = run_resp.json()
        self.assertEqual(run_job["state"], "running")
        self.assertTrue(run_job["vm_id"])

        # 4. Advance to collecting (automatically generates normalized evidence via pipeline)
        col_resp = self.client.post(
            f"/v1/security/vise/jobs/{job_id}/advance",
            headers=self.headers,
            json={"state": "collecting", "actor": "operator"},
        )
        self.assertEqual(col_resp.status_code, 200)
        col_job = col_resp.json()
        self.assertEqual(col_job["state"], "collecting")
        self.assertGreater(len(col_job["evidence"]), 0)

        # 5. Cleanup proof verification (destroys VM and confirms 0 residual guests)
        cl_resp = self.client.post(
            f"/v1/security/vise/jobs/{job_id}/advance",
            headers=self.headers,
            json={"state": "cleanup", "actor": "operator"},
        )
        self.assertEqual(cl_resp.status_code, 200)
        cl_job = cl_resp.json()
        self.assertEqual(cl_job["cleanup_status"], "verified")
        self.assertEqual(cl_job["vm_id"], "")

        # 6. Complete transition succeeds only after verified cleanup
        comp_resp = self.client.post(
            f"/v1/security/vise/jobs/{job_id}/advance",
            headers=self.headers,
            json={"state": "complete", "actor": "operator"},
        )
        self.assertEqual(comp_resp.status_code, 200)
        self.assertEqual(comp_resp.json()["state"], "complete")

    def test_ac2_start_execution_disabled_until_approval_and_isolation_satisfied(self) -> None:
        """AC 2: Start-execution is blocked/disabled until preflight isolation passes and approval is present for untrusted."""
        create_resp = self.client.post(
            "/v1/security/vise/jobs",
            headers=self.headers,
            json={
                "sha256": self.safe_hash,
                "label": "untrusted-malware-test.bin",
                "byte_length": 32768,
                "profile": "linux-behavioral",  # Enforces untrusted
                "provider": "fake",
                "template_id": "fixture-linux",
                "execution_class": "untrusted",
            },
        )
        job_id = create_resp.json()["job_id"]

        # Attempt to jump straight to running fails (409)
        bad_run = self.client.post(
            f"/v1/security/vise/jobs/{job_id}/advance",
            headers=self.headers,
            json={"state": "running", "actor": "operator"},
        )
        self.assertEqual(bad_run.status_code, 409)

        # Preflight and Ready
        self.client.post(f"/v1/security/vise/jobs/{job_id}/advance", headers=self.headers, json={"state": "preflight", "actor": "operator"})
        self.client.post(f"/v1/security/vise/jobs/{job_id}/advance", headers=self.headers, json={"state": "ready", "actor": "operator"})

        # Running without approval for untrusted fails (409)
        unapproved_run = self.client.post(
            f"/v1/security/vise/jobs/{job_id}/advance",
            headers=self.headers,
            json={"state": "running", "actor": "operator"},
        )
        self.assertEqual(unapproved_run.status_code, 409)

        # Running WITH approval ID succeeds
        approved_run = self.client.post(
            f"/v1/security/vise/jobs/{job_id}/advance",
            headers=self.headers,
            json={"state": "running", "actor": "operator", "approval_id": "appr-sec-999"},
        )
        self.assertEqual(approved_run.status_code, 200)
        self.assertEqual(approved_run.json()["state"], "running")
        self.assertEqual(approved_run.json()["approval_id"], "appr-sec-999")

    def test_ac3_evidence_and_safe_brief_viewable_without_guest_trust(self) -> None:
        """AC 3: Evidence is viewable via quarantine references and safe LLM brief without guest trust or binary leaks."""
        create_resp = self.client.post(
            "/v1/security/vise/jobs",
            headers=self.headers,
            json={
                "sha256": self.safe_hash,
                "label": "payload-sample-c.bin",
                "byte_length": 1024,
                "profile": "linux-static",
                "provider": "fake",
                "template_id": "fixture-linux",
                "execution_class": "benign",
            },
        )
        job_id = create_resp.json()["job_id"]

        # Run through preflight, ready, running, collecting
        self.client.post(f"/v1/security/vise/jobs/{job_id}/advance", headers=self.headers, json={"state": "preflight", "actor": "operator"})
        self.client.post(f"/v1/security/vise/jobs/{job_id}/advance", headers=self.headers, json={"state": "ready", "actor": "operator"})
        self.client.post(f"/v1/security/vise/jobs/{job_id}/advance", headers=self.headers, json={"state": "running", "actor": "operator"})
        self.client.post(f"/v1/security/vise/jobs/{job_id}/advance", headers=self.headers, json={"state": "collecting", "actor": "operator"})

        # Fetch safe LLM brief
        brief_resp = self.client.get(
            f"/v1/security/vise/jobs/{job_id}/brief",
            headers=self.headers,
        )
        self.assertEqual(brief_resp.status_code, 200)
        data = brief_resp.json()

        self.assertEqual(data["job_id"], job_id)
        self.assertEqual(data["sha256"], self.safe_hash)
        self.assertIn("llm_summary", data)
        self.assertIn("quarantine_manifest", data)
        self.assertTrue(data["digest_sha256"])

        summary = data["llm_summary"]
        self.assertIn("# Cybersecurity Vise Analysis Dossier", summary)
        self.assertIn("quarantine://", summary)
        self.assertIn("Residual Risk & Containment Invariant", summary)

        # Verify no binary or raw sample fields
        for forbidden in ("MZ", "\\x90", "raw_bytes", "malware_bytes"):
            self.assertNotIn(forbidden, summary)

    def test_ac4_explicit_provider_and_isolation_errors(self) -> None:
        """AC 4: Provider errors (e.g. unconfigured Proxmox/ESXi) fail closed and produce explicit failure reports."""
        create_resp = self.client.post(
            "/v1/security/vise/jobs",
            headers=self.headers,
            json={
                "sha256": self.safe_hash,
                "label": "proxmox-target-probe.bin",
                "byte_length": 2048,
                "profile": "linux-static",
                "provider": "proxmox",  # Unconfigured provider per ADR 0043
                "template_id": "fixture-linux",
                "execution_class": "benign",
            },
        )
        self.assertEqual(create_resp.status_code, 200)
        job_id = create_resp.json()["job_id"]

        # Advance to preflight triggers ProviderNotConfigured
        pf_resp = self.client.post(
            f"/v1/security/vise/jobs/{job_id}/advance",
            headers=self.headers,
            json={"state": "preflight", "actor": "operator"},
        )
        self.assertEqual(pf_resp.status_code, 200)
        job = pf_resp.json()
        self.assertEqual(job["state"], "failed")
        self.assertIn("has no management endpoint", job["failure"])

        # Embedded payload rejection check (400)
        payload_attempt = self.client.post(
            "/v1/security/vise/jobs",
            headers=self.headers,
            json={
                "sha256": self.safe_hash,
                "payload": "forbidden-embedded-bytes",
            },
        )
        self.assertEqual(payload_attempt.status_code, 400)

    def test_web_ui_structure_and_styling(self) -> None:
        """Verifies that agents.html and studio.css contain the required Vise UI components."""
        html_path = ROOT / "platform" / "src" / "ai_lab_platform" / "web" / "agents.html"
        self.assertTrue(html_path.is_file())
        html = html_path.read_text(encoding="utf-8")

        self.assertIn('id="sec-tab-vise"', html)
        self.assertIn('id="vise-intake-card"', html)
        self.assertIn('id="sec-vise-jobs-slot"', html)
        self.assertIn('id="sec-vise-detail-slot"', html)
        self.assertIn('id="sec-vise-brief-dialog"', html)
        self.assertIn('function renderSecurityVise', html)
        self.assertIn('function renderViseDetail', html)
        self.assertIn('function openViseBriefDialog', html)

        css_path = ROOT / "platform" / "src" / "ai_lab_platform" / "web" / "static" / "studio.css"
        self.assertTrue(css_path.is_file())
        css = css_path.read_text(encoding="utf-8")

        self.assertIn('.vise-timeline', css)
        self.assertIn('.vise-proof-grid', css)
        self.assertIn('.vise-proof-card', css)
        self.assertIn('.vise-detail-card', css)
        self.assertIn('.vise-brief-box', css)


if __name__ == "__main__":
    unittest.main()
