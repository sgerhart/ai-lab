"""Unit tests for dataset loading, bundle verification, and disjointness validation."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from packages.contracts import Split
from packages.datasets.task_loader import TaskLoader
from packages.datasets.validator import DatasetValidator


class TestDatasets(unittest.TestCase):
    """Verifies dataset manifest integrity, family-disjoint splits, and test bundles."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.base_dir = Path(__file__).resolve().parent.parent.parent
        cls.manifest_path = cls.base_dir / "datasets" / "manifests" / "dataset_v1.json"
        cls.bundles_dir = cls.base_dir / "datasets" / "test_bundles"
        cls.solutions_dir = cls.base_dir / "datasets" / "reference_solutions"

        cls.loader = TaskLoader(root_dir=cls.base_dir / "datasets")
        cls.tasks = cls.loader.load_tasks()
        cls.solutions = cls.loader.load_reference_solutions()
        cls.validator = DatasetValidator(bundles_dir=cls.bundles_dir)

    def test_load_tasks_and_solutions(self) -> None:
        """Verifies that the compiled dataset contains 105 tasks with 100% solutions."""
        self.assertEqual(len(self.tasks), 105)
        self.assertEqual(len(self.solutions), 105)

        train_tasks = [t for t in self.tasks if t.split == Split.TRAIN]
        val_tasks = [t for t in self.tasks if t.split == Split.VAL]
        test_tasks = [t for t in self.tasks if t.split == Split.TEST]

        self.assertEqual(len(train_tasks), 75)
        self.assertEqual(len(val_tasks), 15)
        self.assertEqual(len(test_tasks), 15)

    def test_family_disjointness_clean(self) -> None:
        """Verifies that train, val, and test splits have 0 overlapping family_ids."""
        is_disjoint, leaks = self.validator.validate_family_disjointness(self.tasks)
        self.assertTrue(is_disjoint, f"Unexpected family leaks found: {leaks}")
        self.assertEqual(len(leaks), 0)

    def test_family_leak_detection(self) -> None:
        """Verifies that an intentional cross-split family leak is caught by the validator."""
        # Find a train task and fabricate a duplicate with split=TEST
        sample_task = self.tasks[0]
        self.assertEqual(sample_task.split, Split.TRAIN)

        leaked_task = sample_task.model_copy(
            update={"task_id": "py-leak-999", "split": Split.TEST}
        )
        tampered_tasks = list(self.tasks) + [leaked_task]

        is_disjoint, leaks = self.validator.validate_family_disjointness(tampered_tasks)
        self.assertFalse(is_disjoint)
        self.assertGreater(len(leaks), 0)
        self.assertTrue(any(sample_task.family_id in msg for msg in leaks))

    def test_bundle_checksum_verification(self) -> None:
        """Verifies that bundle SHA-256 digests match actual file contents."""
        for task in self.tasks[:10]:
            self.assertTrue(
                self.validator.verify_bundle_checksum(task),
                f"Checksum mismatch for task {task.task_id}",
            )

        # Corrupted checksum test
        tampered_task = self.tasks[0].model_copy(
            update={"test_bundle_sha256": "0" * 64}
        )
        self.assertFalse(self.validator.verify_bundle_checksum(tampered_task))

    def test_comprehensive_validation_report(self) -> None:
        """Verifies that the full dataset passes validation with zero errors."""
        report = self.validator.validate_dataset(self.tasks, self.solutions)
        self.assertTrue(report.is_valid, f"Validation failed with errors: {report.errors}")
        self.assertEqual(report.total_tasks, 105)
        self.assertEqual(len(report.failed_reference_solutions), 0)
        self.assertEqual(len(report.corrupted_bundles), 0)
        self.assertEqual(len(report.family_leaks), 0)
        self.assertEqual(len(report.prompt_leakage_warnings), 0)

    def test_reference_solution_failure_on_corrupted_test_case(self) -> None:
        """Verifies that a tampered test case produces a failed reference solution report."""
        task = self.tasks[0]
        sol = self.solutions[task.task_id]

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_bundles = Path(tmp_dir)
            bundle_path = self.bundles_dir / f"{task.test_bundle_sha256}.json"
            bundle_content = json.loads(bundle_path.read_text(encoding="utf-8"))

            # Corrupt an expected output
            bundle_content["test_cases"][0]["expected"] = "__corrupted_sentinel_value__"
            corrupted_bundle_file = tmp_bundles / f"{task.test_bundle_sha256}.json"
            corrupted_bundle_file.write_text(json.dumps(bundle_content), encoding="utf-8")

            local_validator = DatasetValidator(bundles_dir=tmp_bundles)
            ok, passed, total, err = local_validator.verify_reference_solution(task, sol)
            self.assertFalse(ok)
            self.assertEqual(passed, 0)
            self.assertIn("failed", err)


if __name__ == "__main__":
    unittest.main()
