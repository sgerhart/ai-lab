"""Harness-only eval dry-run. Does not pull weights and does not score a real model."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ai_lab_platform.model_catalog import load_catalog, refuse_pull
from ai_lab_platform.model_router import CompletionRequest, ModelRouter


def fixture_path() -> Path:
    return Path(__file__).resolve().parents[3] / "models" / "evaluations" / "fixtures" / "smoke.jsonl"


def load_fixture(path: Path | None = None) -> list[dict[str, str]]:
    target = path or fixture_path()
    rows: list[dict[str, str]] = []
    for line in target.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        item = json.loads(line)
        rows.append({"id": str(item["id"]), "prompt": str(item["prompt"]), "expect_contains": str(item["expect_contains"])})
    return rows


def run_dry_eval(*, model: str = "fake-instruct", backend: str = "ollama") -> dict[str, object]:
    catalog = load_catalog()
    router = ModelRouter()
    cases = load_fixture()
    results = []
    passed = 0
    for case in cases:
        response = router.complete(CompletionRequest(model=model, prompt=case["prompt"], backend=backend))
        ok = case["expect_contains"] in response.text
        passed += int(ok)
        results.append({"id": case["id"], "ok": ok, "text": response.text})
    return {
        "kind": "harness-smoke",
        "model_quality_claim": False,
        "pulled_models": catalog.get("models") or [],
        "passed": passed,
        "total": len(cases),
        "results": results,
        "note": "FakeBackend only. This is not an Ollama or MLX evaluation.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ai-lab eval dry-run (no pulls)")
    parser.add_argument("--pull", action="store_true", help="forbidden; always refused")
    parser.add_argument("--download", action="store_true", help="forbidden; always refused")
    args = parser.parse_args(argv)
    if args.pull or args.download:
        try:
            refuse_pull()
        except Exception as exc:
            print(str(exc), file=sys.stderr)
            return 2
    report = run_dry_eval()
    print(json.dumps(report, indent=2))
    return 0 if int(report["passed"]) == int(report["total"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
