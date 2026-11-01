"""Standalone in-jail test execution harness.

Invoked inside the sandbox environment to execute candidate code against an immutable
test bundle and output structured execution metrics without disclosing hidden test data.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import traceback


def block_network_access() -> None:
    """Disables network socket operations at the runtime level (defense-in-depth)."""
    import socket

    def denied(*args: object, **kwargs: object) -> None:
        raise PermissionError("Network egress denied by SandboxPolicy (deny_all)")

    socket.socket = denied  # type: ignore[assignment]
    socket.create_connection = denied  # type: ignore[assignment]
    socket.getaddrinfo = denied  # type: ignore[assignment]
    socket.gethostbyname = denied  # type: ignore[assignment]


def run_harness(
    candidate_path: Path,
    bundle_path: Path,
    result_path: Path,
    deny_network: bool = True,
) -> int:
    """Executes candidate code against test bundle and writes result payload."""
    if deny_network:
        block_network_access()

    if not candidate_path.exists():
        result = {
            "status": "infra_error",
            "failure_class": "infra_unexpected",
            "passed": 0,
            "total": 0,
            "error": f"Candidate file missing: {candidate_path}",
        }
        result_path.write_text(json.dumps(result), encoding="utf-8")
        return 2

    if not bundle_path.exists():
        result = {
            "status": "infra_error",
            "failure_class": "infra_bundle_mismatch",
            "passed": 0,
            "total": 0,
            "error": f"Test bundle missing: {bundle_path}",
        }
        result_path.write_text(json.dumps(result), encoding="utf-8")
        return 2

    try:
        bundle_data = json.loads(bundle_path.read_text(encoding="utf-8"))
    except Exception as err:
        result = {
            "status": "infra_error",
            "failure_class": "infra_bundle_mismatch",
            "passed": 0,
            "total": 0,
            "error": f"Corrupted test bundle JSON: {err}",
        }
        result_path.write_text(json.dumps(result), encoding="utf-8")
        return 2

    entry_point = bundle_data.get("entry_point", "")
    test_cases = bundle_data.get("test_cases", [])
    total_cases = len(test_cases)

    candidate_code = candidate_path.read_text(encoding="utf-8")

    # 1. Compilation check
    try:
        compiled = compile(candidate_code, str(candidate_path), "exec")
    except SyntaxError as syn_err:
        result = {
            "status": "compile_error",
            "failure_class": "syntax_error",
            "passed": 0,
            "total": total_cases,
            "error": f"SyntaxError at line {syn_err.lineno}: {syn_err.msg}",
        }
        result_path.write_text(json.dumps(result), encoding="utf-8")
        return 1
    except Exception as comp_err:
        result = {
            "status": "compile_error",
            "failure_class": "syntax_error",
            "passed": 0,
            "total": total_cases,
            "error": f"Compilation failed: {comp_err}",
        }
        result_path.write_text(json.dumps(result), encoding="utf-8")
        return 1

    # 2. Scope execution
    local_scope: dict[str, object] = {
        "__name__": "__main__",
        "__file__": str(candidate_path),
        "__builtins__": __builtins__,
    }

    try:
        exec(compiled, local_scope)
    except MemoryError:
        result = {
            "status": "runtime_error",
            "failure_class": "memory_exceeded",
            "passed": 0,
            "total": total_cases,
            "error": "MemoryError: candidate exceeded memory quota during import",
        }
        result_path.write_text(json.dumps(result), encoding="utf-8")
        return 1
    except Exception as exec_err:
        result = {
            "status": "runtime_error",
            "failure_class": "assertion_failed",
            "passed": 0,
            "total": total_cases,
            "error": f"Runtime error on import: {exec_err}\n{traceback.format_exc(limit=3)}",
        }
        result_path.write_text(json.dumps(result), encoding="utf-8")
        return 1

    if entry_point not in local_scope or not callable(local_scope[entry_point]):
        result = {
            "status": "runtime_error",
            "failure_class": "assertion_failed",
            "passed": 0,
            "total": total_cases,
            "error": f"Entry point function '{entry_point}' not found or not callable",
        }
        result_path.write_text(json.dumps(result), encoding="utf-8")
        return 1

    target_func = local_scope[entry_point]
    passed = 0
    first_failure_msg = ""

    for idx, tc in enumerate(test_cases):
        inputs = tc.get("inputs", [])
        expected = tc.get("expected")

        try:
            actual = target_func(*inputs)
            if actual == expected:
                passed += 1
            else:
                if not first_failure_msg:
                    # Report mismatch without dumping full hidden expected values
                    first_failure_msg = f"Test case {idx} failed: output did not match expected"
        except MemoryError:
            result = {
                "status": "runtime_error",
                "failure_class": "memory_exceeded",
                "passed": passed,
                "total": total_cases,
                "error": f"MemoryError on test case {idx}",
            }
            result_path.write_text(json.dumps(result), encoding="utf-8")
            return 1
        except PermissionError as perm_err:
            result = {
                "status": "runtime_error",
                "failure_class": "forbidden_call",
                "passed": passed,
                "total": total_cases,
                "error": f"PermissionError on test case {idx}: {perm_err}",
            }
            result_path.write_text(json.dumps(result), encoding="utf-8")
            return 1
        except Exception as case_err:
            if not first_failure_msg:
                first_failure_msg = f"Exception on test case {idx}: {type(case_err).__name__}: {case_err}"

    all_passed = (passed == total_cases) and total_cases > 0
    status = "completed" if all_passed else "runtime_error"
    failure_class = "none" if all_passed else "assertion_failed"

    result = {
        "status": status,
        "failure_class": failure_class,
        "passed": passed,
        "total": total_cases,
        "error": first_failure_msg if not all_passed else "",
    }
    result_path.write_text(json.dumps(result), encoding="utf-8")
    return 0 if all_passed else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="In-jail execution harness")
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--result", required=True, type=Path)
    parser.add_argument("--allow-network", action="store_true", default=False)
    args = parser.parse_args()

    exit_code = run_harness(
        candidate_path=args.candidate,
        bundle_path=args.bundle,
        result_path=args.result,
        deny_network=not args.allow_network,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
