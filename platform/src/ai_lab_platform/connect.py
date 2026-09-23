"""Lab connect helpers — reachability probes; never return secret values."""

from __future__ import annotations

import json
import socket
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def port_open(host: str, port: int, timeout: float = 0.4) -> bool:
    sock = socket.socket()
    sock.settimeout(timeout)
    try:
        sock.connect((host, port))
        return True
    except OSError:
        return False
    finally:
        sock.close()


def http_probe(url: str, *, token: str = "", timeout: float = 0.8) -> dict[str, Any]:
    """Return {ok, status_code} without body secrets."""
    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"
    try:
        req = Request(url, headers=headers, method="GET")
        with urlopen(req, timeout=timeout) as resp:  # noqa: S310 — operator URLs
            return {"ok": 200 <= resp.status < 300, "status_code": resp.status}
    except HTTPError as exc:
        # Jupyter often returns 200 on /api with token; 403 without is "reachable"
        return {"ok": exc.code in {401, 403} or 200 <= exc.code < 500, "status_code": exc.code}
    except (URLError, OSError, ValueError):
        return {"ok": False, "status_code": None}


def read_token_file(path: str | Path) -> str:
    p = Path(path)
    if not p.is_file():
        return ""
    return p.read_text(encoding="utf-8").strip()


def jupyter_open_url(base_url: str, token: str) -> str:
    base = base_url.rstrip("/")
    if not token:
        return f"{base}/lab"
    return f"{base}/lab?token={token}"


def connect_status(
    *,
    jupyter_url: str,
    ollama_url: str,
    jupyter_token: str = "",
    studio_worker_url: str = "",
) -> dict[str, Any]:
    """Build a redacted connect status payload."""
    j_host, j_port = _host_port(jupyter_url, default_port=8888)
    o_host, o_port = _host_port(ollama_url, default_port=11434)

    jupyter_port = port_open(j_host, j_port) if j_host else False
    ollama_port = port_open(o_host, o_port) if o_host else False

    jupyter_http = {"ok": False, "status_code": None}
    if jupyter_url:
        jupyter_http = http_probe(f"{jupyter_url.rstrip('/')}/api", token=jupyter_token)

    ollama_http = {"ok": False, "status_code": None}
    if ollama_url:
        ollama_http = http_probe(f"{ollama_url.rstrip('/')}/api/tags")

    models: list[str] = []
    if ollama_http.get("ok"):
        try:
            req = Request(f"{ollama_url.rstrip('/')}/api/tags", method="GET")
            with urlopen(req, timeout=0.8) as resp:  # noqa: S310
                data = json.loads(resp.read().decode("utf-8"))
            models = [m.get("name", "") for m in data.get("models", []) if m.get("name")]
        except (URLError, OSError, ValueError, json.JSONDecodeError):
            models = []

    worker_ok = False
    if studio_worker_url:
        worker_ok = http_probe(f"{studio_worker_url.rstrip('/')}/health").get("ok", False)

    return {
        "ok": True,
        "jupyter": {
            "configured": bool(jupyter_url),
            "url_host": j_host,
            "port_open": jupyter_port,
            "http_ok": bool(jupyter_http.get("ok")),
            "token_configured": bool(jupyter_token),
        },
        "ollama": {
            "configured": bool(ollama_url),
            "url_host": o_host,
            "port_open": ollama_port,
            "http_ok": bool(ollama_http.get("ok")),
            "models": models,
        },
        "studio_worker": {"http_ok": worker_ok},
        "note": "Secret values are never included in this response.",
    }


def _host_port(url: str, *, default_port: int) -> tuple[str, int]:
    if not url:
        return "", default_port
    from urllib.parse import urlparse

    parsed = urlparse(url)
    host = parsed.hostname or ""
    port = parsed.port or default_port
    return host, port
