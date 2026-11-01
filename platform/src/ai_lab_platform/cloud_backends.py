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

# Price in USD per 1M tokens: (input_per_million, output_per_million)
PROVIDER_MODEL_RATES: dict[str, dict[str, tuple[float, float]]] = {
    "openai": {
        "gpt-4o-mini": (0.15, 0.60),
        "gpt-4o": (2.50, 10.00),
        "default": (0.15, 0.60),
    },
    "anthropic": {
        "claude-3-5-haiku": (0.80, 4.00),
        "claude-3-5-haiku-latest": (0.80, 4.00),
        "claude-sonnet-4-5": (3.00, 15.00),
        "claude-3-5-sonnet": (3.00, 15.00),
        "default": (0.80, 4.00),
    },
    "gemini": {
        "gemini-2.0-flash": (0.075, 0.30),
        "gemini-1.5-flash": (0.075, 0.30),
        "gemini-1.5-pro": (1.25, 5.00),
        "default": (0.10, 0.40),
    },
}


def estimate_cost_usd(
    provider: str,
    model: str,
    input_tokens: int | None,
    output_tokens: int | None,
) -> float | None:
    """Estimate completion cost in USD based on model rate cards."""
    if input_tokens is None and output_tokens is None:
        return None
    rates_by_provider = PROVIDER_MODEL_RATES.get(provider.lower())
    if not rates_by_provider:
        return None

    model_lower = (model or "").lower()
    rates = rates_by_provider.get(model_lower)
    if rates is None:
        for k, v in rates_by_provider.items():
            if k != "default" and k in model_lower:
                rates = v
                break
    if rates is None:
        rates = rates_by_provider.get("default", (0.0, 0.0))

    in_rate_per_token = rates[0] / 1_000_000.0
    out_rate_per_token = rates[1] / 1_000_000.0
    cost = (input_tokens or 0) * in_rate_per_token + (output_tokens or 0) * out_rate_per_token
    return round(cost, 8)


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
                    "max_tokens": 4096,
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
                inp = u.get("prompt_tokens")
                out = u.get("completion_tokens")
                usage["input_tokens"] = inp
                usage["output_tokens"] = out
                if inp is not None or out is not None:
                    usage["total_tokens"] = u.get("total_tokens", (inp or 0) + (out or 0))
                    usage["estimated_cost_usd"] = estimate_cost_usd(self.provider_id, model, inp, out)
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
                    "max_tokens": 4096,
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
                inp = u.get("input_tokens")
                out = u.get("output_tokens")
                usage["input_tokens"] = inp
                usage["output_tokens"] = out
                if inp is not None or out is not None:
                    usage["total_tokens"] = (inp or 0) + (out or 0)
                    usage["estimated_cost_usd"] = estimate_cost_usd(self.provider_id, model, inp, out)
        return CompletionResponse(
            model=model,
            backend=self.provider_id,
            text=text,
            billing_class=self.billing_class,
            usage=usage,
        )


class GeminiBackend:
    billing_class = BillingClass.USAGE_BILLED_API
    provider_id = "gemini"

    def __init__(
        self,
        secret_store: SecretStore,
        *,
        base_url: str = "https://generativelanguage.googleapis.com/v1beta",
        timeout_seconds: float = 120.0,
    ) -> None:
        self.secret_store = secret_store
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def _gate_key(self) -> str:
        if not self.secret_store.usage_billed_authorized():
            raise PermissionError(
                "gemini is disabled; authorize usage-billed API on /secrets (ADR 0038)"
            )
        key = self.secret_store.get_provider(self.provider_id)
        if not key:
            raise PermissionError("gemini API key not configured in secret store")
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
        url = f"{self.base_url}/models/{model}:generateContent"
        contents: list[dict[str, Any]] = []
        if request.system:
            contents.append({"role": "user", "parts": [{"text": f"System instructions: {request.system}"}]})
            contents.append({"role": "model", "parts": [{"text": "Understood."}]})
        contents.append({"role": "user", "parts": [{"text": request.prompt}]})
        try:
            response = httpx.post(
                url,
                headers={
                    "x-goog-api-key": key,
                    "Content-Type": "application/json",
                },
                json={
                    "contents": contents,
                    "generationConfig": {
                        "maxOutputTokens": 4096,
                        "temperature": 0.2,
                    },
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
            candidates = data.get("candidates") or []
            if candidates and isinstance(candidates[0], dict):
                content = candidates[0].get("content") or {}
                parts = content.get("parts") or []
                text = "".join(str(p.get("text") or "") for p in parts if isinstance(p, dict))
            u = data.get("usageMetadata") or {}
            if isinstance(u, dict):
                inp = u.get("promptTokenCount")
                out = u.get("candidatesTokenCount")
                usage["input_tokens"] = inp
                usage["output_tokens"] = out
                if inp is not None or out is not None:
                    usage["total_tokens"] = u.get("totalTokenCount", (inp or 0) + (out or 0))
                    usage["estimated_cost_usd"] = estimate_cost_usd(self.provider_id, model, inp, out)
        return CompletionResponse(
            model=model,
            backend=self.provider_id,
            text=text,
            billing_class=self.billing_class,
            usage=usage,
        )

