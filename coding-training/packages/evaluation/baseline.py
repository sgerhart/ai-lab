"""Reproducible baseline holdout evaluation runner."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
from typing import Any

from packages.contracts import (
    BaselineReport,
    ExecutionRequest,
    FailureClass,
    GenerationConfig,
    SandboxPolicy,
    Split,
    SplitMetrics,
    Task,
    TaskEvaluationResult,
)
from packages.datasets.task_loader import TaskLoader
from services.model.backend import ModelBackend
from services.rewards.engine import RewardEngine
from services.sandbox_worker.backend import SandboxBackend


def format_task_prompt(task: Task) -> str:
    """Formats a standardized code generation prompt for a given task.
    
    Invariant: Zero hidden test cases or assertion values are disclosed.
    """
    return (
        f"You are an expert Python programmer.\n"
        f"Task ID: {task.task_id}\n"
        f"Write a Python function that solves the following problem:\n\n"
        f"{task.prompt.strip()}\n\n"
        f"Contract:\n"
        f"{task.function_contract.strip()}\n\n"
        f"Return ONLY valid Python code enclosed in a ```python ... ``` markdown block.\n"
        f"Do not include explanations, comments outside the code, unit tests, or assertions."
    )


class BaselineEvaluator:
    """Evaluates models against disjoint task splits and generates reproducible baseline reports."""

    def __init__(
        self,
        model_backend: ModelBackend,
        sandbox_backend: SandboxBackend,
        task_loader: TaskLoader | None = None,
        reward_engine: RewardEngine | None = None,
        policy: SandboxPolicy | None = None,
        model_id: str = "base-model",
        model_revision: str = "v1",
        runtime_image_digest: str = "sha256:d8b2e1a4" * 8,
    ):
        self.model_backend = model_backend
        self.sandbox_backend = sandbox_backend
        self.task_loader = task_loader or TaskLoader()
        self.reward_engine = reward_engine or RewardEngine()
        self.policy = policy or SandboxPolicy(
            wall_timeout_seconds=5.0,
            stdout_limit_bytes=65536,
            stderr_limit_bytes=65536,
        )
        self.model_id = model_id
        self.model_revision = model_revision
        self.runtime_image_digest = runtime_image_digest

    def evaluate_task(
        self,
        task: Task,
        generation_config: GenerationConfig | None = None,
        seed: int = 42,
    ) -> TaskEvaluationResult:
        """Evaluates a single task end-to-end: prompt -> generate -> sandbox run -> reward."""
        gen_config = generation_config or GenerationConfig(seed=seed)
        prompt = format_task_prompt(task)

        # 1. Model inference
        gen_res = self.model_backend.generate(
            prompt=prompt,
            seed=seed,
            config=gen_config,
        )
        candidate_code = gen_res.extracted_code
        candidate_sha256 = hashlib.sha256(candidate_code.encode("utf-8")).hexdigest()

        # 2. Syntax check failure short-circuit
        if not gen_res.syntax_valid:
            return TaskEvaluationResult(
                task_id=task.task_id,
                split=task.split,
                family_id=task.family_id,
                model_id=self.model_id,
                candidate_sha256=candidate_sha256,
                passed=False,
                reward=0.0,
                passed_tests=0,
                total_tests=20,
                syntax_valid=False,
                error_class=FailureClass.SYNTAX_ERROR,
                latency_ms=gen_res.latency_ms,
                prompt_tokens=gen_res.prompt_tokens,
                completion_tokens=gen_res.completion_tokens,
            )

        # 3. Sandbox execution
        exec_req = ExecutionRequest(
            job_id=f"eval-{task.task_id}-{seed}",
            task_id=task.task_id,
            candidate_code=candidate_code,
            candidate_sha256=candidate_sha256,
            test_bundle_ref=task.test_bundle_ref,
            test_bundle_sha256=task.test_bundle_sha256,
            runtime_image_digest=self.runtime_image_digest,
            sandbox_policy=self.policy,
            deadline_epoch_ms=int(time.time() * 1000) + 60000,
        )
        exec_res = self.sandbox_backend.execute(exec_req)

        # 4. Deterministic reward scoring
        reward_res = self.reward_engine.score(exec_res)
        passed = bool(reward_res.reward is not None and reward_res.reward >= 1.0)

        total_tests = exec_res.total if exec_res.total > 0 else 20
        return TaskEvaluationResult(
            task_id=task.task_id,
            split=task.split,
            family_id=task.family_id,
            model_id=self.model_id,
            candidate_sha256=candidate_sha256,
            passed=passed,
            reward=reward_res.reward,
            passed_tests=exec_res.passed,
            total_tests=total_tests,
            syntax_valid=True,
            error_class=exec_res.failure_class,
            latency_ms=gen_res.latency_ms + exec_res.elapsed_ms,
            prompt_tokens=gen_res.prompt_tokens,
            completion_tokens=gen_res.completion_tokens,
        )

    def evaluate_split(
        self,
        split: Split,
        generation_config: GenerationConfig | None = None,
        seed: int = 42,
    ) -> tuple[SplitMetrics, list[TaskEvaluationResult]]:
        """Evaluates all tasks belonging to a specified split."""
        tasks = self.task_loader.get_tasks_by_split(split)
        results: list[TaskEvaluationResult] = []

        for task in tasks:
            res = self.evaluate_task(task, generation_config=generation_config, seed=seed)
            results.append(res)

        total_tasks = len(tasks)
        evaluated_tasks = len(results)
        passed_tasks = sum(1 for r in results if r.passed)
        pass_at_1 = round(passed_tasks / total_tasks, 4) if total_tasks > 0 else 0.0

        scorable_rewards = [r.reward for r in results if r.reward is not None]
        mean_reward = (
            round(sum(scorable_rewards) / len(scorable_rewards), 4)
            if scorable_rewards
            else 0.0
        )

        syntax_valid_count = sum(1 for r in results if r.syntax_valid)
        syntax_valid_rate = (
            round(syntax_valid_count / total_tasks, 4) if total_tasks > 0 else 0.0
        )

        compile_errors = sum(
            1 for r in results if r.error_class == FailureClass.SYNTAX_ERROR
        )
        runtime_errors = sum(
            1
            for r in results
            if not r.passed
            and r.error_class not in (FailureClass.NONE, FailureClass.SYNTAX_ERROR, FailureClass.TIMEOUT)
            and not r.error_class.value.startswith("infra_")
        )
        timeouts = sum(1 for r in results if r.error_class == FailureClass.TIMEOUT)
        infra_errors = sum(
            1 for r in results if r.error_class.value.startswith("infra_")
        )

        metrics = SplitMetrics(
            split=split,
            total_tasks=total_tasks,
            evaluated_tasks=evaluated_tasks,
            passed_tasks=passed_tasks,
            pass_at_1=pass_at_1,
            mean_reward=mean_reward,
            syntax_valid_count=syntax_valid_count,
            syntax_valid_rate=syntax_valid_rate,
            compile_errors=compile_errors,
            runtime_errors=runtime_errors,
            timeouts=timeouts,
            infra_errors=infra_errors,
        )
        return metrics, results

    def evaluate_holdout(
        self,
        splits: list[Split] | None = None,
        generation_config: GenerationConfig | None = None,
        seed: int = 42,
        metadata: dict[str, Any] | None = None,
    ) -> BaselineReport:
        """Evaluates held-out evaluation splits and returns a reproducible BaselineReport."""
        target_splits = splits or [Split.VAL, Split.TEST]
        manifest = self.task_loader.load_manifest()

        split_metrics_dict: dict[str, SplitMetrics] = {}
        all_results: list[TaskEvaluationResult] = []

        for split in target_splits:
            metrics, results = self.evaluate_split(
                split, generation_config=generation_config, seed=seed
            )
            split_metrics_dict[split.value] = metrics
            all_results.extend(results)

        total_evaluated = len(all_results)
        total_passed = sum(1 for r in all_results if r.passed)
        global_pass_at_1 = (
            round(total_passed / total_evaluated, 4) if total_evaluated > 0 else 0.0
        )

        scorable_rewards = [r.reward for r in all_results if r.reward is not None]
        global_mean_reward = (
            round(sum(scorable_rewards) / len(scorable_rewards), 4)
            if scorable_rewards
            else 0.0
        )

        now_utc = datetime.now(timezone.utc)
        report_id = f"baseline-{now_utc.strftime('%Y%m%d-%H%M%S')}"

        report_metadata = {
            "model_id": self.model_id,
            "model_revision": self.model_revision,
            "seed": seed,
            "generation_config": (generation_config or GenerationConfig(seed=seed)).model_dump(),
            "evaluated_splits": [s.value for s in target_splits],
            **(metadata or {}),
        }

        return BaselineReport(
            report_id=report_id,
            created_at=now_utc.isoformat(),
            model_id=self.model_id,
            model_revision=self.model_revision,
            dataset_hash=manifest.manifest_hash,
            splits=split_metrics_dict,
            global_pass_at_1=global_pass_at_1,
            global_mean_reward=global_mean_reward,
            results=all_results,
            metadata=report_metadata,
        )

    @staticmethod
    def export_report(report: BaselineReport, output_path: Path | str) -> Path:
        """Exports a baseline report as formatted, reproducible JSON."""
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(report.model_dump(), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return target
