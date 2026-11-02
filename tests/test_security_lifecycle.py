"""Unit tests for Security VM lifecycle and validation workflow (IWO-077).

Covers all 5 acceptance criteria:
1. Fake-provider workflow covers success (benign & untrusted) and major failure points.
2. No transition bypasses approval.
3. Cleanup is idempotent.
4. Residual check gates completion and triggers blocked incident state on orphan.
5. Resume after process restart is supported by LangGraph checkpointer.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.security.events import EmbeddedPayloadRefused
from ai_lab_platform.security.hypervisor import (
    AuthContext,
    FakeHypervisor,
    IsolationError,
)
from ai_lab_platform.security.lifecycle import (
    SecurityVmLifecycleEngine,
    SecurityVmWorkflowState,
    StepName,
    WorkflowStatus,
    build_security_vm_graph,
    init_workflow_state,
    thread_config,
)

try:
    from langgraph.checkpoint.memory import MemorySaver
    from langgraph.types import Command
except ImportError:
    MemorySaver = None  # type: ignore[misc, assignment]
    Command = None  # type: ignore[misc, assignment]


class SecurityVmLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.hypervisor = FakeHypervisor()
        self.engine = SecurityVmLifecycleEngine(self.hypervisor)

    def test_ac1_benign_workflow_happy_path(self) -> None:
        """AC 1: Benign sample executes full 14-step lifecycle to complete."""
        state = init_workflow_state(
            "job-benign-1",
            template_id="fixture-linux",
            profile="linux-static",
            execution_class="benign",
        )
        self.assertEqual(state["current_step"], StepName.INVENTORY.value)

        completed = self.engine.run_to_completion(state)
        self.assertEqual(completed["status"], WorkflowStatus.COMPLETED.value)
        self.assertEqual(completed["cleanup_status"], "verified")
        self.assertEqual(completed["residual_vms"], [])
        self.assertTrue(completed["benign_validation_ok"])
        self.assertIn("analyzed", completed["findings"][0])
        self.assertEqual(len(completed["evidence"]), 1)
        self.assertTrue(completed["report"]["status"] == "success")
        self.assertEqual(self.hypervisor.residual("job-benign-1"), [])

        # Verify audit history tracked all steps
        steps_run = [h["step"] for h in completed["step_history"]]
        self.assertIn(StepName.INVENTORY.value, steps_run)
        self.assertIn(StepName.TEMPLATE_VALIDATE.value, steps_run)
        self.assertIn(StepName.NETWORK_VALIDATE.value, steps_run)
        self.assertIn(StepName.CLONE_REQUEST.value, steps_run)
        self.assertIn(StepName.BOOT.value, steps_run)
        self.assertIn(StepName.GUEST_READY.value, steps_run)
        self.assertIn(StepName.BENIGN_VALIDATION.value, steps_run)
        self.assertIn(StepName.EXECUTION_APPROVAL.value, steps_run)
        self.assertIn(StepName.ANALYSIS.value, steps_run)
        self.assertIn(StepName.COLLECT.value, steps_run)
        self.assertIn(StepName.SHUTDOWN.value, steps_run)
        self.assertIn(StepName.DESTROY.value, steps_run)
        self.assertIn(StepName.RESIDUAL_CHECK.value, steps_run)
        self.assertIn(StepName.REPORT.value, steps_run)

    def test_ac1_and_ac2_untrusted_workflow_pauses_for_approval_and_resumes(self) -> None:
        """AC 1 & AC 2: Untrusted workflow strictly halts at approval gate until approved."""
        state = init_workflow_state(
            "job-untrusted-1",
            template_id="fixture-linux",
            profile="linux-behavioral",
            execution_class="untrusted",
        )

        paused = self.engine.run_to_completion(state)
        self.assertEqual(paused["status"], WorkflowStatus.AWAITING_APPROVAL.value)
        self.assertEqual(paused["current_step"], StepName.EXECUTION_APPROVAL.value)
        self.assertFalse(paused["analysis_output"].get("executed", False))
        # VM was cloned and booted for benign validation, but is paused before untrusted analysis
        self.assertTrue(paused["vm_id"])
        self.assertEqual(paused["vm_power"], "on")

        # Resume with operator approval
        resumed = self.engine.resume_approval(paused, approval_id="appr-operator-999")
        self.assertEqual(resumed["status"], WorkflowStatus.COMPLETED.value)
        self.assertEqual(resumed["approval_id"], "appr-operator-999")
        self.assertEqual(resumed["cleanup_status"], "verified")
        self.assertEqual(self.hypervisor.residual("job-untrusted-1"), [])

    def test_ac1_pre_clone_failure_fails_cleanly_without_vm(self) -> None:
        """AC 1: Pre-clone failure (e.g. unknown template) fails immediately without creating VM."""
        state = init_workflow_state(
            "job-invalid-tmpl",
            template_id="nonexistent-template",
            profile="linux-static",
        )
        res = self.engine.run_to_completion(state)
        self.assertEqual(res["status"], WorkflowStatus.FAILED.value)
        self.assertIn("template_validate failed", res["error"])
        self.assertEqual(res["vm_id"], "")
        self.assertEqual(self.hypervisor.residual("job-invalid-tmpl"), [])

    def test_ac1_pre_clone_network_denylist_failure(self) -> None:
        """AC 1: Denylisted network triggers preflight isolation failure."""
        state = init_workflow_state(
            "job-denylisted-net",
            template_id="fixture-linux",
            network_id="corp-lan-trusted",
        )
        res = self.engine.run_to_completion(state)
        self.assertEqual(res["status"], WorkflowStatus.FAILED.value)
        self.assertIn("network_validate failed", res["error"])
        self.assertEqual(res["vm_id"], "")

    def test_ac1_post_clone_failure_triggers_compensating_cleanup(self) -> None:
        """AC 1: Failure during boot triggers compensating power_off and destroy."""
        state = init_workflow_state(
            "job-boot-fail",
            template_id="fixture-linux",
        )
        # Advance until clone
        state = self.engine.execute_inventory(state)
        state = self.engine.execute_template_validate(state)
        state = self.engine.execute_network_validate(state)
        state = self.engine.execute_clone_request(state)
        vm_id = state["vm_id"]
        self.assertTrue(vm_id)
        self.assertEqual(self.hypervisor.residual("job-boot-fail"), [vm_id])

        # Sabotage power_on by clearing ownership to simulate error
        auth = AuthContext(job_id="job-boot-fail", actor="security")
        self.hypervisor._guests[vm_id].job_id = "other-job"

        res = self.engine.execute_boot(state)
        self.assertEqual(res["status"], WorkflowStatus.FAILED.value)
        self.assertIn("boot failed", res["error"])
        self.assertIn(StepName.COMPENSATING_CLEANUP.value, [h["step"] for h in res["step_history"]])

    def test_ac3_cleanup_is_idempotent(self) -> None:
        """AC 3: Cleanup is completely idempotent across multiple invocations."""
        state = init_workflow_state(
            "job-idempotent",
            template_id="fixture-linux",
        )
        # Run until completed
        completed = self.engine.run_to_completion(state)
        self.assertEqual(completed["cleanup_status"], "verified")

        # Re-invoke compensating cleanup on already cleaned state
        second = self.engine.execute_compensating_cleanup(completed)
        self.assertEqual(second["cleanup_status"], "verified")
        self.assertEqual(second["residual_vms"], [])

        # Third time
        third = self.engine.execute_destroy(second)
        self.assertEqual(third["vm_id"], "")

    def test_ac4_residual_check_gates_completion_and_triggers_blocked_incident(self) -> None:
        """AC 4: Residual check gates completion; orphaned VM leads to BLOCKED incident state."""
        state = init_workflow_state(
            "job-orphan-incident",
            template_id="fixture-linux",
        )
        # Advance to post-clone
        state = self.engine.execute_inventory(state)
        state = self.engine.execute_template_validate(state)
        state = self.engine.execute_network_validate(state)
        state = self.engine.execute_clone_request(state)
        vm_id = state["vm_id"]

        # Simulate orphaned guest that hypervisor destroy failed to wipe
        # by registering a second phantom guest under this job_id
        from ai_lab_platform.security.hypervisor import _Guest
        self.hypervisor._guests["vm-ghost-99"] = _Guest(
            vm_id="vm-ghost-99",
            job_id="job-orphan-incident",
            template_id="fixture-linux",
            network_id=self.hypervisor.isolated_network,
        )

        # Run compensating cleanup
        res = self.engine.execute_compensating_cleanup(state)
        # Residuals still exist!
        self.assertEqual(res["status"], WorkflowStatus.BLOCKED.value)
        self.assertEqual(res["cleanup_status"], "failed")
        self.assertIn("vm-ghost-99", res["residual_vms"])

        # Attempting report when blocked must fail
        blocked_report = self.engine.execute_report(res)
        self.assertEqual(blocked_report["status"], WorkflowStatus.BLOCKED.value)
        self.assertIn("residual resources remain", blocked_report["error"])
        self.assertFalse(blocked_report["report"].get("status") == "success")

    @unittest.skipIf(MemorySaver is None or Command is None, "langgraph not installed")
    def test_ac5_langgraph_resumable_graph_and_process_restart(self) -> None:
        """AC 5: LangGraph workflow pauses for untrusted approval, survives restart, and resumes."""
        saver = MemorySaver()
        graph1 = build_security_vm_graph(self.hypervisor, checkpointer=saver)

        initial_state = init_workflow_state(
            "job-graph-restart",
            template_id="fixture-linux",
            profile="linux-behavioral",
            execution_class="untrusted",
        )
        cfg = thread_config("job-graph-restart")

        # Run until interrupt at execution_approval
        result = graph1.invoke(initial_state, cfg)
        self.assertTrue(result.get("__interrupt__"))
        self.assertIn("execution_approval", graph1.get_state(cfg).next)

        # Simulate process restart by building a fresh graph instance using same saver
        graph2 = build_security_vm_graph(self.hypervisor, checkpointer=saver)
        snapshot = graph2.get_state(cfg)
        self.assertIn("execution_approval", snapshot.next)

        # Resume execution with approval token
        final_result = graph2.invoke(Command(resume="appr-operator-pass"), cfg)
        self.assertEqual(final_result["status"], WorkflowStatus.COMPLETED.value)
        self.assertEqual(final_result["cleanup_status"], "verified")
        self.assertEqual(final_result["approval_id"], "appr-operator-pass")
        self.assertEqual(self.hypervisor.residual("job-graph-restart"), [])


if __name__ == "__main__":
    unittest.main()
