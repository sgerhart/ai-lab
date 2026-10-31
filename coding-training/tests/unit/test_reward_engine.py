"""Unit tests for the deterministic reward engine."""

from __future__ import annotations

import unittest

from packages.contracts import (
    ExecutionResult,
    ExecutionStatus,
    FailureClass,
)
from services.rewards import RewardEngine


class TestRewardEngine(unittest.TestCase):
    """Verifies reward scoring calculations and invariant enforcement."""

    def setUp(self) -> None:
        self.engine = RewardEngine(version="reward-v1")
        self.dummy_hash = "f" * 64

    def test_full_pass_reward(self) -> None:
        res = ExecutionResult(
            job_id="job-101",
            task_id="py-sum-001",
            candidate_sha256=self.dummy_hash,
            test_bundle_sha256=self.dummy_hash,
            status=ExecutionStatus.COMPLETED,
            passed=10,
            total=10,
            elapsed_ms=50,
            exit_code=0,
            worker_id="w1",
        )
        scored = self.engine.score(res)
        self.assertTrue(scored.is_scorable)
        self.assertEqual(scored.reward, 1.0)
        self.assertEqual(scored.failure_class, FailureClass.NONE)
        self.assertEqual(scored.scoring_version, "reward-v1")

    def test_partial_pass_reward(self) -> None:
        res = ExecutionResult(
            job_id="job-102",
            task_id="py-sum-001",
            candidate_sha256=self.dummy_hash,
            test_bundle_sha256=self.dummy_hash,
            status=ExecutionStatus.COMPLETED,
            passed=7,
            total=10,
            elapsed_ms=55,
            exit_code=0,
            worker_id="w1",
        )
        scored = self.engine.score(res)
        self.assertTrue(scored.is_scorable)
        self.assertAlmostEqual(scored.reward, 0.7)
        self.assertEqual(scored.failure_class, FailureClass.ASSERTION_FAILED)

    def test_compile_error_reward_is_zero(self) -> None:
        res = ExecutionResult(
            job_id="job-103",
            task_id="py-sum-001",
            candidate_sha256=self.dummy_hash,
            test_bundle_sha256=self.dummy_hash,
            status=ExecutionStatus.COMPILE_ERROR,
            passed=0,
            total=10,
            elapsed_ms=5,
            exit_code=1,
            worker_id="w1",
            failure_class=FailureClass.SYNTAX_ERROR,
        )
        scored = self.engine.score(res)
        self.assertTrue(scored.is_scorable)
        self.assertEqual(scored.reward, 0.0)
        self.assertEqual(scored.failure_class, FailureClass.SYNTAX_ERROR)

    def test_timeout_reward_is_zero(self) -> None:
        res = ExecutionResult(
            job_id="job-104",
            task_id="py-sum-001",
            candidate_sha256=self.dummy_hash,
            test_bundle_sha256=self.dummy_hash,
            status=ExecutionStatus.TIMED_OUT,
            passed=0,
            total=10,
            elapsed_ms=10005,
            exit_code=124,
            worker_id="w1",
            failure_class=FailureClass.TIMEOUT,
        )
        scored = self.engine.score(res)
        self.assertTrue(scored.is_scorable)
        self.assertEqual(scored.reward, 0.0)
        self.assertEqual(scored.failure_class, FailureClass.TIMEOUT)

    def test_infrastructure_error_is_never_zero_reward(self) -> None:
        """Mandatory Invariant: Infrastructure failures MUST NOT contaminate training with 0.0."""
        for failure_class in [
            FailureClass.INFRA_WORKER_DOWN,
            FailureClass.INFRA_BUNDLE_MISMATCH,
            FailureClass.INFRA_TIMEOUT,
            FailureClass.INFRA_UNEXPECTED,
        ]:
            res = ExecutionResult(
                job_id="job-infra-01",
                task_id="py-sum-001",
                candidate_sha256=self.dummy_hash,
                test_bundle_sha256=self.dummy_hash,
                status=ExecutionStatus.INFRA_ERROR,
                passed=0,
                total=0,
                elapsed_ms=1,
                exit_code=1,
                worker_id="w1",
                failure_class=failure_class,
            )
            scored = self.engine.score(res)
            self.assertFalse(scored.is_scorable, f"Failed on {failure_class}: must be unscorable")
            self.assertIsNone(scored.reward, f"Failed on {failure_class}: reward must be None, NOT 0.0")
            self.assertIn("Infrastructure failure", scored.unscorable_reason or "")

    def test_empty_test_bundle_is_unscorable(self) -> None:
        res = ExecutionResult(
            job_id="job-empty",
            task_id="py-sum-001",
            candidate_sha256=self.dummy_hash,
            test_bundle_sha256=self.dummy_hash,
            status=ExecutionStatus.COMPLETED,
            passed=0,
            total=0,
            elapsed_ms=1,
            exit_code=0,
            worker_id="w1",
        )
        scored = self.engine.score(res)
        self.assertFalse(scored.is_scorable)
        self.assertIsNone(scored.reward)
        self.assertEqual(scored.unscorable_reason, "Empty test bundle (total tests <= 0)")


if __name__ == "__main__":
    unittest.main()
