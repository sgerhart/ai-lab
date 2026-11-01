"""Negative security test suite for sandbox isolation boundaries.

Verifies that adversarial or malfunctioning candidate programs are strictly contained
without escaping, exhausting host resources, or corrupting state.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
import unittest

from packages.contracts import (
    ExecutionRequest,
    ExecutionStatus,
    FailureClass,
    SandboxPolicy,
)
from packages.datasets.task_loader import TaskLoader
from services.sandbox_worker.jail import SubprocessJail
from services.sandbox_worker.worker import SandboxWorker


class TestNegativeSecurity(unittest.TestCase):
    """Negative security test suite executing adversarial programs in isolated jails."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.base_dir = Path(__file__).resolve().parent.parent.parent
        cls.bundles_dir = cls.base_dir / "datasets" / "test_bundles"
        cls.loader = TaskLoader(root_dir=cls.base_dir / "datasets")
        cls.tasks = cls.loader.load_tasks()
        cls.task = cls.tasks[0]  # py-arr-001 (sum_array)

        cls.worker = SandboxWorker(
            worker_id="security-test-worker",
            bundles_dir=cls.bundles_dir,
            jail=SubprocessJail(),
            enforce_execution_flag=False,  # Bypassed for authorized security test suite
        )

    def _execute_code(
        self,
        code: str,
        policy: SandboxPolicy | None = None,
    ) -> tuple[ExecutionStatus, FailureClass, str]:
        cand_hash = hashlib.sha256(code.encode("utf-8")).hexdigest()
        req = ExecutionRequest(
            job_id="sec-job-01",
            task_id=self.task.task_id,
            candidate_code=code,
            candidate_sha256=cand_hash,
            test_bundle_ref=self.task.test_bundle_ref,
            test_bundle_sha256=self.task.test_bundle_sha256,
            runtime_image_digest="sha256:d8b2e1a4" * 8,
            sandbox_policy=policy or SandboxPolicy(wall_timeout_seconds=2.0),
            deadline_epoch_ms=2000000000000,
        )
        res = self.worker.execute(req)
        return res.status, res.failure_class, res.stderr

    def test_syntax_error_candidate(self) -> None:
        """Candidate with invalid syntax must be trapped at compile time."""
        broken_code = "def reverse_string(s: str) -> str:\n    this is completely broken syntax !!\n"
        status, fc, err = self._execute_code(broken_code)

        self.assertEqual(status, ExecutionStatus.COMPILE_ERROR)
        self.assertEqual(fc, FailureClass.SYNTAX_ERROR)
        self.assertIn("SyntaxError", err)

    def test_infinite_loop_timeout_containment(self) -> None:
        """Candidate with infinite loop must be terminated at wall_timeout_seconds."""
        infinite_loop_code = (
            "def reverse_string(s: str) -> str:\n"
            "    while True:\n"
            "        pass\n"
            "    return s\n"
        )
        tight_policy = SandboxPolicy(wall_timeout_seconds=1.0)
        status, fc, err = self._execute_code(infinite_loop_code, policy=tight_policy)

        self.assertEqual(status, ExecutionStatus.TIMED_OUT)
        self.assertEqual(fc, FailureClass.TIMEOUT)
        self.assertIn("timeout", err.lower())

    def test_network_egress_denied(self) -> None:
        """Candidate attempting network socket creation must be blocked immediately."""
        network_exploit_code = (
            "def reverse_string(s: str) -> str:\n"
            "    import socket\n"
            "    s_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\n"
            "    s_sock.connect(('1.1.1.1', 80))\n"
            "    return s\n"
        )
        status, fc, err = self._execute_code(network_exploit_code)

        self.assertEqual(status, ExecutionStatus.RUNTIME_ERROR)
        self.assertEqual(fc, FailureClass.FORBIDDEN_CALL)
        self.assertIn("Network egress denied", err)

    def test_memory_allocation_bomb(self) -> None:
        """Candidate attempting large memory allocation must be trapped as memory_exceeded."""
        memory_bomb_code = (
            "def reverse_string(s: str) -> str:\n"
            "    import sys\n"
            "    # Attempt to allocate maximum virtual memory quota\n"
            "    big = bytearray(sys.maxsize)\n"
            "    return str(len(big))\n"
        )
        status, fc, err = self._execute_code(memory_bomb_code)

        self.assertEqual(status, ExecutionStatus.RUNTIME_ERROR)
        self.assertEqual(fc, FailureClass.MEMORY_EXCEEDED)
        self.assertTrue("MemoryError" in err or "memory" in err.lower())

    def test_stdout_bomb_truncation(self) -> None:
        """Candidate attempting to flood stdout must have output strictly truncated."""
        stdout_bomb_code = (
            "def reverse_string(s: str) -> str:\n"
            "    for _ in range(5000):\n"
            "        print('A' * 500)\n"
            "    return s[::-1]\n"
        )
        small_limit_policy = SandboxPolicy(
            wall_timeout_seconds=5.0,
            stdout_limit_bytes=4096,
        )
        cand_hash = hashlib.sha256(stdout_bomb_code.encode("utf-8")).hexdigest()
        req = ExecutionRequest(
            job_id="sec-stdout-bomb",
            task_id=self.task.task_id,
            candidate_code=stdout_bomb_code,
            candidate_sha256=cand_hash,
            test_bundle_ref=self.task.test_bundle_ref,
            test_bundle_sha256=self.task.test_bundle_sha256,
            runtime_image_digest="sha256:d8b2e1a4" * 8,
            sandbox_policy=small_limit_policy,
            deadline_epoch_ms=2000000000000,
        )

        res = self.worker.execute(req)
        self.assertTrue(res.stdout_truncated)
        self.assertIn("[AI-LAB: STDOUT TRUNCATED]", res.stdout)
        self.assertLessEqual(len(res.stdout.encode("utf-8")), small_limit_policy.stdout_limit_bytes + 200)

    def test_unauthorized_filesystem_modification_blocked(self) -> None:
        """Candidate attempting to modify test bundle or system files must be contained."""
        fs_attack_code = (
            "def reverse_string(s: str) -> str:\n"
            "    try:\n"
            "        with open('/nonexistent_root_dir/attack.txt', 'w') as f:\n"
            "            f.write('compromised')\n"
            "    except Exception:\n"
            "        pass\n"
            "    return s[::-1]\n"
        )
        status, fc, _ = self._execute_code(fs_attack_code)
        self.assertEqual(status, ExecutionStatus.COMPLETED)
        self.assertEqual(fc, FailureClass.NONE)


if __name__ == "__main__":
    unittest.main()
