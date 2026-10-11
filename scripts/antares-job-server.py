#!/usr/bin/env python3
"""Studio-side Antares job runner (FEAT-015 / IWO-049).

Listens for localize requests, runs `antares query` locally, stores reports.
Default bind 127.0.0.1; set AI_LAB_BIND_ADDRESS to Tailscale IPv4 for mini UI.
Never bind 0.0.0.0.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import uuid
import urllib.error
import urllib.request
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
SNAPSHOTS = HOME / ".ai-lab" / "antares" / "snapshots"
_GITHUB_HTTPS = re.compile(r"^https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?$")
_GITHUB_SSH = re.compile(r"^git@github\.com:([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?$")


def parse_github_repo(url: str) -> tuple[str, str, str]:
    """A github.com repository, with no credential in the URL."""
    raw = (url or "").strip()
    if not raw or any(ch in raw for ch in (" ", "\n", "\t", "\\")):
        raise ValueError("repository URL is empty")
    if raw.startswith("https://") and "@" in raw.split("/", 3)[2]:
        raise ValueError("keep the GitHub credential on the Studio, not in the URL")
    match = _GITHUB_HTTPS.match(raw) or _GITHUB_SSH.match(raw)
    if match is None:
        raise ValueError("URL must be a github.com repository")
    owner, repo = match.group(1), match.group(2)
    if owner in {".", ".."} or repo in {".", ".."}:
        raise ValueError("URL must be a github.com repository")
    if raw.startswith("git@"):
        clone_url = f"git@github.com:{owner}/{repo}.git"
    else:
        clone_url = f"https://github.com/{owner}/{repo}.git"
    return owner, repo, clone_url


def snapshot_dir(owner: str, repo: str) -> Path:
    dest = (SNAPSHOTS / owner / repo).resolve()
    dest.relative_to(SNAPSHOTS.resolve())
    return dest


def refresh_snapshot(clone_url: str, dest: Path) -> None:
    """Replace the snapshot with a shallow clone. Submodules stay off."""
    root = SNAPSHOTS.resolve()
    dest = dest.resolve()
    dest.relative_to(root)
    SNAPSHOTS.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        ["git", "clone", "--depth", "1", "--no-recurse-submodules", "--", clone_url, str(dest)],
        capture_output=True,
        text=True,
        timeout=180,
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "git clone failed").strip().splitlines()
        raise RuntimeError(detail[-1][:300] if detail else "git clone failed")


def antares_command(*, repo: Path, out_dir: Path, cwe: str, profile: str) -> tuple[list[str], float]:
    """Named classes use query. A blank class uses sweep's automatic selection."""
    binary = str(ANTARES_BIN) if ANTARES_BIN.is_file() else "antares"
    named = (cwe or "").strip()
    if named:
        timeout = float(os.environ.get("ANTARES_JOB_TIMEOUT_SEC", "600"))
        return [
            binary,
            "query",
            str(repo),
            "--cwe",
            named,
            "--profile",
            profile,
            "--format",
            "json",
            "--output",
            str(out_dir),
        ], timeout
    workers = os.environ.get("ANTARES_SWEEP_WORKERS", "1")
    timeout = float(os.environ.get("ANTARES_SWEEP_TIMEOUT_SEC", "3600"))
    return [
        binary,
        "sweep",
        str(repo),
        "--scope",
        "auto",
        "--workers",
        workers,
        "--no-tui",
        "--report-format",
        "json",
        "--profile",
        profile,
        "--output",
        str(out_dir),
    ], timeout


def _allowed_repo(path: Path) -> bool:
    try:
        resolved = path.expanduser().resolve()
        root = (HOME / ".ai-lab" / "antares").resolve()
        resolved.relative_to(root)
        return True
    except (OSError, ValueError):
        return False


def _write_job(job: dict[str, Any]) -> None:
    """Keep a small record so a restart can still open a finished review."""
    job_id = str(job.get("id") or "")
    if not re.fullmatch(r"[a-f0-9]{8,32}", job_id) and not re.fullmatch(r"[A-Za-z0-9_-]{1,40}", job_id):
        return
    out = RUNS_ROOT / job_id
    out.mkdir(parents=True, exist_ok=True)
    saved = {key: job.get(key) for key in ("id", "status", "cwe", "repo", "profile", "mode", "source_url", "created_at", "finished_at", "error")}
    (out / "job.json").write_text(json.dumps(saved), encoding="utf-8")


