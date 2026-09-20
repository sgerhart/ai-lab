import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.state_machine import IllegalTransition, transition
from ai_lab_platform.work_order import Status


class StateMachineTests(unittest.TestCase):
    def test_happy_path(self) -> None:
        s = Status.CREATED
        s = transition(s, Status.QUEUED)
        s = transition(s, Status.RUNNING)
        s = transition(s, Status.COMPLETED)
        self.assertEqual(s, Status.COMPLETED)

    def test_reject_completed_to_running(self) -> None:
        with self.assertRaises(IllegalTransition):
            transition(Status.COMPLETED, Status.RUNNING)

    def test_failed_can_retry(self) -> None:
        s = transition(Status.FAILED, Status.QUEUED)
        self.assertEqual(s, Status.QUEUED)


if __name__ == "__main__":
    unittest.main()
