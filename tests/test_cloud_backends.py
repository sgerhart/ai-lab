"""IWO-021 — cloud backends gated by SecretStore (mocked HTTP, no live $)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.cloud_backends import AnthropicBackend, CloudUnavailable, OpenAIBackend
from ai_lab_platform.model_router import CompletionRequest, build_router_from_settings
from ai_lab_platform.secrets_store import SecretStore
from ai_lab_platform.settings import Settings


class CloudBackendGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.store = SecretStore(self.tmp)
        self.store.ensure()

    def test_disabled_without_authorize(self) -> None:
        backend = OpenAIBackend(self.store)
        health = backend.health()
        self.assertFalse(health["enabled"])
        self.assertEqual(health["reason"], "usage_billed_not_authorized")
        with self.assertRaises(PermissionError):
            backend.complete(CompletionRequest(model="gpt-4o-mini", prompt="hi", backend="openai"))

    def test_disabled_without_key(self) -> None:
        self.store.set_usage_billed_authorized(True)
        backend = AnthropicBackend(self.store)
        health = backend.health()
        self.assertFalse(health["enabled"])
        self.assertEqual(health["reason"], "missing_api_key")
        with self.assertRaises(PermissionError):
            backend.complete(
                CompletionRequest(model="claude-3-5-haiku-latest", prompt="hi", backend="anthropic")
            )

    def test_openai_complete_mocked(self) -> None:
        try:
            import httpx  # noqa: F401
        except ImportError:
            self.skipTest("httpx not installed")
        self.store.set_usage_billed_authorized(True)
        self.store.set_provider("openai", "sk-test-not-real")
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "hello-cloud"}}],
            "usage": {"prompt_tokens": 3, "completion_tokens": 2},
        }
        mock_resp.raise_for_status.return_value = None
        with patch("httpx.post", return_value=mock_resp) as mocked:
            text = OpenAIBackend(self.store).complete(
                CompletionRequest(model="gpt-4o-mini", prompt="ping", backend="openai", system="sys")
            )
        self.assertEqual(text.text, "hello-cloud")
        self.assertEqual(text.backend, "openai")
        self.assertEqual(text.billing_class.value, "usage_billed_api")
        args, kwargs = mocked.call_args
        self.assertIn("/chat/completions", args[0])
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer sk-test-not-real")
        # Ensure secret store status never echoes the key
        status = self.store.status()
        self.assertNotIn("sk-test", str(status))

    def test_anthropic_complete_mocked(self) -> None:
        try:
            import httpx  # noqa: F401
        except ImportError:
            self.skipTest("httpx not installed")
        self.store.set_usage_billed_authorized(True)
        self.store.set_provider("anthropic", "ant-test-not-real")
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "content": [{"type": "text", "text": "claude-hi"}],
            "usage": {"input_tokens": 4, "output_tokens": 1},
        }
        mock_resp.raise_for_status.return_value = None
        with patch("httpx.post", return_value=mock_resp) as mocked:
            text = AnthropicBackend(self.store).complete(
                CompletionRequest(
                    model="claude-3-5-haiku-latest", prompt="ping", backend="anthropic"
                )
            )
        self.assertEqual(text.text, "claude-hi")
        self.assertEqual(mocked.call_args.kwargs["headers"]["x-api-key"], "ant-test-not-real")

    def test_http_error_is_cloud_unavailable(self) -> None:
        try:
            import httpx
        except ImportError:
            self.skipTest("httpx not installed")
        self.store.set_usage_billed_authorized(True)
        self.store.set_provider("openai", "sk-test")
        with patch("httpx.post", side_effect=httpx.ConnectError("boom")):
            with self.assertRaises(CloudUnavailable):
                OpenAIBackend(self.store).complete(
                    CompletionRequest(model="gpt-4o-mini", prompt="x", backend="openai")
                )

    def test_router_health_reflects_secrets(self) -> None:
        router = build_router_from_settings(
            Settings(studio_ollama_url="", api_token=""),
            secret_store=self.store,
        )
        providers = {p["id"]: p for p in router.list_providers()}
        self.assertFalse(providers["openai"]["enabled"])
        self.store.set_usage_billed_authorized(True)
        self.store.set_provider("openai", "sk-x")
        providers = {p["id"]: p for p in router.list_providers()}
        self.assertTrue(providers["openai"]["enabled"])
        self.assertIn("gpt-4o-mini", providers["openai"]["models"])
        blob = str(providers)
        self.assertNotIn("sk-x", blob)


if __name__ == "__main__":
    unittest.main()
