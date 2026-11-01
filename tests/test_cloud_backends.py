"""IWO-021 — cloud backends gated by SecretStore (mocked HTTP, no live $)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.cloud_backends import (
    AnthropicBackend,
    CloudUnavailable,
    GeminiBackend,
    OpenAIBackend,
    estimate_cost_usd,
)
from ai_lab_platform.model_router import (
    CompletionRequest,
    CompletionResponse,
    build_router_from_settings,
)
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
        self.assertEqual(text.usage["input_tokens"], 3)
        self.assertEqual(text.usage["output_tokens"], 2)
        self.assertEqual(text.usage["total_tokens"], 5)
        self.assertIsNotNone(text.usage["estimated_cost_usd"])
        self.assertAlmostEqual(text.usage["estimated_cost_usd"], 0.00000165, places=8)
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
        self.assertEqual(text.usage["input_tokens"], 4)
        self.assertEqual(text.usage["output_tokens"], 1)
        self.assertEqual(text.usage["total_tokens"], 5)
        self.assertIsNotNone(text.usage["estimated_cost_usd"])
        self.assertAlmostEqual(text.usage["estimated_cost_usd"], 0.0000072, places=8)
        self.assertEqual(mocked.call_args.kwargs["headers"]["x-api-key"], "ant-test-not-real")

    def test_gemini_complete_mocked(self) -> None:
        try:
            import httpx  # noqa: F401
        except ImportError:
            self.skipTest("httpx not installed")
        self.store.set_usage_billed_authorized(True)
        self.store.set_provider("gemini", "gem-test-not-real")
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "gemini-hi"}]}}],
            "usageMetadata": {"promptTokenCount": 5, "candidatesTokenCount": 2},
        }
        mock_resp.raise_for_status.return_value = None
        with patch("httpx.post", return_value=mock_resp) as mocked:
            text = GeminiBackend(self.store).complete(
                CompletionRequest(
                    model="gemini-2.0-flash", prompt="ping", backend="gemini"
                )
            )
        self.assertEqual(text.text, "gemini-hi")
        self.assertEqual(text.backend, "gemini")
        self.assertEqual(text.usage["input_tokens"], 5)
        self.assertEqual(text.usage["output_tokens"], 2)
        self.assertEqual(text.usage["total_tokens"], 7)
        self.assertIsNotNone(text.usage["estimated_cost_usd"])
        self.assertAlmostEqual(text.usage["estimated_cost_usd"], 0.00000097, places=8)
        self.assertEqual(mocked.call_args.kwargs["headers"]["x-goog-api-key"], "gem-test-not-real")

    def test_estimate_cost_usd_function(self) -> None:
        # None inputs
        self.assertIsNone(estimate_cost_usd("openai", "gpt-4o", None, None))
        # Unknown provider
        self.assertIsNone(estimate_cost_usd("unknown_provider", "model-x", 100, 100))
        # Exact model
        cost = estimate_cost_usd("openai", "gpt-4o", 1000, 500)
        self.assertIsNotNone(cost)
        self.assertAlmostEqual(cost, 0.0075, places=6)
        # Fallback rates for known provider with unknown model
        cost_fallback = estimate_cost_usd("openai", "unknown-future-model", 1000, 1000)
        self.assertIsNotNone(cost_fallback)
        self.assertAlmostEqual(cost_fallback, 0.00075, places=6)

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

    def test_stream_message_emits_cloud_metrics(self) -> None:
        try:
            from fastapi.testclient import TestClient
            from langgraph.checkpoint.memory import MemorySaver
            from ai_lab_platform.control_app import create_control_app
            from ai_lab_platform.store import SqliteStore
            from ai_lab_platform.model_router import ModelRouter
        except ImportError:
            self.skipTest("fastapi or langgraph not installed")

        self.store.set_usage_billed_authorized(True)
        self.store.set_provider("openai", "sk-test-real")

        class MockCloudBackend(OpenAIBackend):
            def complete(self, request: CompletionRequest) -> CompletionResponse:
                return CompletionResponse(
                    model=request.model or "gpt-4o-mini",
                    backend="openai",
                    text="Hello from cloud",
                    billing_class=self.billing_class,
                    usage={
                        "input_tokens": 100,
                        "output_tokens": 50,
                        "total_tokens": 150,
                        "estimated_cost_usd": 0.000045,
                    },
                )

        router = ModelRouter(
            backends={"openai": MockCloudBackend(self.store)},
            default_backend="openai",
        )
        sqlite_store = SqliteStore(str(self.tmp / "test.db"))
        app = create_control_app(
            store=sqlite_store,
            checkpointer=MemorySaver(),
            token="test-token",
            dispatch=lambda _p: {"ok": True, "detail": "unused"},
            model_router=router,
            secret_store=self.store,
        )
        client = TestClient(app)
        headers = {"Authorization": "Bearer test-token"}
        conv = client.post("/v1/conversations", headers=headers, json={"agent": "lab-operations"})
        conv_id = conv.json()["id"]

        resp = client.post(
            f"/v1/conversations/{conv_id}/messages/stream",
            headers=headers,
            json={"content": "hello", "role": "user", "backend": "openai", "model": "gpt-4o-mini"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn('"event": "metrics"', resp.text)
        self.assertIn('"estimated_cost_usd": 4.5e-05', resp.text)
        self.assertIn('"input_tokens": 100', resp.text)
        self.assertIn('"output_tokens": 50', resp.text)
        self.assertIn('"total_tokens": 150', resp.text)


if __name__ == "__main__":
    unittest.main()
