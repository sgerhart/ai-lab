"""Dataset validation, family disjointness verification, and reference solution testing."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

from packages.contracts import Split, Task


@dataclass
class ValidationReport:
    """Detailed summary of dataset verification."""
    is_valid: bool = True
    total_tasks: int = 0
    splits_count: dict[str, int] = field(default_factory=dict)
    families_count: dict[str, int] = field(default_factory=dict)
    family_leaks: list[str] = field(default_factory=list)
    corrupted_bundles: list[str] = field(default_factory=list)
    failed_reference_solutions: list[str] = field(default_factory=list)
    prompt_leakage_warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class DatasetValidator:
    """Validates task schemas, family disjointness, test bundle integrity, and reference solutions."""

    def __init__(
        self,
        datasets_dir: Path | str | None = None,
        bundles_dir: Path | str | None = None,
        solutions_dir: Path | str | None = None,
    ):
        if datasets_dir is None:
            self.datasets_dir = Path(__file__).resolve().parents[2] / "datasets"
        else:
            self.datasets_dir = Path(datasets_dir)
        self.bundles_dir = Path(bundles_dir) if bundles_dir is not None else self.datasets_dir / "test_bundles"
        self.solutions_dir = Path(solutions_dir) if solutions_dir is not None else self.datasets_dir / "reference_solutions"

    def validate_family_disjointness(self, tasks: list[Task]) -> tuple[bool, list[str]]:
        """Verifies that task families are mutually exclusive across train, val, and test splits."""
        family_splits: dict[str, set[Split]] = {}
        for t in tasks:
            family_splits.setdefault(t.family_id, set()).add(t.split)

        leaks: list[str] = []
        for family_id, splits in family_splits.items():
            if len(splits) > 1:
                split_names = ", ".join(s.value for s in splits)
                leaks.append(f"Family '{family_id}' is shared across multiple splits: [{split_names}]")

        return len(leaks) == 0, leaks

    def verify_bundle_checksum(self, task: Task) -> bool:
        """Verifies that the test bundle exists and matches the recorded SHA-256 digest."""
        bundle_file = self.bundles_dir / f"{task.test_bundle_sha256}.json"
        if not bundle_file.exists():
            return False
        content = bundle_file.read_bytes()
        calculated_sha = hashlib.sha256(content).hexdigest()
        return calculated_sha == task.test_bundle_sha256

    def verify_reference_solution(
        self,
        task: Task,
        solution_code: str | None = None,
    ) -> tuple[bool, int, int, str]:
        """Executes a reference solution against its test bundle.
        
        Returns (passed_all, passed_count, total_count, error_message).
        """
        if solution_code is None:
            sol_file = self.solutions_dir / f"{task.task_id}.py"
            if not sol_file.exists():
                return False, 0, 0, f"Reference solution file not found: {sol_file.name}"
            solution_code = sol_file.read_text(encoding="utf-8")

        bundle_file = self.bundles_dir / f"{task.test_bundle_sha256}.json"
        if not bundle_file.exists():
            return False, 0, 0, f"Test bundle not found: {task.test_bundle_sha256}.json"

        bundle_data = json.loads(bundle_file.read_text(encoding="utf-8"))
        test_cases = bundle_data.get("test_cases", [])
        entry_point = bundle_data.get("entry_point", "")

        # Prepare isolated namespace for evaluation
        local_scope: dict[str, object] = {}
        try:
            exec(solution_code, local_scope)
        except Exception as err:
            return False, 0, len(test_cases), f"Solution execution error: {err}"

        if entry_point not in local_scope or not callable(local_scope[entry_point]):
            return False, 0, len(test_cases), f"Entry point '{entry_point}' not found in solution"

        target_func = local_scope[entry_point]
        passed = 0
        for idx, tc in enumerate(test_cases):
            inputs = tc.get("inputs", [])
            expected = tc.get("expected")
            try:
                actual = target_func(*inputs)
                if actual == expected:
                    passed += 1
                else:
                    return False, passed, len(test_cases), f"Test case {idx} failed: got {actual!r}, expected {expected!r}"
            except Exception as err:
                return False, passed, len(test_cases), f"Test case {idx} raised exception: {err}"

        return passed == len(test_cases), passed, len(test_cases), ""

    def validate_dataset(
        self,
        tasks: list[Task],
        solutions: dict[str, str] | None = None,
    ) -> ValidationReport:
        """Performs comprehensive validation of a dataset."""
        report = ValidationReport(total_tasks=len(tasks))

        # Check split counts
        for t in tasks:
            report.splits_count[t.split.value] = report.splits_count.get(t.split.value, 0) + 1
            report.families_count[t.family_id] = report.families_count.get(t.family_id, 0) + 1

        # 1. Family disjointness check
        disjoint, leaks = self.validate_family_disjointness(tasks)
        if not disjoint:
            report.is_valid = False
            report.family_leaks = leaks
            report.errors.extend(leaks)

        # 2. Bundle integrity and reference solution check
        for t in tasks:
            if not self.verify_bundle_checksum(t):
                report.is_valid = False
                err_msg = f"Task {t.task_id}: bundle {t.test_bundle_sha256} missing or checksum mismatch"
                report.corrupted_bundles.append(err_msg)
                report.errors.append(err_msg)
                continue

            sol = solutions.get(t.task_id) if solutions else None
            ok, passed, total, err = self.verify_reference_solution(t, sol)
            if not ok:
                report.is_valid = False
                err_msg = f"Task {t.task_id} reference solution failed ({passed}/{total}): {err}"
                report.failed_reference_solutions.append(err_msg)
                report.errors.append(err_msg)

            # 3. Prompt leakage check (check if expected answers or test bodies are in prompt)
            bundle_file = self.bundles_dir / f"{t.test_bundle_sha256}.json"
            if bundle_file.exists():
                bundle_data = json.loads(bundle_file.read_text(encoding="utf-8"))
                for tc in bundle_data.get("hidden_test_cases", []):
                    expected_str = str(tc.get("expected"))
                    if len(expected_str) > 10 and expected_str in t.prompt:
                        warn = f"Task {t.task_id}: possible prompt leakage of hidden test expected value"
                        report.prompt_leakage_warnings.append(warn)

        return report
