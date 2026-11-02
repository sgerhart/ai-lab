"""Tests for Hypervisor test harness and benign validation workflow (IWO-078).

Validates all 5 Acceptance Criteria:
1. CI runs entirely with fake provider.
2. Dry-run prints intended resource operations without creating VMs.
3. Benign validation executes clone->boot->fixture->evidence->cleanup when authorized.
4. Residual resources fail the run and trigger blocked incident state.
5. Host and network safety checks (denylist, loopback bind, live auth gates) are enforced.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.security.harness import (
    BENIGN_FILE_FIXTURE,
    BENIGN_NETWORK_FIXTURE,
    BENIGN_PROCESS_FIXTURE,
    STANDARD_BENIGN_FIXTURES,
    BenignExecutionEvidence,
    BenignFixture,
    EvidenceRecord,
    OperatorValidationReport,
    run_benign_validation_suite,
    run_dry_run_preflight,
    verify_host_and_network_safety,
    verify_provider_contract,
)
from ai_lab_platform.security.hypervisor import (
    AuthContext,
    FakeHypervisor,
    HypervisorDenied,
    IsolationError,
    ProviderNotConfigured,
    UnconfiguredHypervisor,
)
from ai_lab_platform.security.lifecycle import WorkflowStatus


class HypervisorHarnessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fake = FakeHypervisor()

    def test_ac1_ci_runs_entirely_with_fake_provider_and_contracts(self) -> None:
        """AC 1: CI runs entirely with fake provider; provider contract verified."""
        # 1. Fake provider contract verification
        fake_res = verify_provider_contract(self.fake)
        self.assertEqual(fake_res["status"], "contract_verified")
        self.assertIn("inventory_contract_valid", fake_res["checks"])
        self.assertIn("mutation_auth_gated", fake_res["checks"])
        self.assertIn("network_denylist_enforced", fake_res["checks"])
        self.assertIn("lifecycle_roundtrip_verified", fake_res["checks"])

        # 2. Live unconfigured providers (proxmox, esxi) fail closed in CI
        for name in ("proxmox", "esxi"):
            unconfigured = UnconfiguredHypervisor(name)
            unc_res = verify_provider_contract(unconfigured)
            self.assertEqual(unc_res["status"], "fail_closed_verified")
            self.assertIn("inventory_fails_closed", unc_res["checks"])
            self.assertIn("clone_fails_closed", unc_res["checks"])
            self.assertIn("power_on_fails_closed", unc_res["checks"])
            self.assertIn("destroy_fails_closed", unc_res["checks"])
            self.assertIn("residual_fails_closed", unc_res["checks"])

        # 3. Prohibited arbitrary command execution methods check
        class DangerousProvider:
            provider = "insecure"

            def shell(self, cmd: str) -> str:
                return "bad"

        with self.assertRaises(PermissionError):
            verify_provider_contract(DangerousProvider())  # type: ignore[arg-type]

    def test_ac2_dry_run_preflight_prints_operations_and_creates_no_vm(self) -> None:
        """AC 2: Dry-run / preflight mode produces planned operation trace and never creates a VM."""
        res = run_dry_run_preflight(
            template_id="fixture-linux",
            network_id="fixture-isolated",
            provider_name="fake",
            custom_provider=self.fake,
        )

        self.assertEqual(res["status"], "preflight_passed")
        self.assertFalse(res["vm_created"])
        self.assertTrue(res["safety"]["safety_ok"])
        self.assertTrue(res["template_report"]["manifest_valid"])

        # Verify all 14 lifecycle steps are planned and marked appropriately
        planned = res["planned_steps"]
        self.assertEqual(len(planned), 14)
        step_names = [s["step"] for s in planned]
        self.assertIn("inventory", step_names)
        self.assertIn("template_validate", step_names)
        self.assertIn("network_validate", step_names)
        self.assertIn("clone_request", step_names)
        self.assertIn("boot", step_names)
        self.assertIn("guest_ready", step_names)
        self.assertIn("benign_validation", step_names)
        self.assertIn("execution_approval", step_names)
        self.assertIn("analysis", step_names)
        self.assertIn("collect", step_names)
        self.assertIn("shutdown", step_names)
        self.assertIn("destroy", step_names)
        self.assertIn("residual_check", step_names)
        self.assertIn("report", step_names)

        # Mutating steps must be flagged as dry_run_skipped
        for s in planned:
            if s["mutates"]:
                self.assertTrue(s.get("dry_run_skipped"), f"{s['step']} should be dry_run_skipped")

        # Hypervisor remains completely empty (zero VMs)
        self.assertEqual(len(self.fake._guests), 0)

        # Operator report in dry-run mode
        report = res["report"]
        self.assertEqual(report["mode"], "dry_run")
        self.assertEqual(report["status"], "success")
        self.assertFalse(report["cleanup_summary"]["vm_created"])

    def test_ac3_benign_validation_executes_fixtures_and_produces_evidence_and_report(self) -> None:
        """AC 3: Full benign validation execution captures evidence and generates signed report."""
        job_id = "job-benign-e2e-01"
        res = run_benign_validation_suite(
            job_id,
            template_id="fixture-linux",
            network_id="fixture-isolated",
            provider=self.fake,
        )

        self.assertEqual(res["status"], WorkflowStatus.COMPLETED.value)
        self.assertEqual(res["cleanup_status"], "verified")
        self.assertEqual(res["residual_vms"], [])

        # Evidence checks
        evidence = res["evidence"]
        self.assertEqual(evidence["job_id"], job_id)
        self.assertEqual(evidence["record_count"], 3)
        self.assertTrue(len(evidence["digest"]) == 64)

        categories = {r["category"] for r in evidence["records"]}
        self.assertEqual(categories, {"process", "file", "network"})

        # Signed operator report check
        report = res["report"]
        self.assertEqual(report["status"], "success")
        self.assertEqual(report["mode"], "fake_ci")
        self.assertTrue(len(report["signature_sha256"]) == 64)
        self.assertEqual(report["residual_vms"], [])

        # Markdown representation formatting
        md = res["markdown_report"]
        self.assertIn("# Security VM Validation Report: job-benign-e2e-01", md)
        self.assertIn("✅ PASSED", md)
        self.assertIn("fixture-linux", md)
        self.assertIn("fixture-isolated", md)
        self.assertIn("verified", md)

        # Verify hypervisor was cleaned up cleanly
        self.assertEqual(self.fake.residual(job_id), [])

    def test_ac4_residual_resources_fail_the_run_and_trigger_blocked_state(self) -> None:
        """AC 4: Residual resources fail the run, trigger blocked incident state, and report orphan."""
        job_id = "job-leak-test-01"
        res = run_benign_validation_suite(
            job_id,
            template_id="fixture-linux",
            network_id="fixture-isolated",
            provider=self.fake,
            simulate_residual_leak=True,
        )

        self.assertEqual(res["status"], WorkflowStatus.BLOCKED.value)
        self.assertEqual(res["cleanup_status"], "failed")
        self.assertTrue(len(res["residual_vms"]) > 0)
        self.assertIn("vm-orphan-job-le", res["residual_vms"][0])

        report = res["report"]
        self.assertEqual(report["status"], "blocked")
        self.assertIn(res["residual_vms"][0], report["residual_vms"])

        md = res["markdown_report"]
        self.assertIn("BLOCKED", md)
        self.assertIn("Orphaned VMs detected", md)

    def test_ac5_host_and_network_safety_checks_enforce_isolation_and_authorization(self) -> None:
        """AC 5: Host bind and network isolation rules are enforced; live requires confirmation."""
        # 1. Non-loopback host bind rejected
        bad_bind = verify_host_and_network_safety("fixture-isolated", host_bind="0.0.0.0")
        self.assertFalse(bad_bind["safety_ok"])
        self.assertIn("not loopback", bad_bind["violations"][0])

        # 2. Denylisted networks rejected
        for bad_net in ("tailscale0", "home-lan", "corp-mgmt-bridge", "internal-vlan"):
            bad_res = verify_host_and_network_safety(bad_net)
            self.assertFalse(bad_res["safety_ok"])
            self.assertTrue(any("trusted denylist" in v for v in bad_res["violations"]))

        # 3. Live provider without authorization rejected
        live_denied = verify_host_and_network_safety("fixture-isolated", provider_name="proxmox")
        self.assertFalse(live_denied["safety_ok"])
        self.assertTrue(any("requires explicit live authorization" in v for v in live_denied["violations"]))

        # 4. Live provider with wrong confirmation token rejected
        bad_token = verify_host_and_network_safety(
            "fixture-isolated",
            provider_name="proxmox",
            live_authorized=True,
            confirmation_token="WRONG_TOKEN",
        )
        self.assertFalse(bad_token["safety_ok"])
        self.assertTrue(any("confirmation token" in v for v in bad_token["violations"]))

        # 5. Live provider with explicit authorization and correct confirmation token accepted
        good_live = verify_host_and_network_safety(
            "fixture-isolated",
            provider_name="proxmox",
            live_authorized=True,
            confirmation_token="AUTHORIZE_LIVE_BENIGN_VALIDATION",
        )
        self.assertTrue(good_live["safety_ok"])
        self.assertIn("live_provider_explicitly_authorized", good_live["checks_passed"])

    def test_custom_benign_fixtures(self) -> None:
        """Custom benign fixtures can be supplied and executed."""
        custom_fix = BenignFixture(
            fixture_id="fix-custom-01",
            name="custom_smoke_probe",
            category="process",
            description="Custom smoke probe",
            target_os="linux",
            expected_exit_code=0,
            expected_hash="custom_hash_12345",
            params={"command": "date -u"},
        )
        job_id = "job-custom-fix-01"
        res = run_benign_validation_suite(
            job_id,
            template_id="fixture-linux",
            network_id="fixture-isolated",
            provider=self.fake,
            fixtures=(custom_fix,),
        )
        self.assertEqual(res["status"], WorkflowStatus.COMPLETED.value)
        self.assertEqual(res["evidence"]["record_count"], 1)
        self.assertEqual(res["evidence"]["records"][0]["fixture_id"], "fix-custom-01")


if __name__ == "__main__":
    unittest.main()
