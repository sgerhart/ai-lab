"""Small Studio model comparison. Does not pull weights.

Scores a fixed set of general and coding fixtures against already-installed
Ollama tags. Coding answers run only if the source has no imports or file
access, inside a short Python subprocess with almost no builtins.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

BENCH_CTX = 4096
BENCH_PREDICT = 384
_CODE_FENCE = re.compile(r"```(?:python)?\s*\n(.*?)```", re.S | re.I)
_FORBIDDEN = re.compile(
    r"\b(import|exec|eval|open|compile|globals|locals|getattr|setattr|__)\b|os\.|subprocess\.",
    re.I,
)


def fixture_path() -> Path:
    return Path(__file__).resolve().parents[3] / "models" / "evaluations" / "fixtures" / "model-bench.jsonl"


def load_cases(path: Path | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in (path or fixture_path()).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def score_text(reply: str, expect: str) -> bool:
    text = (reply or "").strip().strip("`").strip().strip(".").lower()
    want = expect.strip().lower()
    if text == want:
        return True
    digits = re.sub(r"\D", "", text)
    return bool(want.isdigit() and digits == want)


def extract_source(reply: str) -> str:
    blocks = _CODE_FENCE.findall(reply or "")
    if blocks:
        return blocks[-1].strip()
    match = re.search(r"(def\s+\w+\s*\(.*\).*)", reply or "", re.S)
    return match.group(1).strip() if match else ""


def score_code(reply: str, name: str, calls: list[list[Any]], expect: list[Any]) -> tuple[bool, str]:
    source = extract_source(reply)
    if not source or f"def {name}" not in source:
        return False, "no function"
    if _FORBIDDEN.search(source):
        return False, "refused"
    payload = json.dumps({"source": source, "name": name, "calls": calls})
    runner = r"""
import json, sys
job = json.load(sys.stdin)
ns = {}
safe = {"range": range, "len": len, "str": str, "int": int, "bool": bool, "list": list, "True": True, "False": False, "None": None}
try:
    exec(compile(job["source"], "<bench>", "exec"), {"__builtins__": safe}, ns)
    fn = ns[job["name"]]
    print(json.dumps([fn(*args) for args in job["calls"]]))
except Exception as exc:
    print(json.dumps({"error": type(exc).__name__}))
"""
    proc = subprocess.run(
        [sys.executable, "-c", runner],
        input=payload,
        text=True,
        capture_output=True,
        timeout=3,
        check=False,
    )
    if proc.returncode != 0:
        return False, "runner failed"
    try:
        got = json.loads(proc.stdout.strip() or "null")
    except json.JSONDecodeError:
        return False, "bad runner output"
    if isinstance(got, dict):
        return False, str(got.get("error") or "error")
    return got == expect, "ok" if got == expect else f"got {got}"


def score_case(case: dict[str, Any], reply: str) -> dict[str, Any]:
    kind = case.get("kind")
    if kind == "code":
        ok, note = score_code(
            reply,
            str(case["function"]),
            list(case.get("calls") or []),
            list(case.get("expect") or []),
        )
    else:
        ok = score_text(reply, str(case.get("expect") or ""))
        note = "ok" if ok else "miss"
    return {"id": case["id"], "kind": kind, "ok": ok, "note": note}


def generate(base_url: str, model: str, prompt: str, *, keep_alive: str = "2m") -> dict[str, Any]:
    url = base_url.rstrip("/") + "/api/generate"
    body = json.dumps(
        {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "think": False,
            "keep_alive": keep_alive,
            "options": {"temperature": 0, "num_predict": BENCH_PREDICT, "num_ctx": BENCH_CTX},
        }
    ).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as resp:
        return json.loads(resp.read().decode())


def run_bench(base_url: str, models: list[str], cases: list[dict[str, Any]]) -> dict[str, Any]:
    reports: list[dict[str, Any]] = []
    for model in models:
        rows = []
        for case_index, case in enumerate(cases):
            unload = case_index == len(cases) - 1
            raw = generate(base_url, model, str(case["prompt"]), keep_alive="0" if unload else "2m")
            scored = score_case(case, str(raw.get("response") or ""))
            duration = raw.get("eval_duration") or 0
            count = raw.get("eval_count") or 0
            scored["tokens_per_sec"] = round(count / (duration / 1e9), 1) if duration else None
            rows.append(scored)
        passed = sum(1 for row in rows if row["ok"])
        reports.append(
            {
                "model": model,
                "passed": passed,
                "total": len(rows),
                "general": _tally(rows, "text"),
                "coding": _tally(rows, "code"),
                "cases": rows,
            }
        )
    return {
        "kind": "studio-model-bench",
        "context_tokens": BENCH_CTX,
        "note": "Short fixtures. A pass here is not a claim that one model replaces the coding profile.",
        "models": reports,
    }


def _tally(rows: list[dict[str, Any]], kind: str) -> str:
    picked = [row for row in rows if row["kind"] == kind]
    return f"{sum(1 for row in picked if row['ok'])}/{len(picked)}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare installed Studio models. Does not pull.")
    parser.add_argument("--ollama", default="http://127.0.0.1:11434")
    parser.add_argument("--model", action="append", dest="models")
    parser.add_argument("--apply", action="store_true", help="Call Ollama. Default prints the plan only.")
    parser.add_argument("--pull", action="store_true")
    args = parser.parse_args(argv)
    if args.pull:
        print("Refusing to pull weights.", file=sys.stderr)
        return 2
    models = args.models or ["qwen3.6:35b-a3b", "qwen3-coder:30b", "qwen3.8:27b"]
    cases = load_cases()
    if not args.apply:
        print(json.dumps({"apply": False, "ollama": args.ollama, "models": models, "cases": [c["id"] for c in cases]}, indent=2))
        return 0
    try:
        report = run_bench(args.ollama, models, cases)
    except urllib.error.URLError as exc:
        print(f"Ollama unreachable: {exc.reason}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
