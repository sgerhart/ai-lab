"""Ollama HTTP backend. Loopback only. Never pulls weights."""

from __future__ import annotations

from urllib.parse import urlparse

from .model_catalog import refuse_pull
from .model_router import CompletionRequest, CompletionResponse


def _require_loopback(base_url: str) -> None:
    host = (urlparse(base_url).hostname or "").lower()
    if host not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError(
            f"Ollama URL must be loopback until a Tailscale bind is documented (got host={host!r})"
        )


class OllamaUnavailable(RuntimeError):
    """Studio/Ollama did not answer. Callers must not treat this as a completed job."""


class OllamaBackend:
    def __init__(self, base_url: str = "http://127.0.0.1:11434", timeout_seconds: float = 2.0) -> None:
        _require_loopback(base_url)
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def complete(self, request: CompletionRequest) -> CompletionResponse:
        import httpx

        url = self.base_url + "/api/generate"
        payload = {"model": request.model, "prompt": request.prompt, "stream": False}
        try:
            response = httpx.post(url, json=payload, timeout=self.timeout_seconds)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            raise OllamaUnavailable(str(exc)) from exc
        text = ""
        if isinstance(data, dict):
            text = str(data.get("response") or data.get("text") or "")
        return CompletionResponse(model=request.model, backend="ollama", text=text)

    def pull(self, model: str) -> None:
        refuse_pull(model)
