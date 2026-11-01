"""Unit tests for the controller store, execution orchestrator, and API endpoints."""

from __future__ import annotations

import time
import unittest
from fastapi.testclient import TestClient

from packages.contracts import (
    ExecutionResult,
    ExecutionStatus,
    FailureClass,
    GenerationConfig,
    SandboxPolicy,
    Split,
    Task,
)
from services.controller.app import app
from services.controller.loop import ExecutionLoopOrchestrator
from services.controller.store import JobStore
from services.model.backend import MockModelBackend
from services.rewards.engine import RewardEngine
from services.sandbox_worker.backend import MockSandboxBackend


class TestController(unittest.TestCase):
    """Verifies job store leases, execution loop orchestration, and controller REST APIs."""

    def setUp(self) -> None:
        self.store = JobStore(":memory:")
        self.reward_engine = RewardEngine()
        self.orchestrator = ExecutionLoopOrchestrator(
            store=self.store,
            reward_engine=self.reward_engine,
        )
        self.client = TestClient(app)

        self.sample_task = Task(
            task_id="py-ctrl-001",
            prompt="def solve(x: int) -> int:\n    return x + 1\n",
            function_contract="def solve(x: int) -> int:",
            source_provenance="unit_test_curation",
            test_bundle_ref="bundle-py-ctrl-001",
            test_bundle_sha256="c" * 64,
            split=Split.TRAIN,
            difficulty="easy",
            family_id="unit_testing",
        )

    def test_job_lease_lifecycle(self) -> None:
        """Verifies atomic job claims, lease renewals, and automatic lease expiration."""
        self.store.create_job("job-lease-01", "py-ctrl-001")

        # Worker 1 claims job for 1 second
        claim1 = self.store.claim_next_job("worker-alpha", lease_duration_seconds=0.1)
        self.assertIsNotNone(claim1)
        self.assertEqual(claim1["job_id"], "job-lease-01")

        # Worker 2 attempts to claim while lease is active -> None
        claim2 = self.store.claim_next_job("worker-beta", lease_duration_seconds=10.0)
        self.assertIsNone(claim2)

        # Worker 1 renews lease
        renewed = self.store.renew_lease("job-lease-01", "worker-alpha", extension_seconds=0.2)
        self.assertTrue(renewed)

        # Unauthorized worker cannot renew lease
        bad_renew = self.store.renew_lease("job-lease-01", "worker-impostor")
        self.assertFalse(bad_renew)

        # Wait for lease to expire
        time.sleep(0.3)

        # Worker 2 claims expired lease
        claim3 = self.store.claim_next_job("worker-beta", lease_duration_seconds=10.0)
        self.assertIsNotNone(claim3)
        self.assertEqual(claim3["job_id"], "job-lease-01")

        # Complete job
        self.store.complete_job("job-lease-01", state="COMPLETED")
        job = self.store.get_job("job-lease-01")
        self.assertIsNotNone(job)
        self.assertEqual(job["state"], "COMPLETED")
        self.assertIsNone(job["lease_owner"])

    def test_orchestrator_successful_pipeline(self) -> None:
        """Verifies full execution pipeline: model generate -> sandbox run -> reward score -> audit."""
        mock_model = MockModelBackend(
            responses={
                self.sample_task.prompt: "```python\ndef solve(x: int) -> int:\n    return x + 1\n```"
            }
        )
        mock_sandbox = MockSandboxBackend(
            default_status=ExecutionStatus.COMPLETED,
            default_passed=20,
            default_total=20,
        )

        res = self.orchestrator.run_task(
            task=self.sample_task,
            model=mock_model,
            sandbox=mock_sandbox,
            gen_config=GenerationConfig(seed=42),
            sandbox_policy=SandboxPolicy(),
            actor="test_runner",
        )

        self.assertEqual(res.execution.status, ExecutionStatus.COMPLETED)
        self.assertEqual(res.reward.reward, 1.0)
        self.assertTrue(res.reward.is_scorable)
        self.assertEqual(res.audit.action, "execute_and_score")
        self.assertEqual(res.audit.decision, "allow")

        # Verify durable storage
        persisted_job = self.store.get_job(res.job_id)
        self.assertIsNotNone(persisted_job)
        self.assertEqual(persisted_job["state"], "COMPLETED")
        self.assertIsNotNone(persisted_job["execution"])
        self.assertIsNotNone(persisted_job["reward"])
        self.assertEqual(persisted_job["reward"]["reward"], 1.0)

    def test_orchestrator_infrastructure_error_is_unscorable(self) -> None:
        """Mandatory Invariant: Infrastructure failures MUST NOT receive 0.0 and must be unscorable."""
        mock_model = MockModelBackend()
        # Simulate sandbox worker infrastructure failure (e.g. host VM crash or bundle missing)
        class BrokenInfraSandbox:
            def execute(self, req: object) -> ExecutionResult:
                return ExecutionResult(
                    job_id="job-broken-01",
                    task_id="py-ctrl-001",
                    candidate_sha256="a" * 64,
                    test_bundle_sha256="b" * 64,
                    status=ExecutionStatus.INFRA_ERROR,
                    passed=0,
                    total=0,
                    elapsed_ms=5,
                    exit_code=1,
                    stderr="Sandbox VM unreachable",
                    worker_id="infra-down-01",
                    failure_class=FailureClass.INFRA_WORKER_DOWN,
                )

        res = self.orchestrator.run_task(
            task=self.sample_task,
            model=mock_model,
            sandbox=BrokenInfraSandbox(),  # type: ignore[arg-type]
            actor="test_infra_runner",
        )

        self.assertEqual(res.execution.status, ExecutionStatus.INFRA_ERROR)
        self.assertIsNone(res.reward.reward)
        self.assertFalse(res.reward.is_scorable)
        self.assertIn("Infrastructure failure", res.reward.unscorable_reason)
        self.assertEqual(res.audit.decision, "investigate")

        persisted_job = self.store.get_job(res.job_id)
        self.assertIsNotNone(persisted_job)
        self.assertEqual(persisted_job["state"], "FAILED")

    def test_controller_api_endpoints(self) -> None:
        """Verifies REST endpoints for health, metrics, job submission, and audit trails."""
        # 1. Health
        health_resp = self.client.get("/v1/health")
        self.assertEqual(health_resp.status_code, 200)
        self.assertTrue(health_resp.json()["healthy"])

        # 2. Submit Job
        payload = {
            "task_id": "py-ctrl-002",
            "prompt": "def add(a: int, b: int) -> int:\n    return a + b\n",
            "test_bundle_ref": "bundle-002",
            "test_bundle_sha256": "e" * 64,
            "family_id": "math_basics",
        }
        submit_resp = self.client.post("/v1/jobs/submit", json=payload)
        self.assertEqual(submit_resp.status_code, 200)
        data = submit_resp.json()
        job_id = data["job_id"]
        self.assertIn("job-", job_id)
        self.assertEqual(data["status"], "completed")

        # 3. Get Job
        get_job_resp = self.client.get(f"/v1/jobs/{job_id}")
        self.assertEqual(get_job_resp.status_code, 200)
        job_data = get_job_resp.json()
        self.assertEqual(job_data["task_id"], "py-ctrl-002")
        self.assertEqual(job_data["state"], "COMPLETED")

        # 4. List Jobs
        list_resp = self.client.get("/v1/jobs")
        self.assertEqual(list_resp.status_code, 200)
        self.assertGreaterEqual(len(list_resp.json()), 1)

        # 5. Metrics
        metrics_resp = self.client.get("/v1/metrics")
        self.assertEqual(metrics_resp.status_code, 200)
        metrics = metrics_resp.json()
        self.assertGreaterEqual(metrics["total_jobs"], 1)

        # 6. Audit events
        audit_resp = self.client.get("/v1/audit/events")
        self.assertEqual(audit_resp.status_code, 200)
        self.assertGreaterEqual(len(audit_resp.json()), 1)

    def test_controller_tasks_api(self) -> None:
        """Verifies /v1/tasks catalog endpoint with split and difficulty filtering."""
        resp = self.client.get("/v1/tasks")
        self.assertEqual(resp.status_code, 200)
        tasks = resp.json()
        self.assertEqual(len(tasks), 105)

        # Split filter: train = 75, val = 15, test = 15
        train_resp = self.client.get("/v1/tasks?split=train")
        self.assertEqual(train_resp.status_code, 200)
        self.assertEqual(len(train_resp.json()), 75)

        val_resp = self.client.get("/v1/tasks?split=val")
        self.assertEqual(val_resp.status_code, 200)
        self.assertEqual(len(val_resp.json()), 15)

        test_resp = self.client.get("/v1/tasks?split=test")
        self.assertEqual(test_resp.status_code, 200)
        self.assertEqual(len(test_resp.json()), 15)

        # Difficulty filter
        easy_resp = self.client.get("/v1/tasks?difficulty=easy")
        self.assertEqual(easy_resp.status_code, 200)
        self.assertGreater(len(easy_resp.json()), 0)

        # Check fields of first task
        first = tasks[0]
        self.assertIn("task_id", first)
        self.assertIn("prompt", first)
        self.assertIn("entry_point", first)
        self.assertIn("test_bundle_sha256", first)

    def test_controller_models_api(self) -> None:
        """Verifies /v1/models catalog endpoint returning base models and adapter checkpoints."""
        resp = self.client.get("/v1/models")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("base_models", data)
        self.assertIn("checkpoints", data)
        base_models = data["base_models"]
        self.assertTrue(any(m["model_id"] == "Qwen/Qwen3-0.6B" for m in base_models))

    def test_controller_console_mount_and_redirect(self) -> None:
        """Verifies root redirect to /console/ and static web console serving."""
        from services.controller.app import console_dist
        if not console_dist.exists():
            self.skipTest("Console dist not built yet")

        root_resp = self.client.get("/", follow_redirects=False)
        self.assertIn(root_resp.status_code, (302, 307))
        self.assertEqual(root_resp.headers["location"], "/console/")

        console_resp = self.client.get("/console/")
        self.assertEqual(console_resp.status_code, 200)
        self.assertIn("<div id=\"root\">", console_resp.text)


    def test_controller_sse_stream(self) -> None:
        """Verifies Server-Sent Events (SSE) telemetry stream headers."""
        resp = self.client.get("/v1/events/stream")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/event-stream", resp.headers.get("content-type", ""))


if __name__ == "__main__":
    unittest.main()

