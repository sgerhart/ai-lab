"""Status dashboard payload. Counts and reachability only — no secrets or addresses."""

from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

_RESOURCE_INTS = (
    "cpu_count",
    "memory_bytes",
    "memory_free_percent",
    "disk_bytes",
    "disk_free_bytes",
)


def sanitize_resources(raw: Any, *, reason: str) -> dict[str, Any]:
    """Keep a host snapshot that is safe to render. Drop anything else."""
    if not isinstance(raw, dict) or not raw.get("available"):
        return {"available": False, "reason": reason}
    chip = raw.get("chip")
    out: dict[str, Any] = {
        "available": True,
        "chip": chip if isinstance(chip, str) and len(chip) <= 80 else None,
    }
    for key in _RESOURCE_INTS:
        value = raw.get(key)
        out[key] = value if isinstance(value, int) and value >= 0 else None
    percent = out.get("memory_free_percent")
    if isinstance(percent, int) and percent > 100:
        out["memory_free_percent"] = None
    return out


def fetch_remote_resources(base_url: str, *, timeout: float = 1.2) -> dict[str, Any]:
    """GET {base}/resources from a lab host that already reports to the mini."""
    reason = "Studio has not reported memory or disk yet."
    parsed = urlparse(base_url or "")
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username:
        return {"available": False, "reason": reason}
    url = f"{parsed.scheme}://{parsed.netloc}/resources"
    try:
        req = Request(url, method="GET")
        with urlopen(req, timeout=timeout) as resp:  # noqa: S310 — operator URL from settings
            body = json.loads(resp.read().decode("utf-8"))
    except (HTTPError, URLError, OSError, ValueError, json.JSONDecodeError, TimeoutError):
        return {"available": False, "reason": reason}
    return sanitize_resources(body, reason=reason)


def build_lab_dashboard(
    *,
    mini_resources: dict[str, Any],
    services: dict[str, bool],
    connect: dict[str, Any],
    studio_resources: dict[str, Any],
    memory: dict[str, Any],
    scheduler_last_tick: str | None,
    antares_jobs_up: bool,
    antares_completions_up: bool,
    frontier_configured: int,
    frontier_authorized: bool,
    mcp_servers: list[dict[str, Any]],
    local_models: list[dict[str, Any]],
) -> dict[str, Any]:
    ollama = connect.get("ollama") if isinstance(connect.get("ollama"), dict) else {}
    jupyter = connect.get("jupyter") if isinstance(connect.get("jupyter"), dict) else {}
    worker = connect.get("studio_worker") if isinstance(connect.get("studio_worker"), dict) else {}
    ollama_up = bool(ollama.get("http_ok"))
    jupyter_up = bool(jupyter.get("http_ok") or jupyter.get("port_open"))
    installed = [row for row in (ollama.get("installed") or []) if isinstance(row, dict)]
    loaded = [row for row in (ollama.get("loaded") or []) if isinstance(row, dict)]
    ready_models = [row for row in local_models if row.get("available") and row.get("model")]

    modules = [
        _chat_module(ollama_up, ready_models),
        _module(
            "jupyter",
            "Jupyter",
            "ready" if jupyter_up else "off",
            "Notebooks on the Studio." if jupyter_up else "Studio notebooks are not reachable.",
            "jupyter" if jupyter_up else "",
        ),
        _module("agents", "Agents Studio", "ready", "Build and run agents here.", "agents"),
        _memory_module(memory),
        _frontier_module(frontier_configured, frontier_authorized),
        _mcp_module(mcp_servers),
        _module(
            "scheduler",
            "Scheduler",
            "ready" if scheduler_last_tick else "limited",
            f"Last tick {scheduler_last_tick}." if scheduler_last_tick else "No tick has been recorded yet.",
            "",
        ),
        _antares_module(antares_jobs_up, antares_completions_up),
    ]
    return {
        "ok": True,
        "hosts": {
            "mini": {
                "name": "mac-mini",
                "role": "Control",
                "up": True,
                "resources": sanitize_resources(
                    mini_resources,
                    reason="The mini did not report memory or disk.",
                ),
                "services": [
                    {"id": "api", "label": "API", "up": True},
                    {"id": "postgres", "label": "PostgreSQL", "up": bool(services.get("postgres"))},
                    {"id": "redis", "label": "Redis", "up": bool(services.get("redis"))},
                    {"id": "qdrant", "label": "Qdrant", "up": bool(services.get("qdrant"))},
                ],
            },
            "studio": {
                "name": "mac-studio",
                "role": "Compute",
                "up": ollama_up,
                "resources": sanitize_resources(
                    studio_resources,
                    reason=str(studio_resources.get("reason") or "Studio has not reported memory or disk yet."),
                ),
                "ollama_up": ollama_up,
                "jupyter_up": jupyter_up,
                "worker_up": bool(worker.get("http_ok")),
                "installed": _models(installed),
                "loaded": _models(loaded),
            },
        },
        "modules": modules,
    }


