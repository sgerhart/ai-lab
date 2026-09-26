"""Vise jobs and the fake hypervisor. No live provider calls."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.security.events import EmbeddedPayloadRefused
from ai_lab_platform.security.hypervisor import (
    AuthContext,
    FakeHypervisor,
    HypervisorDenied,
    IsolationError,
    ProviderNotConfigured,
    UnconfiguredHypervisor,
)
from ai_lab_platform.security.vise import ViseStore, ViseTransitionError

SHA = "ab" * 32


def _job(store: ViseStore, **overrides: object) -> str:
    body: dict[str, object] = {
        "sha256": SHA,
        "byte_length": 4,
        "label": "fixture",
        "profile": "linux-static",
        "provider": "fake",
        "template_id": "fixture-linux",
        "execution_class": "benign",
    }
    body.update(overrides)
    return store.create(body).job_id  # type: ignore[arg-type]


class HypervisorContractTests(unittest.TestCase):
    def test_fake_lifecycle_and_both_provider_names(self) -> None:
        fake = FakeHypervisor()
        auth = AuthContext(job_id="job-1", actor="security")
        self.assertEqual(fake.validate_network(fake.isolated_network, auth)["nic_count"], 1)
        with self.assertRaises(IsolationError):
            fake.validate_network("home-lan", auth)
        vm_id = fake.clone("fixture-linux", auth)
        fake.power_on(vm_id, auth)
        self.assertTrue(fake.guest_ready(vm_id, auth))
        fake.power_off(vm_id, auth)
        fake.destroy(vm_id, auth)
        self.assertEqual(fake.residual("job-1"), [])
        with self.assertRaises(HypervisorDenied):
            fake.clone("fixture-linux", AuthContext(job_id="", actor=""))
        for name in ("proxmox", "esxi"):
            live = UnconfiguredHypervisor(name)
            self.assertEqual(live.provider, name)
            with self.assertRaises(ProviderNotConfigured):
                live.inventory()
            self.assertNotIn("endpoint", live.__dict__)

    def test_public_methods_have_no_arbitrary_call(self) -> None:
        banned = {"request", "shell", "ssh", "exec", "call"}
        for cls in (FakeHypervisor, UnconfiguredHypervisor):
            names = {name for name in dir(cls) if not name.startswith("_")}
            self.assertFalse(names & banned)


class ViseJobTests(unittest.TestCase):
    def test_untrusted_running_requires_approval_and_verified_cleanup(self) -> None:
        store = ViseStore()
        job_id = _job(store, profile="linux-behavioral")
        job = store.get(job_id)
        self.assertEqual(job.execution_class, "untrusted")
        self.assertEqual(job.cleanup_status, "pending")
        store.advance(job_id, "preflight", actor="security")
        store.advance(job_id, "ready", actor="security")
        with self.assertRaises(ViseTransitionError):
            store.advance(job_id, "running", actor="security")
        self.assertEqual(store.get(job_id).state, "ready")
        store.advance(job_id, "approval", actor="operator", approval_id="appr-1")
        running = store.advance(job_id, "running", actor="security", approval_id="appr-1")
        self.assertEqual(running.state, "running")
        evidence = {
            "evidence_id": "ev-1",
            "locator": "quarantine://operator-supplied/report",
            "sha256": "cd" * 32,
            "media_type": "application/json",
            "byte_length": 20,
        }
        store.advance(job_id, "collecting", actor="security", evidence=[evidence], finding="fixture hashes")
        self.assertEqual(store.get(job_id).evidence[0].to_dict()["locator"], evidence["locator"])
        store.advance(job_id, "cleanup", actor="security")
        self.assertEqual(store.get(job_id).cleanup_status, "verified")
        done = store.advance(job_id, "complete", actor="security")
        self.assertEqual(done.state, "complete")

    def test_sample_bytes_are_refused_and_live_provider_fails_closed(self) -> None:
        store = ViseStore()
        with self.assertRaises(EmbeddedPayloadRefused):
            store.create({"sha256": SHA, "sample": "abcd", "profile": "linux-static", "provider": "fake"})
        job_id = _job(store, provider="proxmox", template_id="")
        failed = store.advance(job_id, "preflight", actor="security")
        self.assertEqual(failed.state, "failed")
        self.assertIn("no management endpoint", failed.failure)

    def test_api_requires_auth_and_does_not_run_without_approval(self) -> None:
        from fastapi.testclient import TestClient
        from ai_lab_platform.control_app import create_control_app
        from ai_lab_platform.settings import Settings
        from ai_lab_platform.store import SqliteStore

        tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
        tmp.close()
        app = create_control_app(store=SqliteStore(tmp.name), token="lab-token", settings=Settings(api_token="lab-token"))
        client = TestClient(app)
        headers = {"Authorization": "Bearer lab-token"}
        self.assertEqual(client.get("/v1/security/vise/jobs").status_code, 401)
        created = client.post(
            "/v1/security/vise/jobs",
            headers=headers,
            json={
                "sha256": SHA,
                "byte_length": 4,
                "profile": "windows-static",
                "provider": "fake",
                "template_id": "fixture-windows",
                "execution_class": "untrusted",
            },
        )
        self.assertEqual(created.status_code, 200, created.text)
        body = created.json()
        job_id = body["job_id"]
        self.assertEqual(body["execution_class"], "untrusted")
        self.assertEqual(body["cleanup_status"], "pending")
        self.assertNotIn("sample", body)
        client.post(f"/v1/security/vise/jobs/{job_id}/advance", headers=headers, json={"state": "preflight", "actor": "security"})
        client.post(f"/v1/security/vise/jobs/{job_id}/advance", headers=headers, json={"state": "ready", "actor": "security"})
        blocked = client.post(
            f"/v1/security/vise/jobs/{job_id}/advance",
            headers=headers,
            json={"state": "running", "actor": "security"},
        )
        self.assertEqual(blocked.status_code, 409)
