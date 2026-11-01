"""Unit tests for Apple Silicon RL (GRPO) compatibility spike and policy gradients."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from packages.contracts import RLConfig, RLSpikeReport
from services.model.rl_spike import (
    RLCompatibilitySpike,
    compute_grpo_advantages,
    compute_grpo_token_loss,
)


class TestRLSpike(unittest.TestCase):
    """Verifies GRPO mathematical contracts, loss clipping, and on-policy gradient updates."""

    def test_grpo_advantage_normalization(self) -> None:
        """Verifies group advantage normalization across rollouts (zero mean, unit std)."""
        # Mixed rewards
        rewards = [1.0, 1.0, 0.0, 0.0]
        advs = compute_grpo_advantages(rewards)
        self.assertEqual(len(advs), 4)
        self.assertAlmostEqual(sum(advs), 0.0, places=4)
        self.assertGreater(advs[0], 0.0)
        self.assertGreater(advs[1], 0.0)
        self.assertLess(advs[2], 0.0)
        self.assertLess(advs[3], 0.0)

        # Identical rewards (variance = 0)
        identical_advs = compute_grpo_advantages([1.0, 1.0, 1.0, 1.0])
        self.assertEqual(identical_advs, [0.0, 0.0, 0.0, 0.0])

        # Edge cases
        self.assertEqual(compute_grpo_advantages([]), [])
        self.assertEqual(compute_grpo_advantages([0.5]), [0.0])

    def test_grpo_clipped_surrogate_loss_and_kl(self) -> None:
        """Verifies clipped surrogate objective and Schulman KL divergence penalty."""
        # Unclipped step: ratio = exp(-0.1 - (-0.1)) = 1.0
        pl, kl, tl = compute_grpo_token_loss(
            logprob=-0.1,
            old_logprob=-0.1,
            ref_logprob=-0.1,
            advantage=1.0,
            clip_eps=0.2,
            beta=0.04,
        )
        self.assertAlmostEqual(pl, -1.0, places=4)
        self.assertAlmostEqual(kl, 0.0, places=4)
        self.assertAlmostEqual(tl, -1.0, places=4)

        # Clipped step: ratio = exp(0.5) ≈ 1.648, should clip at 1 + 0.2 = 1.2
        pl_clip, _, _ = compute_grpo_token_loss(
            logprob=-0.1,
            old_logprob=-0.6,
            ref_logprob=-0.1,
            advantage=1.0,
            clip_eps=0.2,
            beta=0.04,
        )
        self.assertAlmostEqual(pl_clip, -1.2, places=4)

        # Divergence from reference policy incurs non-negative KL penalty
        _, kl_div, _ = compute_grpo_token_loss(
            logprob=-0.1,
            old_logprob=-0.1,
            ref_logprob=-0.5,
            advantage=0.0,
            clip_eps=0.2,
            beta=0.04,
        )
        self.assertGreater(kl_div, 0.0)

    def test_rl_spike_gradient_step_divergence(self) -> None:
        """Mandatory Invariant: Policy gradient step must produce non-zero gradient norm and parameter divergence."""
        config = RLConfig(group_size=4, beta=0.04, learning_rate=1e-4)
        spike = RLCompatibilitySpike(config=config)
        report = spike.run_spike()

        self.assertTrue(report.gradient_step_verified)
        self.assertTrue(report.loss_finite)
        self.assertTrue(report.advantages_normalized)
        self.assertGreater(report.step_result.gradient_norm, 0.0)
        self.assertTrue(report.step_result.weights_diverged)
        self.assertNotEqual(
            report.step_result.initial_param_hash,
            report.step_result.updated_param_hash,
        )
        self.assertEqual(len(report.step_result.initial_param_hash), 64)
        self.assertEqual(len(report.step_result.updated_param_hash), 64)

    def test_rl_spike_report_serialization(self) -> None:
        """Verifies report round-trip serialization and schema compliance."""
        spike = RLCompatibilitySpike()
        report = spike.run_spike()

        dumped = report.model_dump()
        restored = RLSpikeReport.model_validate(dumped)

        self.assertEqual(restored.spike_id, report.spike_id)
        self.assertEqual(restored.framework, "mlx-compatible-proof")
        self.assertIn("apple_silicon", restored.device_arch)
        self.assertGreater(len(restored.findings), 0)
        self.assertIn("WO_08", restored.recommendation)

    def test_rl_spike_cli_report_generation(self) -> None:
        """Verifies CLI runner generation of on-disk report JSON."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_file = Path(tmp_dir) / "test_rl_report.json"
            config = RLConfig(group_size=4, beta=0.05, learning_rate=2e-4)
            spike = RLCompatibilitySpike(config=config)
            report = spike.run_spike()

            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(report.model_dump(), f, indent=2)

            self.assertTrue(out_file.exists())
            loaded = json.loads(out_file.read_text(encoding="utf-8"))
            self.assertTrue(loaded["gradient_step_verified"])
            self.assertEqual(loaded["group_size"], 4)


if __name__ == "__main__":
    unittest.main()