def _models(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        name = str(row.get("name") or "").strip()
        if not name:
            continue
        size = row.get("size_bytes")
        item: dict[str, Any] = {
            "name": name,
            "size_bytes": size if isinstance(size, int) else None,
        }
        for key in ("parameter_size", "quantization", "expires_at"):
            value = row.get(key)
            if isinstance(value, str) and value:
                item[key] = value[:40]
        out.append(item)
    return out


def _module(mid: str, label: str, state: str, detail: str, open_as: str) -> dict[str, str]:
    return {"id": mid, "label": label, "state": state, "detail": detail, "open": open_as}


def _chat_module(ollama_up: bool, ready_models: list[dict[str, Any]]) -> dict[str, str]:
    if ollama_up and ready_models:
        count = len(ready_models)
        noun = "model" if count == 1 else "models"
        return _module("chat", "Chat", "ready", f"{count} local {noun} ready on the Studio.", "chat")
    if ollama_up:
        return _module("chat", "Chat", "limited", "Studio is up, but no local chat model is ready.", "chat")
    return _module("chat", "Chat", "off", "Studio Ollama is not reachable.", "")


def _memory_module(memory: dict[str, Any]) -> dict[str, str]:
    backend = str(memory.get("backend") or "")
    if backend == "qdrant" and memory.get("ok"):
        docs = memory.get("documents")
        count = docs if isinstance(docs, int) else None
        detail = f"Qdrant is up with {count} items." if count is not None else "Qdrant is up."
        return _module("memory", "Memory", "ready", detail, "")
    if backend == "memory":
        return _module("memory", "Memory", "limited", "Using temporary memory, not Qdrant.", "")
    return _module("memory", "Memory", "off", "Memory is not available.", "")


def _frontier_module(configured: int, authorized: bool) -> dict[str, str]:
    if configured and authorized:
        return _module(
            "frontier",
            "Frontier LLMs",
            "ready",
            f"{configured} provider key saved and spend is authorized.",
            "keys",
        )
    if configured:
        return _module(
            "frontier",
            "Frontier LLMs",
            "limited",
            "A key is saved. Spend stays off until you authorize it.",
            "keys",
        )
    return _module("frontier", "Frontier LLMs", "limited", "No frontier key is saved yet.", "keys")


def _mcp_module(servers: list[dict[str, Any]]) -> dict[str, str]:
    enabled = [s for s in servers if isinstance(s, dict) and s.get("enabled", True) and s.get("id")]
    if enabled:
        names = ", ".join(str(s.get("label") or s.get("id")) for s in enabled[:4])
        return _module("mcp", "MCP services", "ready", names, "settings")
    return _module("mcp", "MCP services", "limited", "No extra service is saved yet.", "settings")


def _antares_module(jobs_up: bool, completions_up: bool) -> dict[str, str]:
    if jobs_up and completions_up:
        return _module("antares", "Antares", "ready", "Jobs and the local model helper are up.", "")
    if jobs_up:
        return _module("antares", "Antares", "limited", "Jobs are up. The local model helper is down.", "")
    return _module("antares", "Antares", "off", "Antares jobs are not reachable.", "")
