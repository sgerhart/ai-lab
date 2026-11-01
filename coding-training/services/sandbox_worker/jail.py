"""Sandbox jail containment and process execution."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from typing import Protocol

from packages.contracts import SandboxPolicy


@dataclass
class JailRunOutput:
    """Raw process execution metrics returned from the jail runner."""
    exit_code: int
    stdout: str
    stderr: str
    stdout_truncated: bool
    stderr_truncated: bool
    elapsed_ms: int
    timed_out: bool
    oom_killed: bool
    process_limited: bool
    result_payload: dict[str, object] | None


class SandboxJail(Protocol):
    """Protocol for jail implementations (Bubblewrap, Namespaces, Subprocess)."""

    def run(
        self,
        candidate_code: str,
        bundle_content: dict[str, object],
        policy: SandboxPolicy,
    ) -> JailRunOutput: ...


class SubprocessJail:
    """Portable subprocess jail with process group isolation and resource controls."""

    def __init__(self, harness_path: Path | None = None):
        if harness_path is None:
            self.harness_path = Path(__file__).resolve().parent / "harness.py"
        else:
            self.harness_path = harness_path

    def run(
        self,
        candidate_code: str,
        bundle_content: dict[str, object],
        policy: SandboxPolicy,
    ) -> JailRunOutput:
        with tempfile.TemporaryDirectory(prefix="ai_lab_jail_") as tmp_dir:
            work_dir = Path(tmp_dir)
            cand_path = work_dir / "candidate.py"
            bundle_path = work_dir / "bundle.json"
            result_path = work_dir / "result.json"

            cand_path.write_text(candidate_code, encoding="utf-8")
            bundle_path.write_text(json.dumps(bundle_content), encoding="utf-8")

            # Copy harness to temporary directory to avoid external path issues
            local_harness = work_dir / "harness.py"
            shutil.copyfile(self.harness_path, local_harness)

            cmd = [
                sys.executable,
                str(local_harness),
                "--candidate",
                str(cand_path),
                "--bundle",
                str(bundle_path),
                "--result",
                str(result_path),
            ]
            if policy.network_enabled:
                cmd.append("--allow-network")

            # Isolate environment
            clean_env = {
                "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                "PYTHONUNBUFFERED": "1",
                "PYTHONDONTWRITEBYTECODE": "1",
                "TMPDIR": str(work_dir),
            }

            def preexec_fn() -> None:
                os.setsid()  # Create new session/process group for clean teardown

            start_t = time.monotonic()
            timed_out = False
            oom_killed = False
            process_limited = False
            exit_code = 1
            raw_stdout = b""
            raw_stderr = b""

            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(work_dir),
                env=clean_env,
                preexec_fn=preexec_fn,
            )

            try:
                raw_stdout, raw_stderr = proc.communicate(timeout=policy.wall_timeout_seconds)
                exit_code = proc.returncode
            except subprocess.TimeoutExpired:
                timed_out = True
                try:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                except (ProcessLookupError, PermissionError):
                    pass
                raw_stdout, raw_stderr = proc.communicate()
                exit_code = -signal.SIGKILL
            except Exception as proc_err:
                raw_stderr = str(proc_err).encode("utf-8")

            elapsed_ms = int((time.monotonic() - start_t) * 1000)

            # Check signal termination reasons
            if exit_code in (-9, 137):
                if not timed_out:
                    oom_killed = True
            elif exit_code in (-signal.SIGSEGV, 139):
                oom_killed = True

            # Process output and check truncation
            stdout_str = raw_stdout.decode("utf-8", errors="replace")
            stderr_str = raw_stderr.decode("utf-8", errors="replace")

            stdout_truncated = len(stdout_str.encode("utf-8")) > policy.stdout_limit_bytes
            stderr_truncated = len(stderr_str.encode("utf-8")) > policy.stderr_limit_bytes

            if stdout_truncated:
                stdout_str = stdout_str[: policy.stdout_limit_bytes] + "\n[AI-LAB: STDOUT TRUNCATED]"
            if stderr_truncated:
                stderr_str = stderr_str[: policy.stderr_limit_bytes] + "\n[AI-LAB: STDERR TRUNCATED]"

            # Parse harness result payload if created
            result_payload: dict[str, object] | None = None
            if result_path.exists():
                try:
                    result_payload = json.loads(result_path.read_text(encoding="utf-8"))
                except Exception:
                    pass

            return JailRunOutput(
                exit_code=exit_code,
                stdout=stdout_str,
                stderr=stderr_str,
                stdout_truncated=stdout_truncated,
                stderr_truncated=stderr_truncated,
                elapsed_ms=elapsed_ms,
                timed_out=timed_out,
                oom_killed=oom_killed,
                process_limited=process_limited,
                result_payload=result_payload,
            )


class BubblewrapJail:
    """Hardened Linux jail using Bubblewrap (bwrap) unprivileged user namespaces."""

    def __init__(self, harness_path: Path | None = None):
        if harness_path is None:
            self.harness_path = Path(__file__).resolve().parent / "harness.py"
        else:
            self.harness_path = harness_path
        self.bwrap_bin = shutil.which("bwrap")
        self.fallback = SubprocessJail(harness_path=self.harness_path)

    @property
    def is_available(self) -> bool:
        return self.bwrap_bin is not None

    def run(
        self,
        candidate_code: str,
        bundle_content: dict[str, object],
        policy: SandboxPolicy,
    ) -> JailRunOutput:
        if not self.is_available:
            # Transparent fallback on non-Linux or systems without bwrap
            return self.fallback.run(candidate_code, bundle_content, policy)

        with tempfile.TemporaryDirectory(prefix="ai_lab_bwrap_") as tmp_dir:
            work_dir = Path(tmp_dir)
            cand_path = work_dir / "candidate.py"
            bundle_path = work_dir / "bundle.json"
            result_path = work_dir / "result.json"

            cand_path.write_text(candidate_code, encoding="utf-8")
            bundle_path.write_text(json.dumps(bundle_content), encoding="utf-8")
            local_harness = work_dir / "harness.py"
            shutil.copyfile(self.harness_path, local_harness)

            # Bubblewrap sandbox flags:
            # - unshare all namespaces
            # - unshare-net disables network entirely (air-gapped)
            # - drop all capabilities
            # - read-only system mounts
            # - ephemeral tmpfs workspace
            bwrap_cmd = [
                self.bwrap_bin,
                "--unshare-all",
                "--die-with-parent",
                "--cap-drop", "ALL",
                "--ro-bind", "/usr", "/usr",
                "--ro-bind", "/bin", "/bin",
                "--tmpfs", "/tmp",
                "--bind", str(work_dir), "/sandbox",
                "--chdir", "/sandbox",
            ]
            if os.path.exists("/lib"):
                bwrap_cmd.extend(["--ro-bind", "/lib", "/lib"])
            if os.path.exists("/lib64"):
                bwrap_cmd.extend(["--ro-bind", "/lib64", "/lib64"])
            if os.path.exists("/etc/alternatives"):
                bwrap_cmd.extend(["--ro-bind", "/etc/alternatives", "/etc/alternatives"])

            if not policy.network_enabled:
                bwrap_cmd.append("--unshare-net")

            # Add execution target inside sandbox
            bwrap_cmd.extend([
                "python3",
                "/sandbox/harness.py",
                "--candidate", "/sandbox/candidate.py",
                "--bundle", "/sandbox/bundle.json",
                "--result", "/sandbox/result.json",
            ])

            start_t = time.monotonic()
            timed_out = False
            oom_killed = False
            raw_stdout = b""
            raw_stderr = b""
            exit_code = 1

            proc = subprocess.Popen(
                bwrap_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid,
            )

            try:
                raw_stdout, raw_stderr = proc.communicate(timeout=policy.wall_timeout_seconds)
                exit_code = proc.returncode
            except subprocess.TimeoutExpired:
                timed_out = True
                try:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                except (ProcessLookupError, PermissionError):
                    pass
                raw_stdout, raw_stderr = proc.communicate()
                exit_code = -signal.SIGKILL

            elapsed_ms = int((time.monotonic() - start_t) * 1000)

            stdout_str = raw_stdout.decode("utf-8", errors="replace")
            stderr_str = raw_stderr.decode("utf-8", errors="replace")

            stdout_truncated = len(stdout_str.encode("utf-8")) > policy.stdout_limit_bytes
            stderr_truncated = len(stderr_str.encode("utf-8")) > policy.stderr_limit_bytes

            result_payload: dict[str, object] | None = None
            if result_path.exists():
                try:
                    result_payload = json.loads(result_path.read_text(encoding="utf-8"))
                except Exception:
                    pass

            return JailRunOutput(
                exit_code=exit_code,
                stdout=stdout_str,
                stderr=stderr_str,
                stdout_truncated=stdout_truncated,
                stderr_truncated=stderr_truncated,
                elapsed_ms=elapsed_ms,
                timed_out=timed_out,
                oom_killed=oom_killed,
                process_limited=False,
                result_payload=result_payload,
            )
