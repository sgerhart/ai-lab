"""Isolated network contract tests for Cybersecurity Vise (IWO-072).

Acceptance criteria:
1. Job cannot become ready if network validation fails.
2. Trusted network identifiers can be denylisted.
3. Controlled egress defaults false.
4. Validation result is recorded as evidence.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.security.hypervisor import (
    DEFAULT_TRUSTED_NETWORK_DENYLIST,
    FakeHypervisor,
    IsolatedNetworkSpec,
    IsolationError,
)
from ai_lab_platform.security.vise import ViseStore, ViseTransitionError

SHA = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"


class IsolatedNetworkContractTests(unittest.TestCase):
    def test_default_denylist_and_spec_structure(self) -> None:
        self.assertIn("tailscale", DEFAULT_TRUSTED_NETWORK_DENYLIST)
        self.assertIn("lan", DEFAULT_TRUSTED_NETWORK_DENYLIST)
        self.assertIn("trusted", DEFAULT_TRUSTED_NETWORK_DENYLIST)
        spec = IsolatedNetworkSpec(network_id="vmbr99")
        self.assertEqual(spec.network_id, "vmbr99")
        self.assertEqual(spec.nic_count, 1)
        self.assertFalse(spec.uplink)
        self.assertFalse(spec.controlled_egress)
        self.assertEqual(spec.gateway_policy, "isolated")

    def test_job_cannot_become_ready_if_network_validation_fails(self) -> None:
        """AC 1: Job cannot become ready if network validation fails."""
        fake = FakeHypervisor()
        store = ViseStore({"fake": fake})
        # Create job targeting a non-existent network
        job = store.create(
            {
                "sha256": SHA,
                "profile": "linux-static",
                "provider": "fake",
                "template_id": "fixture-linux",
                "network_id": "unknown-net",
            }
        )
        failed = store.advance(job.job_id, "preflight", actor="security")
        self.assertEqual(failed.state, "failed")
        self.assertIn("not known to provider", failed.failure)

        # Attempting to move to ready from failed raises ViseTransitionError
        with self.assertRaises(ViseTransitionError):
            store.advance(job.job_id, "ready", actor="security")

    def test_trusted_network_identifiers_denylisted(self) -> None:
        """AC 2: Trusted network identifiers can be denylisted."""
        fake = FakeHypervisor()
        # Add a network that contains a trusted name
        fake.add_network("tailscale-bridge", nic_count=1, uplink=False, controlled_egress=False)
        store = ViseStore({"fake": fake})

        job = store.create(
            {
                "sha256": SHA,
                "profile": "linux-static",
                "provider": "fake",
                "template_id": "fixture-linux",
                "network_id": "tailscale-bridge",
            }
        )
        failed = store.advance(job.job_id, "preflight", actor="security")
        self.assertEqual(failed.state, "failed")
        self.assertIn("denylisted as trusted", failed.failure)

        # Also test custom denylist on job
        fake.add_network("custom-private-net", nic_count=1, uplink=False, controlled_egress=False)
        custom_job = store.create(
            {
                "sha256": SHA,
                "profile": "linux-static",
                "provider": "fake",
                "template_id": "fixture-linux",
                "network_id": "custom-private-net",
                "network_denylist": ["custom-private"],
            }
        )
        custom_failed = store.advance(custom_job.job_id, "preflight", actor="security")
        self.assertEqual(custom_failed.state, "failed")
        self.assertIn("denylisted as trusted (custom-private)", custom_failed.failure)

    def test_controlled_egress_defaults_to_false(self) -> None:
        """AC 3: Controlled egress defaults false."""
        fake = FakeHypervisor()
        fake.add_network("egress-net", nic_count=1, uplink=False, controlled_egress=True)
        store = ViseStore({"fake": fake})

        # By default, controlled_egress is false on the job
        job_no_egress = store.create(
            {
                "sha256": SHA,
                "profile": "linux-static",
                "provider": "fake",
                "template_id": "fixture-linux",
                "network_id": "egress-net",
            }
        )
        self.assertFalse(job_no_egress.controlled_egress)
        failed = store.advance(job_no_egress.job_id, "preflight", actor="security")
        self.assertEqual(failed.state, "failed")
        self.assertIn("controlled egress defaults to false", failed.failure)

        # Explicitly allowing controlled egress succeeds
        job_with_egress = store.create(
            {
                "sha256": SHA,
                "profile": "linux-static",
                "provider": "fake",
                "template_id": "fixture-linux",
                "network_id": "egress-net",
                "controlled_egress": True,
            }
        )
        self.assertTrue(job_with_egress.controlled_egress)
        passed = store.advance(job_with_egress.job_id, "preflight", actor="security")
        self.assertEqual(passed.state, "preflight")
        ready = store.advance(job_with_egress.job_id, "ready", actor="security")
        self.assertEqual(ready.state, "ready")

    def test_validation_result_is_recorded_as_evidence(self) -> None:
        """AC 4: Validation result is recorded as evidence."""
        fake = FakeHypervisor()
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

        # Isolation dictionary contains template, network, and validation evidence
        isolation = passed.isolation
        self.assertIn("network", isolation)
        self.assertIn("evidence", isolation)
        evidence = isolation["evidence"]
        self.assertTrue(evidence["locator"].startswith(f"quarantine://evidence/isolation/{job.job_id}"))
        self.assertEqual(len(evidence["sha256"]), 64)
        self.assertEqual(evidence["media_type"], "application/json")
        self.assertGreater(evidence["byte_length"], 0)

        # Ready state validates that evidence is present
        ready = store.advance(job.job_id, "ready", actor="security")
        self.assertEqual(ready.state, "ready")

    def test_multi_nic_and_uplink_violations_fail_closed(self) -> None:
        fake = FakeHypervisor()
        fake.add_network("multi-nic-net", nic_count=2, uplink=False)
        fake.add_network("uplink-net", nic_count=1, uplink=True)
        store = ViseStore({"fake": fake})

        job1 = store.create(
            {
                "sha256": SHA,
                "profile": "linux-static",
                "provider": "fake",
                "template_id": "fixture-linux",
                "network_id": "multi-nic-net",
            }
        )
        failed1 = store.advance(job1.job_id, "preflight", actor="security")
        self.assertEqual(failed1.state, "failed")
        self.assertIn("requires exactly 1 NIC", failed1.failure)

        job2 = store.create(
            {
                "sha256": SHA,
                "profile": "linux-static",
                "provider": "fake",
                "template_id": "fixture-linux",
                "network_id": "uplink-net",
            }
        )
        failed2 = store.advance(job2.job_id, "preflight", actor="security")
        self.assertEqual(failed2.state, "failed")
        self.assertIn("active uplink to trusted network", failed2.failure)


if __name__ == "__main__":
    unittest.main()
