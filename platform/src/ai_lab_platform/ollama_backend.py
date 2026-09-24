"""Ollama HTTP backend. Loopback or Tailscale lab hosts only. Never pulls weights."""

from __future__ import annotations

import ipaddress
import json
from typing import Any
from urllib.parse import urlparse

from .conversation import BillingClass
from .model_catalog import refuse_pull
from .model_router import CompletionRequest, CompletionResponse


def require_lab_ollama_url(base_url: str) -> None:
    """Reject public / all-interfaces Ollama endpoints."""
    host = (urlparse(base_url).hostname or "").lower()
    if not host:
        raise ValueError("Ollama URL missing host")
    if host in {"127.0.0.1", "localhost", "::1", "mac-studio"}:
        return
    if host.endswith(".ts.net"):
        return
    try:
        addr = ipaddress.ip_address(host)
    except ValueError as exc:
        raise ValueError(
            f"Ollama URL host not allowed (use loopback, mac-studio, or Tailscale; got {host!r})"
        ) from exc
    if addr.is_loopback or addr in ipaddress.ip_network("100.64.0.0/10"):
        return
    raise ValueError(
        f"Ollama URL must be loopback or Tailscale CGNAT (got host={host!r})"
    )


# Back-compat alias used by older tests/docs
_require_loopback = require_lab_ollama_url


class OllamaUnavailable(RuntimeError):
    """Studio/Ollama did not answer. Callers must not treat this as a completed job."""


class OllamaBackend:
    billing_class = BillingClass.LOCAL

    def __init__(self, base_url: str = "http://127.0.0.1:11434", timeout_seconds: float = 120.0) -> None:
        require_lab_ollama_url(base_url)
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def complete(self, request: CompletionRequest) -> CompletionResponse:
        import httpx

        url = self.base_url + "/api/generate"
        payload: dict[str, Any] = {
            "model": request.model,
            "prompt": request.prompt,
            "stream": False,
            "options": {"num_predict": 512, "temperature": 0.1},
        }
        if request.system:
            payload["system"] = request.system
        try:
            response = httpx.post(url, json=payload, timeout=self.timeout_seconds)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            raise OllamaUnavailable(str(exc)) from exc
        text = ""
        if isinstance(data, dict):
            text = str(data.get("response") or data.get("text") or "")
        return CompletionResponse(
            model=request.model,
            backend="ollama",
            text=text,
            billing_class=self.billing_class,
            usage={
                "eval_count": data.get("eval_count") if isinstance(data, dict) else None,
                "estimated_cost_usd": 0.0,
            },
        )

    def stream_complete(self, request: CompletionRequest):
        """Yield text chunks from Ollama streaming generate. Raises OllamaUnavailable."""
        import httpx

        url = self.base_url + "/api/generate"
        payload: dict[str, Any] = {
            "model": request.model,
            "prompt": request.prompt,
            "stream": True,
            "options": {"num_predict": 512, "temperature": 0.1},
        }
        if request.system:
            payload["system"] = request.system
        try:
            with httpx.stream(
                "POST", url, json=payload, timeout=self.timeout_seconds
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(data, dict):
                        chunk = data.get("response") or ""
                        if chunk:
                            yield str(chunk)
                        if data.get("done"):
                            break
        except httpx.HTTPError as exc:
            raise OllamaUnavailable(str(exc)) from exc

    def list_models(self) -> list[str]:
        import httpx

        try:
            response = httpx.get(self.base_url + "/api/tags", timeout=min(5.0, self.timeout_seconds))
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError:
            return []
        names: list[str] = []
        if isinstance(data, dict):
            for item in data.get("models") or []:
                name = item.get("name") if isinstance(item, dict) else None
                if name:
                    names.append(str(name))
        return names

    def health(self) -> dict[str, Any]:
        models = self.list_models()
        ok = bool(models) or self._ping_tags()
        return {
            "ok": ok,
            "enabled": ok,
            "backend": "ollama",
            "billing_class": self.billing_class.value,
            "base_host": urlparse(self.base_url).hostname,
            "models": models,
            "reason": None if ok else "unreachable_or_empty",
        }

    def _ping_tags(self) -> bool:
        import httpx

        try:
            response = httpx.get(self.base_url + "/api/tags", timeout=2.0)
            return response.status_code < 500
        except httpx.HTTPError:
            return False

    def pull(self, model: str) -> None:
        refuse_pull(model)
