"""Security VM template contract tests for Cybersecurity Vise (IWO-073).

Acceptance criteria:
1. Template manifest validates offline.
2. Missing required tool/snapshot fails preflight.
3. Version drift is reported.
4. Windows/Linux profiles exist.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.security.hypervisor import FakeHypervisor, IsolationError
from ai_lab_platform.security.templates import (
    BASELINE_PROFILES,
    LINUX_BASELINE_PROFILE,
    WINDOWS_BASELINE_PROFILE,
    TemplateManifest,
    TemplateValidationReport,
    check_template_drift,
    load_manifest_file,
    validate_manifest_offline,
)
from ai_lab_platform.security.vise import ViseStore, ViseTransitionError

SHA = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"


class TemplateContractTests(unittest.TestCase):
    def test_windows_and_linux_baseline_profiles_exist(self) -> None:
        """AC 4: Windows and Linux baseline profiles exist."""
        # 1. Profiles in Python registry
        self.assertIn("fixture-linux", BASELINE_PROFILES)
        self.assertIn("fixture-windows", BASELINE_PROFILES)
        self.assertEqual(LINUX_BASELINE_PROFILE.os_type, "linux")
        self.assertEqual(WINDOWS_BASELINE_PROFILE.os_type, "windows")

        # 2. JSON manifests in repository
        templates_dir = ROOT / "infrastructure" / "security" / "templates"
        linux_json = templates_dir / "linux-baseline.json"
        windows_json = templates_dir / "windows-baseline.json"
        self.assertTrue(linux_json.is_file(), f"missing {linux_json}")
        self.assertTrue(windows_json.is_file(), f"missing {windows_json}")

        linux_loaded = load_manifest_file(linux_json)
        windows_loaded = load_manifest_file(windows_json)
        self.assertEqual(linux_loaded.template_id, "fixture-linux")
        self.assertEqual(windows_loaded.template_id, "fixture-windows")
        self.assertTrue(linux_loaded.immutable)
        self.assertTrue(windows_loaded.immutable)
        self.assertEqual(linux_loaded.network_policy, "isolated")
        self.assertEqual(windows_loaded.network_policy, "isolated")

    def test_template_manifest_validates_offline(self) -> None:
        """AC 1: Template manifest validates offline without network or hypervisor."""
        valid_raw = {
            "template_id": "test-sec-linux",
            "os_type": "linux",
            "os_version": "debian-12",
            "version": "1.0.0",
            "expected_snapshot": "clean-baseline",
            "tools": ["wireshark", "tcpdump"],
            "sensors": ["auditd"],
            "network_policy": "isolated",
            "guest_agent_ready": True,
            "disposable_credentials_policy": "ephemeral-per-job",
            "immutable": True,
        }
        report = validate_manifest_offline(valid_raw)
        self.assertTrue(report.valid)
        self.assertEqual(len(report.errors), 0)

        # Missing required field
        bad_raw = dict(valid_raw)
        del bad_raw["expected_snapshot"]
        report_bad = validate_manifest_offline(bad_raw)
        self.assertFalse(report_bad.valid)
        self.assertTrue(any("expected_snapshot" in err for err in report_bad.errors))

        # Secret rejection
        secret_raw = dict(valid_raw)
        secret_raw["root_password"] = "hunter2"
        report_secret = validate_manifest_offline(secret_raw)
        self.assertFalse(report_secret.valid)
        self.assertTrue(any("Secret-like" in err for err in report_secret.errors))

        # Mutable golden image rejection
        mutable_raw = dict(valid_raw)
        mutable_raw["immutable"] = False
        report_mutable = validate_manifest_offline(mutable_raw)
        self.assertFalse(report_mutable.valid)
        self.assertTrue(any("immutable must be True" in err for err in report_mutable.errors))

        # Non-isolated network policy rejection
        net_raw = dict(valid_raw)
        net_raw["network_policy"] = "bridged-lan"
        report_net = validate_manifest_offline(net_raw)
        self.assertFalse(report_net.valid)
        self.assertTrue(any("network_policy must be 'isolated'" in err for err in report_net.errors))

    def test_missing_required_tool_fails_preflight(self) -> None:
        """AC 2: Missing required tool fails preflight and cannot become ready."""
        fake = FakeHypervisor()
        # Set template without 'tcpdump'
        fake.set_template_metadata(
            "fixture-linux",
            {
                "template_id": "fixture-linux",
                "os_type": "linux",
                "version": "1.0.0",
                "snapshot": "clean-baseline",
                "tools": ["wireshark"],  # missing tcpdump
                "sensors": ["auditd"],
                "guest_agent_ready": True,
                "immutable": True,
            },
        )
        store = ViseStore({"fake": fake})

        # Job explicitly requiring tcpdump
        job = store.create(
            {
                "sha256": SHA,
                "profile": "linux-static",
                "provider": "fake",
                "template_id": "fixture-linux",
                "required_tools": ["tcpdump"],
            }
        )
        failed = store.advance(job.job_id, "preflight", actor="security")
        self.assertEqual(failed.state, "failed")
        self.assertIn("missing required tool: tcpdump", failed.failure)

        # Transition to ready must fail
        with self.assertRaises(ViseTransitionError):
            store.advance(job.job_id, "ready", actor="security")

    def test_missing_required_snapshot_fails_preflight(self) -> None:
        """AC 2: Missing or mismatched snapshot fails preflight."""
        fake = FakeHypervisor()
        # Set template snapshot to 'dirty-state' instead of 'clean-baseline'
        fake.set_template_metadata(
            "fixture-linux",
            {
                "template_id": "fixture-linux",
                "os_type": "linux",
                "version": "1.0.0",
                "snapshot": "dirty-state",
                "tools": ["wireshark", "tcpdump"],
                "sensors": ["auditd"],
                "guest_agent_ready": True,
                "immutable": True,
            },
        )
        store = ViseStore({"fake": fake})

        job = store.create(
            {
                "sha256": SHA,
                "profile": "linux-static",
                "provider": "fake",
                "template_id": "fixture-linux",
                "expected_snapshot": "clean-baseline",
            }
        )
        failed = store.advance(job.job_id, "preflight", actor="security")
        self.assertEqual(failed.state, "failed")
        self.assertIn("expected snapshot 'clean-baseline', found 'dirty-state'", failed.failure)

        with self.assertRaises(ViseTransitionError):
            store.advance(job.job_id, "ready", actor="security")

    def test_version_drift_is_reported(self) -> None:
        """AC 3: Version drift is reported in isolation metadata and helper."""
        fake = FakeHypervisor()
        # Manifest expects version 1.0.0, but template has drifted to 0.9.0
        fake.set_template_metadata(
            "fixture-linux",
            {
                "template_id": "fixture-linux",
                "os_type": "linux",
                "version": "0.9.0",
                "snapshot": "clean-baseline",
                "tools": ["wireshark", "tcpdump", "auditd", "yara", "strace", "gdb"],
                "sensors": ["auditd", "osquery"],
                "guest_agent_ready": True,
                "immutable": True,
            },
        )
        store = ViseStore({"fake": fake})

        job = store.create(
            {
                "sha256": SHA,
                "profile": "linux-static",
                "provider": "fake",
                "template_id": "fixture-linux",
            }
        )
        passed = store.advance(job.job_id, "preflight", actor="security")
        self.assertEqual(passed.state, "preflight")

        # Isolation template metadata records version drift
        tmpl_report = passed.isolation["template"]
        self.assertTrue(tmpl_report["version_drift"])
        self.assertEqual(tmpl_report["drift_details"]["manifest_version"], "1.0.0")
        self.assertEqual(tmpl_report["drift_details"]["template_version"], "0.9.0")

        # Offline helper check
        drift, details = check_template_drift(LINUX_BASELINE_PROFILE, "0.9.0")
        self.assertTrue(drift)
        self.assertEqual(details["template_version"], "0.9.0")

        no_drift, _ = check_template_drift(LINUX_BASELINE_PROFILE, "1.0.0")
        self.assertFalse(no_drift)

    def test_control_app_templates_endpoints(self) -> None:
        """Test GET and POST /v1/security/templates routes in control_app."""
        from fastapi.testclient import TestClient
        from ai_lab_platform.control_app import create_control_app
        from ai_lab_platform.settings import Settings
        from ai_lab_platform.store import SqliteStore

        tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
        tmp.close()
        app = create_control_app(
            store=SqliteStore(tmp.name),
            token="lab-token",
            settings=Settings(api_token="lab-token"),
        )
        client = TestClient(app)
        headers = {"Authorization": "Bearer lab-token"}

        # Unauthorized
        self.assertEqual(client.get("/v1/security/templates").status_code, 401)

        # List templates
        resp = client.get("/v1/security/templates", headers=headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("templates", data)
        self.assertTrue(len(data["templates"]) >= 2)

        # Validate template endpoint
        val_resp = client.post(
            "/v1/security/templates/validate",
            json=LINUX_BASELINE_PROFILE.to_dict(),
            headers=headers,
        )
        self.assertEqual(val_resp.status_code, 200)
        val_data = val_resp.json()
        self.assertTrue(val_data["valid"])
        self.assertFalse(val_data["version_drift"])


if __name__ == "__main__":
    unittest.main()
