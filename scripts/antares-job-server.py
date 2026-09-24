#!/usr/bin/env python3
"""Studio-side Antares job runner (FEAT-015 / IWO-049).

Listens for localize requests, runs `antares query` locally, stores reports.
Default bind 127.0.0.1; set AI_LAB_BIND_ADDRESS to Tailscale IPv4 for mini UI.
Never bind 0.0.0.0.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8002
HOME = Path.home()
RUNS_ROOT = HOME / ".ai-lab" / "antares" / "runs"
DEFAULT_REPO = HOME / ".ai-lab" / "antares" / "fixture-cwe78"
DEFAULT_PROFILE = "lab-antares-1b"
ANTARES_BIN = Path.home() / ".local" / "bin" / "antares"


def _allowed_repo(path: Path) -> bool:
    try:
        resolved = path.expanduser().resolve()
        root = (HOME / ".ai-lab" / "antares").resolve()
        resolved.relative_to(root)
        return True
    except (OSError, ValueError):
        return False


class JobStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._jobs: dict[str, dict[str, Any]] = {}
        RUNS_ROOT.mkdir(parents=True, exist_ok=True)

    def create(self, *, cwe: str, repo: Path, profile: str) -> dict[str, Any]:
        job_id = uuid.uuid4().hex[:12]
        out_dir = RUNS_ROOT / job_id
        out_dir.mkdir(parents=True, exist_ok=True)
        job = {
            "id": job_id,
            "status": "queued",
            "cwe": cwe,
            "repo": str(repo),
            "profile": profile,
            "output_dir": str(out_dir),
            "created_at": time.time(),
            "finished_at": None,
            "error": None,
            "findings": [],
            "summary": {},
        }
        with self._lock:
            self._jobs[job_id] = job
        threading.Thread(target=self._run, args=(job_id,), daemon=True).start()
        return dict(job)

    def get(self, job_id: str) -> dict[str, Any] | None:
        with self._lock:
            job = self._jobs.get(job_id)
            return dict(job) if job else None

    def list(self) -> list[dict[str, Any]]:
        with self._lock:
            return [dict(j) for j in sorted(self._jobs.values(), key=lambda x: x["created_at"], reverse=True)]

    def _update(self, job_id: str, **fields: Any) -> None:
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id].update(fields)

    def _run(self, job_id: str) -> None:
        job = self.get(job_id)
        if not job:
            return
        self._update(job_id, status="running")
        out_dir = Path(job["output_dir"])
        env = os.environ.copy()
        env["PATH"] = f"{HOME}/.local/bin:/opt/homebrew/bin:" + env.get("PATH", "")
        env.setdefault("ANTARES_ENDPOINT", "http://127.0.0.1:8001/v1/completions")
        env.setdefault("ANTARES_API_KEY", "local-no-auth")
        cmd = [
            str(ANTARES_BIN) if ANTARES_BIN.is_file() else "antares",
            "query",
            job["repo"],
            "--cwe",
            job["cwe"],
            "--profile",
            job["profile"],
            "--format",
            "json",
            "--output",
            str(out_dir),
        ]
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env,
                timeout=float(os.environ.get("ANTARES_JOB_TIMEOUT_SEC", "600")),
            )
            report = out_dir / "report.json"
            findings: list[Any] = []
            summary: dict[str, Any] = {}
            if report.is_file():
                data = json.loads(report.read_text(encoding="utf-8"))
                findings = list(data.get("findings") or [])
                summary = dict(data.get("summary") or {})
            if proc.returncode != 0 and not findings:
                self._update(
                    job_id,
                    status="failed",
                    finished_at=time.time(),
                    error=(proc.stderr or proc.stdout or f"exit {proc.returncode}")[-2000:],
                    findings=findings,
                    summary=summary,
                )
                return
            self._update(
                job_id,
                status="completed",
                finished_at=time.time(),
                findings=findings,
                summary=summary,
                error=None if proc.returncode == 0 else (proc.stderr or "")[-1000:],
            )
        except Exception as exc:  # noqa: BLE001
            self._update(job_id, status="failed", finished_at=time.time(), error=str(exc))


STORE = JobStore()


def make_handler(store: JobStore):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, fmt: str, *args: Any) -> None:
            sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

        def _json(self, code: int, body: Any) -> None:
            raw = json.dumps(body).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def _read_json(self) -> dict[str, Any]:
            n = int(self.headers.get("Content-Length") or "0")
            if n <= 0:
                return {}
            return json.loads(self.rfile.read(n).decode("utf-8"))

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            path = parsed.path
            if path in ("/health", "/v1/health"):
                completions_ok = False
                try:
                    import urllib.request

                    with urllib.request.urlopen("http://127.0.0.1:8001/health", timeout=2) as resp:
                        completions_ok = 200 <= getattr(resp, "status", 0) < 300
                except Exception:
                    completions_ok = False
                self._json(
                    200,
                    {
                        "ok": True,
                        "role": "antares-jobs",
                        "antares_bin": ANTARES_BIN.is_file(),
                        "completions_local": completions_ok,
                    },
                )
                return
            if path == "/v1/runs":
                self._json(200, {"runs": store.list()[:50]})
                return
            if path.startswith("/v1/runs/") and path.endswith("/report"):
                job_id = path.split("/")[3]
                job = store.get(job_id)
                if not job:
                    self._json(404, {"error": "not found"})
                    return
                qs = parse_qs(parsed.query)
                fmt = (qs.get("format") or ["json"])[0]
                ext = {"json": "report.json", "md": "report.md", "sarif": "report.sarif"}.get(fmt, "report.json")
                report = Path(job["output_dir"]) / ext
                if not report.is_file():
                    self._json(404, {"error": "report not ready", "status": job["status"]})
                    return
                raw = report.read_bytes()
                ctype = {
                    "report.json": "application/json",
                    "report.md": "text/markdown",
                    "report.sarif": "application/json",
                }.get(ext, "application/octet-stream")
                self.send_response(200)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
                return
            if path.startswith("/v1/runs/"):
                job_id = path.rstrip("/").split("/")[-1]
                job = store.get(job_id)
                if not job:
                    self._json(404, {"error": "not found"})
                    return
                self._json(200, job)
                return
            self._json(404, {"error": "not found"})

        def do_POST(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            if path != "/v1/runs":
                self._json(404, {"error": "not found"})
                return
            try:
                body = self._read_json()
            except json.JSONDecodeError:
                self._json(400, {"error": "invalid json"})
                return
            cwe = str(body.get("cwe") or "").strip()
            if not cwe.upper().startswith("CWE-"):
                self._json(400, {"error": "cwe required (e.g. CWE-78)"})
                return
            repo_s = str(body.get("repo") or DEFAULT_REPO).strip()
            repo = Path(repo_s).expanduser()
            if not repo.is_dir():
                self._json(400, {"error": f"repo not found: {repo}"})
                return
            if not _allowed_repo(repo):
                self._json(403, {"error": "repo must be under ~/.ai-lab/antares/"})
                return
            profile = str(body.get("profile") or DEFAULT_PROFILE).strip() or DEFAULT_PROFILE
            job = store.create(cwe=cwe, repo=repo, profile=profile)
            self._json(202, job)

    return Handler


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=os.environ.get("AI_LAB_BIND_ADDRESS", DEFAULT_HOST))
    parser.add_argument("--port", type=int, default=int(os.environ.get("ANTARES_JOB_PORT", DEFAULT_PORT)))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    if args.host in ("0.0.0.0", "::", "[::]"):
        print("refusing all-interfaces bind", file=sys.stderr)
        return 2
    print(f"host={args.host} port={args.port} runs={RUNS_ROOT}")
    if args.dry_run:
        print("dry-run: not starting")
        return 0
    server = ThreadingHTTPServer((args.host, args.port), make_handler(STORE))
    print(f"listening http://{args.host}:{args.port}/v1/runs", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("shutdown", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
