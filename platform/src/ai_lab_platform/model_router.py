"""Provider-neutral model interface. No vendor SDK required for tests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class CompletionRequest:
    model: str
    prompt: str
    backend: str = "ollama"


@dataclass
class CompletionResponse:
    model: str
    backend: str
    text: str


class CompletionBackend(Protocol):
    def complete(self, request: CompletionRequest) -> CompletionResponse: ...


class FakeBackend:
    """Deterministic backend for tests. Not a model."""

    def complete(self, request: CompletionRequest) -> CompletionResponse:
        return CompletionResponse(
            model=request.model,
            backend=request.backend,
            text=f"[fake:{request.backend}:{request.model}] {request.prompt[:80]}",
        )


class ModelRouter:
    def __init__(self, backends: dict[str, CompletionBackend] | None = None) -> None:
        self.backends = backends or {"ollama": FakeBackend(), "cloud": FakeBackend()}

    def complete(self, request: CompletionRequest) -> CompletionResponse:
        if request.backend not in self.backends:
            raise KeyError(f"unknown backend {request.backend}")
        return self.backends[request.backend].complete(request)
