"""Deterministic reward scoring engine."""

from __future__ import annotations

from packages.contracts import (
    ExecutionResult,
    ExecutionStatus,
    FailureClass,
    RewardResult,
    RewardVersion,
)


class RewardEngine:
    """Pure deterministic reward scorer.
    
    Invariants:
    1. Infrastructure errors are NEVER assigned a numerical reward of 0.0. They are unscorable.
    2. Valid runs with total > 0 yield a normalized reward in [0.0, 1.0].
    3. Syntax errors, runtime crashes, and timeouts yield a reward of 0.0 with their failure class.
    """

    def __init__(self, version: str = RewardVersion.V1.value):
        self.version = version

    def score(self, execution: ExecutionResult) -> RewardResult:
        """Calculates deterministic reward from an execution report."""
        # Check for infrastructure failure first
        if execution.is_infra_error:
            return RewardResult(
                job_id=execution.job_id,
                candidate_sha256=execution.candidate_sha256,
                test_bundle_sha256=execution.test_bundle_sha256,
                reward=None,
                is_scorable=False,
                unscorable_reason=f"Infrastructure failure: {execution.failure_class.value}",
                passed=execution.passed,
                total=execution.total,
                scoring_version=self.version,
                failure_class=execution.failure_class,
            )

        # Empty test bundles cannot produce a score
        if execution.total <= 0:
            return RewardResult(
                job_id=execution.job_id,
                candidate_sha256=execution.candidate_sha256,
                test_bundle_sha256=execution.test_bundle_sha256,
                reward=None,
                is_scorable=False,
                unscorable_reason="Empty test bundle (total tests <= 0)",
                passed=0,
                total=0,
                scoring_version=self.version,
                failure_class=FailureClass.NONE,
            )

        # Syntax errors or compilation failures
        if execution.status == ExecutionStatus.COMPILE_ERROR:
            return RewardResult(
                job_id=execution.job_id,
                candidate_sha256=execution.candidate_sha256,
                test_bundle_sha256=execution.test_bundle_sha256,
                reward=0.0,
                is_scorable=True,
                passed=0,
                total=execution.total,
                scoring_version=self.version,
                failure_class=FailureClass.SYNTAX_ERROR,
            )

        # Timeouts
        if execution.status == ExecutionStatus.TIMED_OUT:
            return RewardResult(
                job_id=execution.job_id,
                candidate_sha256=execution.candidate_sha256,
                test_bundle_sha256=execution.test_bundle_sha256,
                reward=0.0,
                is_scorable=True,
                passed=0,
                total=execution.total,
                scoring_version=self.version,
                failure_class=FailureClass.TIMEOUT,
            )

        # Completed execution: score is fraction of tests passed
        fraction = execution.passed / float(execution.total)
        clamped_reward = max(0.0, min(1.0, fraction))
        
        failure_class = FailureClass.NONE
        if clamped_reward < 1.0:
            failure_class = FailureClass.ASSERTION_FAILED

        return RewardResult(
            job_id=execution.job_id,
            candidate_sha256=execution.candidate_sha256,
            test_bundle_sha256=execution.test_bundle_sha256,
            reward=clamped_reward,
            is_scorable=True,
            passed=execution.passed,
            total=execution.total,
            scoring_version=self.version,
            failure_class=failure_class,
        )
