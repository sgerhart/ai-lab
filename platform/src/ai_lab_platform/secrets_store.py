"""Operator secret store for foundation API keys (FEAT-012).

Values live under ~/.ai-lab/secrets/ (mode 0600 files). Never log or return
raw values. Vault (ADR 0039) is the eventual home; this file store is the
browser-entry bridge until Vault is initialized.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

PROVIDER_IDS = ("openai", "anthropic", "gemini")
_SAFE_ID = re.compile(r"^[a-z][a-z0-9_-]{0,31}$")


class SecretStore:
    def __init__(self, root: str | Path | None = None) -> None:
        if root is None:
            root = Path.home() / ".ai-lab" / "secrets"
        self.root = Path(root)
        self.providers_dir = self.root / "providers"
        self.flags_dir = self.root / "flags"

    def ensure(self) -> None:
        self.providers_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.flags_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.root, 0o700)
        os.chmod(self.providers_dir, 0o700)
        os.chmod(self.flags_dir, 0o700)

    def _provider_path(self, provider_id: str) -> Path:
        if provider_id not in PROVIDER_IDS or not _SAFE_ID.match(provider_id):
            raise ValueError(f"unknown provider: {provider_id}")
        return self.providers_dir / f"{provider_id}.key"

    def has_provider(self, provider_id: str) -> bool:
        path = self._provider_path(provider_id)
        if not path.is_file():
            return False
        return bool(path.read_text(encoding="utf-8").strip())

    def get_provider(self, provider_id: str) -> str:
        """Return raw key for server-side use only. Never send to browsers."""
        path = self._provider_path(provider_id)
        if not path.is_file():
            return ""
        return path.read_text(encoding="utf-8").strip()

    def set_provider(self, provider_id: str, value: str) -> None:
        self.ensure()
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("empty secret")
        if "\n" in cleaned or "\r" in cleaned:
            raise ValueError("secret must be a single line")
        path = self._provider_path(provider_id)
        path.write_text(cleaned + "\n", encoding="utf-8")
        os.chmod(path, 0o600)

    def clear_provider(self, provider_id: str) -> bool:
        path = self._provider_path(provider_id)
        if path.is_file():
            path.unlink()
            return True
        return False

    def usage_billed_authorized(self) -> bool:
        flag = self.flags_dir / "usage_billed_authorized"
        return flag.is_file() and flag.read_text(encoding="utf-8").strip() == "1"

    def set_usage_billed_authorized(self, authorized: bool) -> None:
        self.ensure()
        flag = self.flags_dir / "usage_billed_authorized"
        if authorized:
            flag.write_text("1\n", encoding="utf-8")
            os.chmod(flag, 0o600)
        elif flag.exists():
            flag.unlink()

    def status(self) -> dict[str, Any]:
        """Redacted status for APIs and UI."""
        providers = []
        for pid in PROVIDER_IDS:
            present = self.has_provider(pid)
            providers.append(
                {
                    "id": pid,
                    "configured": present,
                    "billing_class": "usage_billed_api",
                    "hint": _hint(pid),
                }
            )
        return {
            "ok": True,
            "backend": "file",
            "path_note": "~/.ai-lab/secrets/providers/*.key (mode 600); Vault later (ADR 0039)",
            "usage_billed_authorized": self.usage_billed_authorized(),
            "providers": providers,
            "note": "Secret values are never included in this response.",
        }


def _hint(provider_id: str) -> str:
    return {
        "openai": "OpenAI platform API key (not ChatGPT Plus session)",
        "anthropic": "Anthropic Console API key (not Claude Pro alone)",
        "gemini": "Google AI Studio / Gemini API key",
    }.get(provider_id, "")


def default_secret_store() -> SecretStore:
    return SecretStore()
