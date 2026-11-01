"""Unit tests for BaselineEvaluator, prompt safety, and holdout baseline reports."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from packages.contracts import (
    BaselineReport,
    FailureClass,
    GenerationConfig,
    Split,
)
from packages.datasets.task_loader import TaskLoader
from packages.evaluation.baseline import BaselineEvaluator, format_task_prompt
from services.model.backend import MockModelBackend
from services.sandbox_worker import MockSandboxBackend, SandboxWorker


class TestBaselineEvaluator(unittest.TestCase):
    """Verifies baseline evaluation mechanics, deterministic metrics, and prompt safety."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.datasets_dir = Path(__file__).resolve().parents[2] / "datasets"
        cls.task_loader = TaskLoader(cls.datasets_dir)
        cls.ref_solutions = cls.task_loader.load_reference_solutions()

    def test_format_task_prompt_zero_test_disclosure(self) -> None:
        """Mandatory Invariant: Evaluation prompts must NEVER leak test vectors or bundle assertions."""
        tasks = self.task_loader.load_tasks()
        self.assertGreater(len(tasks), 0)

        for task in tasks[:10]:
            prompt = format_task_prompt(task)
            # Invariant checks
            self.assertIn("def ", prompt)
            self.assertIn(task.function_contract, prompt)
            self.assertNotIn("test_bundle", prompt)
            self.assertNotIn(task.test_bundle_sha256, prompt)
            self.assertNotIn("assert ", prompt)
            self.assertNotIn("self.assertEqual", prompt)

    def test_evaluate_task_syntax_error_short_circuit(self) -> None:
        """Syntax errors must produce COMPILE_ERROR without sending execution to sandbox."""
        bad_backend = MockModelBackend(
            generator_fn=lambda prompt, seed, cfg: "```python\ndef broken(\n    return 42\n```"
        )
        evaluator = BaselineEvaluator(
            model_backend=bad_backend,
            sandbox_backend=MockSandboxBackend(),
            task_loader=self.task_loader,
        )
        task = self.task_loader.load_tasks()[0]
        res = evaluator.evaluate_task(task)

        self.assertFalse(res.syntax_valid)
        self.assertFalse(res.passed)
        self.assertEqual(res.reward, 0.0)
        self.assertEqual(res.error_class, FailureClass.SYNTAX_ERROR)

    def test_evaluate_split_with_mock_backend(self) -> None:
        """Evaluates validation split with default mock model (dummy returns None)."""
        evaluator = BaselineEvaluator(
            model_backend=MockModelBackend(),
            sandbox_backend=MockSandboxBackend(),
            task_loader=self.task_loader,
        )
        metrics, results = evaluator.evaluate_split(Split.VAL)

        self.assertEqual(metrics.split, Split.VAL)
        self.assertEqual(metrics.total_tasks, 15)
        self.assertEqual(metrics.evaluated_tasks, 15)
        self.assertIsInstance(metrics.pass_at_1, float)
        self.assertIsInstance(metrics.mean_reward, float)
        self.assertEqual(len(results), 15)

    def test_reference_solutions_holdout_100_percent_pass(self) -> None:
        """Ground-Truth Verification: Reference solutions must achieve 100% pass@1 on holdout splits."""
        model_backend = MockModelBackend(task_solutions=self.ref_solutions)
        sandbox_worker = SandboxWorker(
            bundles_dir=self.datasets_dir / "test_bundles",
            enforce_execution_flag=False,
        )
        evaluator = BaselineEvaluator(
            model_backend=model_backend,
            sandbox_backend=sandbox_worker,
            task_loader=self.task_loader,
            model_id="reference-solutions",
            model_revision="v1.0",
        )

        # 1. Evaluate validation split (15 tasks)
        val_metrics, val_results = evaluator.evaluate_split(Split.VAL)
        self.assertEqual(val_metrics.total_tasks, 15)
        self.assertEqual(val_metrics.passed_tasks, 15)
        self.assertEqual(val_metrics.pass_at_1, 1.0)
        self.assertEqual(val_metrics.mean_reward, 1.0)
        self.assertEqual(val_metrics.compile_errors, 0)
        self.assertEqual(val_metrics.runtime_errors, 0)

        # 2. Evaluate test split (15 tasks)
        test_metrics, test_results = evaluator.evaluate_split(Split.TEST)
        self.assertEqual(test_metrics.total_tasks, 15)
        self.assertEqual(test_metrics.passed_tasks, 15)
        self.assertEqual(test_metrics.pass_at_1, 1.0)
        self.assertEqual(test_metrics.mean_reward, 1.0)
        self.assertEqual(test_metrics.compile_errors, 0)
        self.assertEqual(test_metrics.runtime_errors, 0)

    def test_baseline_report_export_and_json_structure(self) -> None:
        """Verifies report generation, metadata serialization, and round-trip JSON deserialization."""
        model_backend = MockModelBackend(task_solutions=self.ref_solutions)
        sandbox_backend = MockSandboxBackend()
        evaluator = BaselineEvaluator(
            model_backend=model_backend,
            sandbox_backend=sandbox_backend,
            task_loader=self.task_loader,
            model_id="test-model",
            model_revision="rev-001",
        )

        report = evaluator.evaluate_holdout(
            splits=[Split.VAL, Split.TEST],
            generation_config=GenerationConfig(seed=123),
            seed=123,
            metadata={"environment": "unit-test"},
        )

        self.assertIsInstance(report, BaselineReport)
        self.assertEqual(report.model_id, "test-model")
        self.assertEqual(report.model_revision, "rev-001")
        self.assertIn("val", report.splits)
        self.assertIn("test", report.splits)
        self.assertEqual(len(report.results), 30)  # 15 val + 15 test

        # Export and verify JSON round-trip
        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = Path(tmpdir) / "baseline_report.json"
            exported = evaluator.export_report(report, out_file)
            self.assertTrue(exported.exists())

            raw_data = json.loads(exported.read_text(encoding="utf-8"))
            reloaded = BaselineReport(**raw_data)
            self.assertEqual(reloaded.report_id, report.report_id)
            self.assertEqual(reloaded.dataset_hash, report.dataset_hash)
            self.assertEqual(reloaded.global_pass_at_1, report.global_pass_at_1)
