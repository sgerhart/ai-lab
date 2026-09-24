"""Minimal HTTP client for the ai-lab control plane (FEAT-005 / IWO-042)."""

from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class LabApiError(RuntimeError):
    def __init__(self, message: str, *, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


class LabApiClient:
    """Bearer-authenticated JSON client for the mini control plane."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        token: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = (base_url or os.environ.get("AI_LAB_API_BASE") or "http://127.0.0.1:8088").rstrip(
            "/"
        )
        self.token = (
            token
            if token is not None
            else os.environ.get("AI_LAB_API_TOKEN", "").strip()
        )
        self.timeout = timeout

    def _headers(self, *, auth: bool = True) -> dict[str, str]:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if auth and self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def request(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, Any] | None = None,
        auth: bool = True,
    ) -> Any:
        data = None if body is None else json.dumps(body).encode("utf-8")
        url = f"{self.base_url}{path}"
        req = Request(url, data=data, headers=self._headers(auth=auth), method=method)
        try:
            with urlopen(req, timeout=self.timeout) as resp:  # noqa: S310 — operator URL
                raw = resp.read().decode("utf-8")
                status = getattr(resp, "status", 200)
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise LabApiError(f"HTTP {exc.code}: {detail[:500]}", status=exc.code) from exc
        except URLError as exc:
            raise LabApiError(f"unreachable: {exc}") from exc
        if not raw:
            return {"ok": True, "status": status}
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"raw": raw, "status": status}

    def get(self, path: str, *, auth: bool = True) -> Any:
        return self.request("GET", path, auth=auth)

    def post(self, path: str, body: dict[str, Any] | None = None, *, auth: bool = True) -> Any:
        return self.request("POST", path, body=body or {}, auth=auth)


__all__ = ["LabApiClient", "LabApiError"]
