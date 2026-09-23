"""Provider-neutral model router with billing classes (FEAT-011 / IWO-004, ADR 0038).

Cloud providers start **disabled**. There is no silent fallback from local to
usage-billed API. Credentials never appear in API responses.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from .conversation import BillingClass


@dataclass
class CompletionRequest:
    model: str
    prompt: str
    backend: str = "fake"
    system: str = ""


@dataclass
class CompletionResponse:
    model: str
    backend: str
    text: str
    billing_class: BillingClass = BillingClass.LOCAL
    usage: dict[str, Any] = field(default_factory=dict)


class CompletionBackend(Protocol):
    def complete(self, request: CompletionRequest) -> CompletionResponse: ...

    def health(self) -> dict[str, Any]: ...


class FakeBackend:
    """Deterministic backend for tests. Not a live model."""

    billing_class = BillingClass.LOCAL

    def complete(self, request: CompletionRequest) -> CompletionResponse:
        return CompletionResponse(
            model=request.model,
            backend=request.backend or "fake",
            text=f"[fake:{request.backend or 'fake'}:{request.model}] {request.prompt[:80]}",
            billing_class=self.billing_class,
            usage={"input_tokens": 0, "output_tokens": 0, "estimated_cost_usd": 0.0},
        )

    def health(self) -> dict[str, Any]:
        return {"ok": True, "backend": "fake", "billing_class": self.billing_class.value}


class ScriptedToolBackend:
    """Test backend that returns a scripted sequence of tool/final turns.

    Each script item is either:
      {"type": "tool", "name": "...", "args": {...}}
      {"type": "final", "text": "..."}
    """

    billing_class = BillingClass.LOCAL

    def __init__(self, script: list[dict[str, Any]] | None = None) -> None:
        self.script = list(script or [])
        self._i = 0

    def complete(self, request: CompletionRequest) -> CompletionResponse:
        if self._i >= len(self.script):
            item: dict[str, Any] = {"type": "final", "text": "done"}
        else:
            item = self.script[self._i]
            self._i += 1
        if item.get("type") == "tool":
            text = f"TOOL {item['name']} {item.get('args', {})}"
        else:
            text = f"FINAL {item.get('text', '')}"
        return CompletionResponse(
            model=request.model,
            backend="scripted",
            text=text,
            billing_class=self.billing_class,
            usage={"input_tokens": 1, "output_tokens": 1, "estimated_cost_usd": 0.0},
        )

    def health(self) -> dict[str, Any]:
        return {"ok": True, "backend": "scripted", "billing_class": self.billing_class.value}


class DisabledCloudBackend:
    """Stub for OpenAI / Anthropic / Gemini until the owner enables credentials."""

    def __init__(self, name: str, billing_class: BillingClass = BillingClass.USAGE_BILLED_API) -> None:
        self.name = name
        self.billing_class = billing_class
        self.enabled = False

    def complete(self, request: CompletionRequest) -> CompletionResponse:
        raise PermissionError(
            f"provider {self.name} is disabled; enable only after owner configures "
            "credentials and accepts usage-billed API charges (ADR 0038)"
        )

    def health(self) -> dict[str, Any]:
        return {
            "ok": False,
            "backend": self.name,
            "enabled": False,
            "billing_class": self.billing_class.value,
            "reason": "disabled_by_default",
        }


@dataclass
class ProviderInfo:
    id: str
    billing_class: BillingClass
    enabled: bool
    models: list[str]
    health: dict[str, Any]


class ModelRouter:
    """Routes completion requests. Never silently switches to a paid provider."""

    def __init__(
        self,
        backends: dict[str, CompletionBackend] | None = None,
        *,
        default_backend: str = "fake",
        allow_fallback: bool = False,
    ) -> None:
        if backends is None:
            backends = {
                "fake": FakeBackend(),
                # Local stand-in until Studio Ollama is wired (still billing_class=local).
                "ollama": FakeBackend(),
                "openai": DisabledCloudBackend("openai"),
                "anthropic": DisabledCloudBackend("anthropic"),
                "gemini": DisabledCloudBackend("gemini"),
            }
        self.backends = backends
        self.default_backend = default_backend
        self.allow_fallback = allow_fallback  # must stay False unless explicit policy
        self._usage_log: list[dict[str, Any]] = []

    def list_providers(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for name, backend in self.backends.items():
            health = backend.health()
            billing = getattr(backend, "billing_class", BillingClass.LOCAL)
            if isinstance(billing, BillingClass):
                bc = billing.value
            else:
                bc = str(billing)
            enabled = bool(health.get("enabled", health.get("ok", False)))
            if isinstance(backend, DisabledCloudBackend):
                enabled = backend.enabled
            models = ["fake-instruct"] if name in {"fake", "scripted", "ollama"} else []
            out.append(
                {
                    "id": name,
                    "billing_class": bc,
                    "enabled": enabled,
                    "models": models,
                    "health": {k: v for k, v in health.items() if k != "api_key"},
                }
            )
        return out

    def complete(self, request: CompletionRequest) -> CompletionResponse:
        backend_name = request.backend or self.default_backend
        if backend_name not in self.backends:
            raise KeyError(f"unknown backend {backend_name}")
        try:
            response = self.backends[backend_name].complete(request)
        except PermissionError:
            if self.allow_fallback and backend_name != self.default_backend:
                # Explicit opt-in only; still never used by default.
                response = self.backends[self.default_backend].complete(
                    CompletionRequest(
                        model=request.model,
                        prompt=request.prompt,
                        backend=self.default_backend,
                        system=request.system,
                    )
                )
            else:
                raise
        self._usage_log.append(
            {
                "backend": response.backend,
                "model": response.model,
                "billing_class": response.billing_class.value,
                "usage": dict(response.usage),
            }
        )
        return response

    def usage_log(self) -> list[dict[str, Any]]:
        return list(self._usage_log)
