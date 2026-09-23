"""Model catalog, pull refusal, and harness-only eval dry-run."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.eval_dry_run import main as eval_main, run_dry_eval
from ai_lab_platform.model_catalog import PullRefused, listed_ids, load_catalog, refuse_pull
from ai_lab_platform.train_refuse import main as train_main


class ModelCatalogTests(unittest.TestCase):
    def test_catalog_entries_are_honest(self) -> None:
        data = load_catalog()
        self.assertEqual(data["schema_version"], 1)
        self.assertIn("No automatic pulls", data["policy"])
        for model in data["models"]:
            self.assertNotEqual(model.get("status"), "pulled")
            self.assertFalse(model.get("pull_authorized"))
        # Git may list catalogued models; weights stay off-repo.
        self.assertEqual(set(listed_ids()), {m["id"] for m in data["models"]})

    def test_refuse_pull(self) -> None:
        with self.assertRaises(PullRefused):
            refuse_pull("anything")

    def test_rejects_git_claiming_a_pull(self) -> None:
        path = Path(tempfile.mkdtemp()) / "catalog.json"
        path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "models": [
                        {"id": "secret-slm", "status": "pulled", "pull_authorized": False},
                    ],
                }
            ),
            encoding="utf-8",
        )
        with self.assertRaises(ValueError):
            load_catalog(path)

    def test_rejects_authorized_flag_in_git_catalog(self) -> None:
        path = Path(tempfile.mkdtemp()) / "catalog.json"
        path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "models": [{"id": "x", "status": "catalogued-not-pulled", "pull_authorized": True}],
                }
            ),
            encoding="utf-8",
        )
        with self.assertRaises(ValueError):
            load_catalog(path)


class EvalDryRunTests(unittest.TestCase):
    def test_harness_smoke_is_not_a_model_claim(self) -> None:
        report = run_dry_eval()
        self.assertFalse(report["model_quality_claim"])
        self.assertEqual(report["kind"], "harness-smoke")
        self.assertEqual(report["passed"], report["total"])
        self.assertGreaterEqual(int(report["total"]), 1)

    def test_cli_refuses_pull(self) -> None:
        self.assertEqual(eval_main(["--pull"]), 2)
        self.assertEqual(eval_main(["--download"]), 2)

    def test_cli_dry_run_ok(self) -> None:
        self.assertEqual(eval_main([]), 0)


class TrainRefuseTests(unittest.TestCase):
    def test_train_entrypoint_refuses(self) -> None:
        self.assertEqual(train_main([]), 2)
        self.assertEqual(train_main(["--start"]), 2)
        self.assertEqual(train_main(["--download-dataset"]), 2)


if __name__ == "__main__":
    unittest.main()
