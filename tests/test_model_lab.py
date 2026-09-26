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
from ai_lab_platform.model_catalog import (
    LocalModelUnavailable,
    PullRefused,
    find_installed_match,
    list_studio_choices,
    listed_ids,
    load_catalog,
    ollama_tag_matches,
    refuse_pull,
    require_local_available,
    resolve_profile,
    summarize_profiles,
)
from ai_lab_platform.model_router import CompletionRequest, DisabledCloudBackend, FakeBackend, ModelRouter
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
        profiles = data.get("profiles") or []
        self.assertGreaterEqual(len(profiles), 4)
        ids = {p["id"] for p in profiles}
        self.assertTrue({"general-local", "coding-local", "fast-local", "frontier-coding", "qwen36-local"} <= ids)
        self.assertEqual(data.get("default_profile"), "qwen36-local")

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


class ModelProfileTests(unittest.TestCase):
    def test_tag_match_variants(self) -> None:
        self.assertTrue(ollama_tag_matches("qwen3-coder:30b", "qwen3-coder:30b"))
        self.assertTrue(ollama_tag_matches("qwen3-coder:30b-a3b-q4_K_M", "qwen3-coder:30b"))
        self.assertTrue(ollama_tag_matches("llama3.2:3b", "llama3.2:3b"))
        self.assertFalse(ollama_tag_matches("llama3.2:3b", "qwen3-coder:30b"))

    def test_qwen36_is_default_when_mlx_tag_is_installed(self) -> None:
        data = load_catalog()
        self.assertEqual(data["default_profile"], "qwen36-local")
        r = resolve_profile("qwen36-local", installed_ollama=["qwen3.6:35b-a3b", "qwen3-coder:30b"])
        self.assertTrue(r.available)
        self.assertEqual(r.model, "qwen3.6:35b-a3b")
        coder = resolve_profile("coding-local", installed_ollama=["qwen3.6:35b-a3b", "qwen3-coder:30b"])
        self.assertEqual(coder.model, "qwen3-coder:30b")

    def test_role_assignment_overrides_catalog_tag(self) -> None:
        installed = ["qwen3.6:35b-a3b", "qwen3.8:27b", "qwen3-coder:30b", "llama3.2:3b"]
        roles = {"general-local": "qwen3.6:35b-a3b"}
        resolved = resolve_profile("general-local", installed_ollama=installed, roles=roles)
        self.assertEqual(resolved.model, "qwen3.6:35b-a3b")
        choices = list_studio_choices(installed, roles=roles)
        general = next(row for row in choices if "general-local" in (row.get("profile_ids") or []))
        self.assertEqual(general["model"], "qwen3.6:35b-a3b")

    def test_fast_local_available_when_installed(self) -> None:
        r = resolve_profile("fast-local", installed_ollama=["llama3.2:3b"])
        self.assertTrue(r.available)
        self.assertEqual(r.backend, "ollama")
        self.assertEqual(r.model, "llama3.2:3b")
        self.assertEqual(r.billing_class, "local")

    def test_coding_local_unavailable_without_install(self) -> None:
        r = resolve_profile("coding-local", installed_ollama=["llama3.2:3b"])
        self.assertFalse(r.available)
        self.assertEqual(r.reason, "not_installed_on_studio")
        with self.assertRaises(LocalModelUnavailable):
            require_local_available(r)

    def test_coding_local_matches_variant_tag(self) -> None:
        r = resolve_profile(
            "coding-local",
            installed_ollama=["qwen3-coder:30b-a3b-q4_K_M", "llama3.2:3b"],
        )
        self.assertTrue(r.available)
        self.assertEqual(r.model, "qwen3-coder:30b-a3b-q4_K_M")

    def test_frontier_unavailable_without_cloud(self) -> None:
        r = resolve_profile("frontier-coding", installed_ollama=[], cloud_enabled={"openai": False})
        self.assertFalse(r.available)
        self.assertEqual(r.billing_class, "usage_billed_api")

    def test_studio_choices_list_installed(self) -> None:
        choices = list_studio_choices(["llama3.2:3b", "custom:7b"])
        models = {c["model"] for c in choices}
        self.assertIn("llama3.2:3b", models)
        self.assertIn("custom:7b", models)
        fast = next(c for c in choices if c["model"] == "llama3.2:3b")
        self.assertEqual(fast["profile_id"], "fast-local")
        self.assertEqual(fast["billing_class"], "local")

    def test_summarize_profiles(self) -> None:
        rows = summarize_profiles(installed_ollama=["llama3.2:3b"], cloud_enabled={})
        by_id = {r["id"]: r for r in rows}
        self.assertTrue(by_id["fast-local"]["available"])
        self.assertFalse(by_id["coding-local"]["available"])

    def test_find_installed_match(self) -> None:
        self.assertEqual(
            find_installed_match(["qwen3.8:27b-mlx"], ["qwen3.8:27b", "qwen3.8:27b-mlx"]),
            "qwen3.8:27b-mlx",
        )

    def test_unavailable_local_does_not_invoke_cloud(self) -> None:
        """Selecting a missing local model must not call a paid backend."""
        cloud = DisabledCloudBackend("openai")
        router = ModelRouter(
            backends={"ollama": FakeBackend(), "openai": cloud},
            default_backend="ollama",
            allow_fallback=False,
        )
        resolved = resolve_profile("coding-local", installed_ollama=["llama3.2:3b"])
        with self.assertRaises(LocalModelUnavailable):
            require_local_available(resolved)
        # Explicitly still no cloud complete
        with self.assertRaises(PermissionError):
            router.complete(CompletionRequest(model="gpt-4.1", prompt="x", backend="openai"))


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
