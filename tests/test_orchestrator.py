import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.orchestrator import Orchestrator
from ai_lab_platform.store import SqliteStore
from ai_lab_platform.work_order import Status, WorkOrder


class OrchestratorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
        self.tmp.close()
        self.store = SqliteStore(self.tmp.name)
        self.orch = Orchestrator(self.store)

    def test_submit_and_complete(self) -> None:
        order = WorkOrder.new(
            objective="noop",
            agent="development",
            allowed_tools=["repo_read"],
        )
        order = self.orch.submit(order)
        self.assertEqual(order.status, Status.QUEUED)
        started = self.orch.start_next()
        assert started is not None
        self.assertEqual(started.status, Status.RUNNING)
        done = self.orch.complete(started.id, "ok")
        self.assertEqual(done.status, Status.COMPLETED)
        self.assertEqual(done.final_result, "ok")

    def test_privileged_tool_requires_approval(self) -> None:
        order = WorkOrder.new(
            objective="push",
            agent="development",
            allowed_tools=["git_push"],
        )
        order = self.orch.submit(order)
        started = self.orch.start_next()
        assert started is not None
        paused = self.orch.request_tool(started.id, "git_push")
        self.assertEqual(paused.status, Status.AWAITING_APPROVAL)
        queued = self.orch.approve(paused.id)
        self.assertEqual(queued.status, Status.QUEUED)

    def test_retry_then_stop(self) -> None:
        order = WorkOrder.new(
            objective="flaky",
            agent="research",
            allowed_tools=["http_get"],
        )
        order.execution_policy.max_attempts = 2
        order = self.orch.submit(order)
        started = self.orch.start_next()
        assert started is not None
        again = self.orch.fail(started.id, "boom")
        self.assertEqual(again.status, Status.QUEUED)
        started2 = self.orch.start_next()
        assert started2 is not None
        terminal = self.orch.fail(started2.id, "boom2")
        self.assertEqual(terminal.status, Status.FAILED)

    def test_recover_running(self) -> None:
        order = WorkOrder.new(objective="long", agent="lab-operations", allowed_tools=["health_read"])
        self.orch.submit(order)
        started = self.orch.start_next()
        assert started is not None
        recovered = self.orch.recover_running()
        self.assertEqual(len(recovered), 1)
        self.assertIn(recovered[0].status, {Status.QUEUED, Status.FAILED})


if __name__ == "__main__":
    unittest.main()
