"""Usage-billed cloud completion backends (FEAT-011 / IWO-021).

Keys come from SecretStore (never logged). Enabled only when the operator has
set usage_billed_authorized and configured a provider key. No silent fallback
from local Ollama.
"""

from __future__ import annotations

from typing import Any

from .conversation import BillingClass
from .model_router import CompletionRequest, CompletionResponse
from .secrets_store import SecretStore

DEFAULT_MODELS: dict[str, list[str]] = {
    "openai": ["gpt-4o-mini", "gpt-4o"],
    "anthropic": ["claude-3-5-haiku-latest", "claude-sonnet-4-5"],
    "gemini": ["gemini-2.0-flash"],
}


class CloudUnavailable(RuntimeError):
    """Transport or API error from a usage-billed provider."""


class OpenAIBackend:
    billing_class = BillingClass.USAGE_BILLED_API
    provider_id = "openai"

    def __init__(
        self,
        secret_store: SecretStore,
        *,
        base_url: str = "https://api.openai.com/v1",
        timeout_seconds: float = 120.0,
    ) -> None:
        self.secret_store = secret_store
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def _gate_key(self) -> str:
        if not self.secret_store.usage_billed_authorized():
            raise PermissionError(
                "openai is disabled; authorize usage-billed API on /secrets (ADR 0038)"
            )
        key = self.secret_store.get_provider(self.provider_id)
        if not key:
            raise PermissionError("openai API key not configured in secret store")
        return key

    def health(self) -> dict[str, Any]:
        authorized = self.secret_store.usage_billed_authorized()
        has_key = self.secret_store.has_provider(self.provider_id)
        enabled = authorized and has_key
        reason = None
        if not authorized:
            reason = "usage_billed_not_authorized"
        elif not has_key:
            reason = "missing_api_key"
        return {
            "ok": enabled,
            "enabled": enabled,
            "backend": self.provider_id,
            "billing_class": self.billing_class.value,
            "models": list(DEFAULT_MODELS[self.provider_id]) if enabled else [],
            "reason": reason,
        }

    def complete(self, request: CompletionRequest) -> CompletionResponse:
        key = self._gate_key()
        import httpx

        model = request.model or DEFAULT_MODELS[self.provider_id][0]
        messages: list[dict[str, str]] = []
        if request.system:
            messages.append({"role": "system", "content": request.system})
        messages.append({"role": "user", "content": request.prompt})
        url = self.base_url + "/chat/completions"
        try:
            response = httpx.post(
                url,
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": 512,
                    "temperature": 0.2,
                },
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            raise CloudUnavailable(str(exc)) from exc
        text = ""
        usage: dict[str, Any] = {"estimated_cost_usd": None}
        if isinstance(data, dict):
            choices = data.get("choices") or []
            if choices and isinstance(choices[0], dict):
                msg = choices[0].get("message") or {}
                text = str(msg.get("content") or "")
            u = data.get("usage") or {}
            if isinstance(u, dict):
                usage["input_tokens"] = u.get("prompt_tokens")
                usage["output_tokens"] = u.get("completion_tokens")
        return CompletionResponse(
            model=model,
            backend=self.provider_id,
            text=text,
            billing_class=self.billing_class,
            usage=usage,
        )


class AnthropicBackend:
    billing_class = BillingClass.USAGE_BILLED_API
    provider_id = "anthropic"

    def __init__(
        self,
        secret_store: SecretStore,
        *,
        base_url: str = "https://api.anthropic.com/v1",
        timeout_seconds: float = 120.0,
        api_version: str = "2023-06-01",
    ) -> None:
        self.secret_store = secret_store
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.api_version = api_version

    def _gate_key(self) -> str:
        if not self.secret_store.usage_billed_authorized():
            raise PermissionError(
                "anthropic is disabled; authorize usage-billed API on /secrets (ADR 0038)"
            )
        key = self.secret_store.get_provider(self.provider_id)
        if not key:
            raise PermissionError("anthropic API key not configured in secret store")
        return key

    def health(self) -> dict[str, Any]:
        authorized = self.secret_store.usage_billed_authorized()
        has_key = self.secret_store.has_provider(self.provider_id)
        enabled = authorized and has_key
        reason = None
        if not authorized:
            reason = "usage_billed_not_authorized"
        elif not has_key:
            reason = "missing_api_key"
        return {
            "ok": enabled,
            "enabled": enabled,
            "backend": self.provider_id,
            "billing_class": self.billing_class.value,
            "models": list(DEFAULT_MODELS[self.provider_id]) if enabled else [],
            "reason": reason,
        }

    def complete(self, request: CompletionRequest) -> CompletionResponse:
        key = self._gate_key()
        import httpx

        model = request.model or DEFAULT_MODELS[self.provider_id][0]
        url = self.base_url + "/messages"
        try:
            response = httpx.post(
                url,
                headers={
                    "x-api-key": key,
                    "anthropic-version": self.api_version,
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "max_tokens": 512,
                    "system": request.system or "You are a helpful lab agent.",
                    "messages": [{"role": "user", "content": request.prompt}],
                },
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            raise CloudUnavailable(str(exc)) from exc
        text = ""
        usage: dict[str, Any] = {"estimated_cost_usd": None}
        if isinstance(data, dict):
            blocks = data.get("content") or []
            parts: list[str] = []
            for block in blocks:
                if isinstance(block, dict) and block.get("type") == "text":
                    parts.append(str(block.get("text") or ""))
            text = "".join(parts)
            u = data.get("usage") or {}
            if isinstance(u, dict):
                usage["input_tokens"] = u.get("input_tokens")
                usage["output_tokens"] = u.get("output_tokens")
        return CompletionResponse(
            model=model,
            backend=self.provider_id,
            text=text,
            billing_class=self.billing_class,
            usage=usage,
        )
