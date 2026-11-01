"""Orchestrator for the execution-verified candidate generation and evaluation loop."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import uuid

from packages.contracts import (
    AuditEvent,
    ExecutionRequest,
    ExecutionResult,
    GenerationConfig,
    RewardResult,
    SandboxPolicy,
    Task,
)
from services.model.backend import ModelBackend
from services.rewards.engine import RewardEngine
from services.sandbox_worker.backend import SandboxBackend
from .store import JobStore


@dataclass
class PipelineResult:
    """Consolidated outcome of one full task execution pass."""
    job_id: str
    task_id: str
    candidate_sha256: str
    candidate_code: str
    execution: ExecutionResult
    reward: RewardResult
    audit: AuditEvent


class ExecutionLoopOrchestrator:
    """Orchestrates candidate generation, sandboxed execution, reward scoring, and persistence."""

    def __init__(
        self,
        store: JobStore,
        reward_engine: RewardEngine | None = None,
        runtime_image_digest: str = "sha256:d8b2e1a4" * 8,
    ):
        self.store = store
        self.reward_engine = reward_engine or RewardEngine()
        self.runtime_image_digest = runtime_image_digest

    def run_task(
        self,
        task: Task,
        model: ModelBackend,
        sandbox: SandboxBackend,
        gen_config: GenerationConfig | None = None,
        sandbox_policy: SandboxPolicy | None = None,
        actor: str = "controller-orchestrator",
    ) -> PipelineResult:
        """Executes one round of generation -> execution -> reward scoring -> audit."""
        job_id = f"job-{uuid.uuid4().hex[:12]}"
        gen_config = gen_config or GenerationConfig()
        sandbox_policy = sandbox_policy or SandboxPolicy()

        # 1. Register job in durable store
        self.store.create_job(job_id=job_id, task_id=task.task_id)

        # 2. Prompt model to generate candidate code
        gen_res = model.generate(
            prompt=task.prompt,
            seed=gen_config.seed,
            config=gen_config,
        )
        candidate_code = gen_res.extracted_code
        candidate_sha256 = hashlib.sha256(candidate_code.encode("utf-8")).hexdigest()

        # 3. Persist generated candidate
        self.store.record_candidate(
            candidate_sha256=candidate_sha256,
            task_id=task.task_id,
            prompt=task.prompt,
            code=candidate_code,
            model_name=gen_res.model_version,
            syntax_valid=gen_res.syntax_valid,
            prompt_tokens=gen_res.prompt_tokens,
            completion_tokens=gen_res.completion_tokens,
        )

        # 4. Build execution request for the sandbox worker
        exec_req = ExecutionRequest(
            job_id=job_id,
            task_id=task.task_id,
            candidate_code=candidate_code,
            candidate_sha256=candidate_sha256,
            test_bundle_ref=task.test_bundle_ref,
            test_bundle_sha256=task.test_bundle_sha256,
            runtime_image_digest=self.runtime_image_digest,
            sandbox_policy=sandbox_policy,
            deadline_epoch_ms=int(datetime.now(timezone.utc).timestamp() * 1000) + 60000,
        )

        # 5. Execute candidate code inside isolated sandbox
        exec_res = sandbox.execute(exec_req)
        self.store.record_execution(exec_res)

        # 6. Score deterministic reward (invariant: infra error is never 0.0)
        reward_res = self.reward_engine.score(exec_res)
        self.store.record_reward(reward_res)

        # 7. Record tamper-evident audit event
        audit_event = AuditEvent(
            event_id=f"audit-{uuid.uuid4().hex[:10]}",
            actor=actor,
            action="execute_and_score",
            resource_id=job_id,
            decision="allow" if not exec_res.is_infra_error else "investigate",
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            details={
                "task_id": task.task_id,
                "candidate_sha256": candidate_sha256,
                "status": exec_res.status.value,
                "reward": reward_res.reward,
                "is_scorable": reward_res.is_scorable,
                "failure_class": exec_res.failure_class.value,
            },
        )
        self.store.record_audit(audit_event)

        # 8. Mark job terminal state
        final_state = "COMPLETED" if not exec_res.is_infra_error else "FAILED"
        self.store.complete_job(job_id=job_id, state=final_state)

        return PipelineResult(
            job_id=job_id,
            task_id=task.task_id,
            candidate_sha256=candidate_sha256,
            candidate_code=candidate_code,
            execution=exec_res,
            reward=reward_res,
            audit=audit_event,
        )