def _saved_jobs() -> list[dict[str, Any]]:
    jobs = []
    if not RUNS_ROOT.is_dir():
        return jobs
    for child in RUNS_ROOT.iterdir():
        if not child.is_dir():
            continue
        record: dict[str, Any] = {}
        meta_path = child / "job.json"
        if meta_path.is_file():
            try:
                loaded = json.loads(meta_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                loaded = {}
            if isinstance(loaded, dict):
                record.update(loaded)
        report_path = child / "report.json"
        if report_path.is_file():
            try:
                report = json.loads(report_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                report = {}
            if isinstance(report, dict):
                record.setdefault("status", "completed")
                record["findings"] = list(report.get("findings") or [])
                record["summary"] = dict(report.get("summary") or {})
                if not record.get("repo"):
                    target = str((report.get("metadata") or {}).get("target") or "")
                    match = _snapshot_named(target)
                    if match is not None:
                        record["repo"] = str(match)
                        owner, name = match.parent.name, match.name
                        if not record.get("source_url"):
                            record["source_url"] = f"git@github.com:{owner}/{name}.git"
        if not record.get("id"):
            record["id"] = child.name
        record["output_dir"] = str(child)
        if not isinstance(record.get("created_at"), (int, float)):
            stamp = 0.0
            for candidate in (report_path, meta_path):
                if candidate.is_file():
                    stamp = candidate.stat().st_mtime
                    break
            record["created_at"] = stamp
        if record.get("repo"):
            jobs.append(record)
    return jobs


def _snapshot_named(name: str) -> Path | None:
    clean = (name or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,80}", clean) or clean in {".", ".."}:
        return None
    matches = [path for path in SNAPSHOTS.glob("*/*") if path.is_dir() and path.name == clean]
    if len(matches) != 1:
        return None
    return matches[0]


class JobStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._jobs: dict[str, dict[str, Any]] = {}
        RUNS_ROOT.mkdir(parents=True, exist_ok=True)
        for job in _saved_jobs():
            self._jobs[str(job["id"])] = job

    def create(
        self,
        *,
        cwe: str,
        repo: Path,
        profile: str,
        source_url: str = "",
        mode: str = "query",
    ) -> dict[str, Any]:
        job_id = uuid.uuid4().hex[:12]
        out_dir = RUNS_ROOT / job_id
        out_dir.mkdir(parents=True, exist_ok=True)
        job = {
            "id": job_id,
            "status": "queued",
            "cwe": cwe,
            "repo": str(repo),
            "profile": profile,
            "mode": mode,
            "source_url": source_url,
            "output_dir": str(out_dir),
            "created_at": time.time(),
            "finished_at": None,
            "error": None,
            "findings": [],
            "summary": {},
        }
        with self._lock:
            self._jobs[job_id] = job
        _write_job(job)
        threading.Thread(target=self._run, args=(job_id,), daemon=True).start()
        return dict(job)

    def get(self, job_id: str) -> dict[str, Any] | None:
        with self._lock:
            job = self._jobs.get(job_id)
            return dict(job) if job else None

    def list(self) -> list[dict[str, Any]]:
        with self._lock:
            rows = [dict(job) for job in self._jobs.values()]
        rows.sort(key=lambda job: float(job.get("created_at") or 0), reverse=True)
        return rows

    def _update(self, job_id: str, **fields: Any) -> None:
        with self._lock:
            if job_id not in self._jobs:
                return
            self._jobs[job_id].update(fields)
            saved = dict(self._jobs[job_id])
        _write_job(saved)

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
        if job.get("source_url"):
            try:
                refresh_snapshot(str(job["source_url"]), Path(job["repo"]))
            except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as exc:
                self._update(job_id, status="failed", finished_at=time.time(), error=str(exc)[:500])
                return
        cmd, timeout = antares_command(
            repo=Path(job["repo"]),
            out_dir=out_dir,
            cwe=str(job.get("cwe") or ""),
            profile=str(job["profile"]),
        )
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env,
                timeout=timeout,
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


def _host_report() -> dict[str, Any]:
    """Local chip, memory, and disk for the status dashboard. No addresses."""
    root = Path(__file__).resolve().parents[1]
    src = root / "platform" / "src"
    sibling = Path(__file__).resolve().parent / "host_resources.py"
    if src.is_dir():
        sys.path.insert(0, str(src))
        from ai_lab_platform.host_resources import collect
    elif sibling.is_file():
        import importlib.util

        spec = importlib.util.spec_from_file_location("ai_lab_host_resources", sibling)
        if spec is None or spec.loader is None:
            return {"available": False, "reason": "This machine did not report memory or disk."}
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        collect = module.collect
    else:
        return {"available": False, "reason": "This machine did not report memory or disk."}
    return collect()


def paths_present(repo: Path, paths: list[Any]) -> dict[str, bool]:
    """Which cited paths are files inside the snapshot. No file contents."""
    root = repo.resolve()
    present: dict[str, bool] = {}
    for raw in paths[:200]:
        key = str(raw or "")
        rel = key.strip().replace("\\", "/")
        parts = [part for part in rel.split("/") if part and part != "."]
        if not rel or rel.startswith("/") or rel.startswith("~") or any(part == ".." for part in parts):
            present[key] = False
            continue
        dest = (root.joinpath(*parts)).resolve()
        try:
            dest.relative_to(root)
        except ValueError:
            present[key] = False
            continue
        present[key] = dest.is_file()
    return present


def _handoff_module():
    candidates = [
        Path(__file__).resolve().with_name("antares_handoff.py"),
        Path(__file__).resolve().parents[1] / "platform" / "src" / "ai_lab_platform" / "antares_handoff.py",
    ]
    for path in candidates:
        if not path.is_file():
            continue
        spec = importlib.util.spec_from_file_location("antares_handoff", path)
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    raise RuntimeError("antares handoff module is not installed")


def _detail_record(job_id: str) -> dict[str, Any]:
    path = RUNS_ROOT / job_id / "detail.json"
    if not path.is_file():
        return {"status": "pending", "done": 0, "total": 0, "findings": []}
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"status": "failed", "done": 0, "total": 0, "findings": [], "error": "detail record could not be read"}
    return loaded if isinstance(loaded, dict) else {"status": "failed", "done": 0, "total": 0, "findings": []}


def _write_detail(job_id: str, body: dict[str, Any]) -> None:
    path = RUNS_ROOT / job_id / "detail.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body), encoding="utf-8")


_detail_running: set[str] = set()


def _start_detail(store: JobStore, job_id: str) -> dict[str, Any]:
    current = _detail_record(job_id)
    if current.get("status") in {"running", "completed"} or job_id in _detail_running:
        return current
    job = store.get(job_id)
    if not job or job.get("status") != "completed":
        return {"status": "pending", "done": 0, "total": 0, "findings": [], "error": "the Antares review is not finished"}
    _detail_running.add(job_id)
    threading.Thread(target=_run_detail, args=(store, job_id), daemon=True).start()
    return {"status": "running", "done": 0, "total": len(job.get("findings") or []), "findings": []}


def _run_detail(store: JobStore, job_id: str) -> None:
    try:
        job = store.get(job_id) or {}
        findings = [row for row in (job.get("findings") or []) if isinstance(row, dict)]
        repo = Path(str(job.get("repo") or ""))
        module = _detail_module()
        model = os.environ.get("ANTARES_DETAIL_MODEL", "llama3.2:3b")
        done: list[dict[str, Any]] = []
        record = {"status": "running", "done": 0, "total": len(findings), "model": model, "findings": []}
        _write_detail(job_id, record)
        for finding in findings:
            path = str(finding.get("file_path") or "")
            cwes = finding.get("cwe_ids") if isinstance(finding.get("cwe_ids"), list) else []
            cwe = str(cwes[0]) if cwes else ""
            title = str(finding.get("title") or "")
            text = _snapshot_text(repo, path)
            if text is None:
                row = {"file_path": path, "cwe": cwe, "title": title, "verdict": "rejected", "line": None, "reason": "The cited path is not a file in the snapshot."}
            else:
                excerpt, count = module.numbered_excerpt(text)
                try:
                    reply = _ollama_generate(model, module.review_prompt(path=path, cwe=cwe, title=title, excerpt=excerpt))
                    parsed = module.parse_review(reply, line_count=min(count, 160))
                except urllib.error.URLError:
                    raise
                except (OSError, TimeoutError, json.JSONDecodeError, RuntimeError) as exc:
                    parsed = {"verdict": "uncertain", "line": None, "reason": str(exc)[:180] or "The reviewer did not answer."}
                row = {"file_path": path, "cwe": cwe, "title": title, **parsed}
            done.append(row)
            record = {"status": "running", "done": len(done), "total": len(findings), "model": model, "findings": []}
            _write_detail(job_id, record)
        _write_detail(job_id, {"status": "completed", "done": len(done), "total": len(findings), "model": model, "findings": done})
    except Exception as exc:  # noqa: BLE001
        _write_detail(job_id, {"status": "failed", "done": 0, "total": 0, "findings": [], "error": str(exc)[:300]})
    finally:
        _detail_running.discard(job_id)


def _ollama_generate(model: str, prompt: str) -> str:
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False, "options": {"temperature": 0, "num_predict": 180}}).encode()
    req = urllib.request.Request(
        "http://127.0.0.1:11434/api/generate",
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    if not isinstance(body, dict):
        raise RuntimeError("the reviewer did not answer")
    return str(body.get("response") or "")


def _snapshot_text(repo: Path, raw: str) -> str | None:
    rel = raw.strip().replace("\\", "/")
    parts = [part for part in rel.split("/") if part and part != "."]
    if not rel or rel.startswith("/") or any(part == ".." for part in parts):
        return None
    dest = (repo.resolve().joinpath(*parts)).resolve()
    try:
        dest.relative_to(repo.resolve())
    except ValueError:
        return None
    if not dest.is_file():
        return None
    return dest.read_text(encoding="utf-8", errors="replace")[:200_000]


def _detail_module():
    candidates = [
        Path(__file__).resolve().with_name("antares_detail.py"),
        Path(__file__).resolve().parents[1] / "platform" / "src" / "ai_lab_platform" / "antares_detail.py",
    ]
    for path in candidates:
        if not path.is_file():
            continue
        spec = importlib.util.spec_from_file_location("antares_detail", path)
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    raise RuntimeError("detail review module is not installed")


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
            if path == "/resources":
                self._json(200, _host_report())
                return
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
            if path.startswith("/v1/runs/") and path.endswith("/detail"):
                job_id = path.split("/")[3]
                if not store.get(job_id):
                    self._json(404, {"error": "not found"})
                    return
                self._json(200, _detail_record(job_id))
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
                report = Path(job.get("output_dir") or (RUNS_ROOT / job_id)) / ext
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
            presence = re.fullmatch(r"/v1/runs/([a-f0-9]{8,32})/presence", path)
            if presence:
                job = store.get(presence.group(1))
                if not job:
                    self._json(404, {"error": "not found"})
                    return
                try:
                    body = self._read_json()
                except json.JSONDecodeError:
                    self._json(400, {"error": "invalid json"})
                    return
                paths = body.get("paths")
                if not isinstance(paths, list):
                    self._json(400, {"error": "paths must be a list"})
                    return
                self._json(200, {"present": paths_present(Path(job["repo"]), paths)})
                return
            detail = re.fullmatch(r"/v1/runs/([a-f0-9]{8,32})/detail", path)
            if detail:
                job_id = detail.group(1)
                if not store.get(job_id):
                    self._json(404, {"error": "not found"})
                    return
                self._json(202, _start_detail(store, job_id))
                return
            audit = re.fullmatch(r"/v1/runs/([a-f0-9]{8,32})/audit", path)
            if audit:
                job = store.get(audit.group(1))
                if not job:
                    self._json(404, {"error": "not found"})
                    return
                if int(self.headers.get("Content-Length") or "0") > 2_000_000:
                    self._json(413, {"error": "audit payload is too large"})
                    return
                try:
                    body = self._read_json()
                    published = _handoff_module().publish_audit(
                        Path(job["repo"]),
                        body,
                        today=time.strftime("%Y-%m-%d"),
                    )
                    if body.get("push") and not published.get("already_recorded"):
                        published.update(
                            _handoff_module().commit_audit(
                                Path(job["repo"]),
                                list(published.get("files") or []),
                                branch=str(published.get("branch") or ""),
                                message=(
                                    "Record an Antares security audit as draft work orders.\n\n"
                                    "The leads are not confirmed. Product code stays unchanged until a person accepts an order."
                                ),
                                push=True,
                            )
                        )
                except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as exc:
                    self._json(400, {"error": str(exc)[:300]})
                    return
                self._json(200, published)
                return
            if path != "/v1/runs":
                self._json(404, {"error": "not found"})
                return
            try:
                body = self._read_json()
            except json.JSONDecodeError:
                self._json(400, {"error": "invalid json"})
                return
            cwe_raw = str(body.get("cwe") or "").strip()
            parts = [part.strip() for part in cwe_raw.split(",") if part.strip()]
            if any(not part.upper().startswith("CWE-") for part in parts):
                self._json(400, {"error": "cwe must look like CWE-78, or be left blank"})
                return
            cwe = ",".join(parts)
            repo_url = str(body.get("repo_url") or "").strip()
            source_url = ""
            if repo_url:
                try:
                    owner, name, clone_url = parse_github_repo(repo_url)
                    repo = snapshot_dir(owner, name)
                except ValueError as exc:
                    self._json(400, {"error": str(exc)})
                    return
                source_url = clone_url
            else:
                repo_s = str(body.get("repo") or DEFAULT_REPO).strip()
                repo = Path(repo_s).expanduser()
                if not repo.is_dir():
                    self._json(400, {"error": f"repo not found: {repo}"})
                    return
                if not _allowed_repo(repo):
                    self._json(403, {"error": "repo must be under ~/.ai-lab/antares/"})
                    return
            profile = str(body.get("profile") or DEFAULT_PROFILE).strip() or DEFAULT_PROFILE
            job = store.create(
                cwe=cwe,
                repo=repo,
                profile=profile,
                source_url=source_url,
                mode="sweep" if not cwe else "query",
            )
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
    store = JobStore()
    server = ThreadingHTTPServer((args.host, args.port), make_handler(store))
    print(f"listening http://{args.host}:{args.port}/v1/runs", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("shutdown", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
