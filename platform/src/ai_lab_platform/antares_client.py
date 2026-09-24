"""Client helpers for Studio Antares job + completions servers (IWO-049)."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any


class AntaresStudioClient:
    def __init__(
        self,
        *,
        job_url: str = "",
        completions_url: str = "",
        timeout_sec: float = 30.0,
    ) -> None:
        self.job_url = (job_url or "").rstrip("/")
        self.completions_url = (completions_url or "").rstrip("/")
        self.timeout_sec = timeout_sec

    def configured(self) -> bool:
        return bool(self.job_url)

    def _get(self, url: str) -> tuple[int, Any]:
        req = urllib.request.Request(url, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_sec) as resp:
                raw = resp.read()
                ctype = resp.headers.get("Content-Type", "")
                if "json" in ctype or raw[:1] in (b"{", b"["):
                    return resp.status, json.loads(raw.decode("utf-8"))
                return resp.status, raw.decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            try:
                return exc.code, json.loads(body)
            except json.JSONDecodeError:
                return exc.code, {"error": body}
        except Exception as exc:  # noqa: BLE001
            return 503, {"error": str(exc)}

    def _post_json(self, url: str, payload: dict[str, Any]) -> tuple[int, Any]:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_sec) as resp:
                return resp.status, json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            try:
                return exc.code, json.loads(body)
            except json.JSONDecodeError:
                return exc.code, {"error": body}
        except Exception as exc:  # noqa: BLE001
            return 503, {"error": str(exc)}

    def status(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "job_url": self.job_url or None,
            "completions_url": self.completions_url or None,
            "configured": self.configured(),
            "jobs": None,
            "completions": None,
        }
        if self.job_url:
            code, body = self._get(f"{self.job_url}/health")
            out["jobs"] = {"http": code, "body": body}
            # Completions stay on Studio loopback; job helper reports local health.
            if isinstance(body, dict) and body.get("completions_local") is not None:
                out["completions"] = {
                    "http": 200 if body.get("completions_local") else 503,
                    "body": {"ok": bool(body.get("completions_local")), "via": "antares-jobs"},
                }
        if self.completions_url and out["completions"] is None:
            code, body = self._get(f"{self.completions_url}/health")
            out["completions"] = {"http": code, "body": body}
        return out

    def start_run(self, *, cwe: str, repo: str = "", profile: str = "") -> tuple[int, Any]:
        if not self.job_url:
            return 503, {"error": "ANTARES_JOB_URL not configured on control plane"}
        payload: dict[str, Any] = {"cwe": cwe}
        if repo:
            payload["repo"] = repo
        if profile:
            payload["profile"] = profile
        return self._post_json(f"{self.job_url}/v1/runs", payload)

    def list_runs(self) -> tuple[int, Any]:
        if not self.job_url:
            return 503, {"error": "ANTARES_JOB_URL not configured on control plane"}
        return self._get(f"{self.job_url}/v1/runs")

    def get_run(self, run_id: str) -> tuple[int, Any]:
        if not self.job_url:
            return 503, {"error": "ANTARES_JOB_URL not configured on control plane"}
        return self._get(f"{self.job_url}/v1/runs/{run_id}")

    def get_report(self, run_id: str, fmt: str = "json") -> tuple[int, Any]:
        if not self.job_url:
            return 503, {"error": "ANTARES_JOB_URL not configured on control plane"}
        return self._get(f"{self.job_url}/v1/runs/{run_id}/report?format={fmt}")
