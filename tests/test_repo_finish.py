"""MCP deny-by-default, Ollama loopback, and audit events."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.mcp import McpDenied, assert_allowed, listed_server_ids, load_allowlist
from ai_lab_platform.model_catalog import PullRefused
from ai_lab_platform.model_router import CompletionRequest
from ai_lab_platform.ollama_backend import OllamaBackend
from ai_lab_platform.orchestrator import Orchestrator
from ai_lab_platform.policy import load_policy
from ai_lab_platform.store import SqliteStore
from ai_lab_platform.work_order import WorkOrder


class McpAllowlistTests(unittest.TestCase):
    def test_empty_allowlist_denies(self) -> None:
        data = load_allowlist()
        self.assertEqual(data["policy"], "deny-unlisted")
        self.assertEqual(listed_server_ids(), frozenset())
        with self.assertRaises(McpDenied):
            assert_allowed("filesystem")


class OllamaBackendTests(unittest.TestCase):
    def test_rejects_lan_and_public_hosts(self) -> None:
        with self.assertRaises(ValueError):
            OllamaBackend("http://10.0.0.1:11434")
        with self.assertRaises(ValueError):
            OllamaBackend("http://8.8.8.8:11434")

    def test_allows_mac_studio_magicdns(self) -> None:
        backend = OllamaBackend("http://mac-studio:11434")
        self.assertEqual(backend.base_url, "http://mac-studio:11434")

    def test_pull_is_refused(self) -> None:
        with self.assertRaises(PullRefused):
            OllamaBackend().pull("llama3.1")

    def test_complete_uses_generate_on_loopback(self) -> None:
        try:
            import httpx  # noqa: F401
        except ImportError:
            self.skipTest("httpx not installed")
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"response": "pong"}
        mock_resp.raise_for_status.return_value = None
        with patch("ai_lab_platform.model_slot.read_resident", return_value=[]), patch(
            "httpx.post", return_value=mock_resp
        ) as mocked:
            text = OllamaBackend().complete(
                CompletionRequest(model="unused", prompt="ping", backend="ollama")
            )
        self.assertEqual(text.text, "pong")
        mocked.assert_called_once()
        args, kwargs = mocked.call_args
        self.assertTrue(str(args[0]).startswith("http://127.0.0.1:11434/"))
        self.assertFalse(kwargs["json"].get("stream"))
        self.assertNotIn("images", kwargs["json"])

    def test_complete_sends_images(self) -> None:
        try:
            import httpx  # noqa: F401
        except ImportError:
            self.skipTest("httpx not installed")
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"response": "a switch"}
        mock_resp.raise_for_status.return_value = None
        with patch("ai_lab_platform.model_slot.read_resident", return_value=[]), patch(
            "httpx.post", return_value=mock_resp
        ) as mocked:
            text = OllamaBackend().complete(
                CompletionRequest(
                    model="qwen3.8:27b",
                    prompt="what is this",
                    backend="ollama",
                    images=["abc123"],
                )
            )
        self.assertEqual(text.text, "a switch")
        _args, kwargs = mocked.call_args
        self.assertEqual(kwargs["json"]["images"], ["abc123"])

    def test_reads_images_from_capabilities(self) -> None:
        try:
            import httpx  # noqa: F401
        except ImportError:
            self.skipTest("httpx not installed")
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"capabilities": ["completion", "vision"]}
        mock_resp.raise_for_status.return_value = None
        backend = OllamaBackend("http://127.0.0.1:11434")
        with patch("httpx.post", return_value=mock_resp) as mocked:
            self.assertTrue(backend.reads_images("qwen3.8:27b"))
            self.assertTrue(backend.reads_images("Qwen3.8:27b"))
        self.assertEqual(mocked.call_count, 1)
        mock_resp.json.return_value = {"capabilities": ["completion"]}
        backend._vision_cache.clear()
        with patch("httpx.post", return_value=mock_resp):
            self.assertFalse(backend.reads_images("llama3.2:3b"))


class AuditTests(unittest.TestCase):
    def test_submit_writes_audit(self) -> None:
        tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
        tmp.close()
        store = SqliteStore(tmp.name)
        orch = Orchestrator(store)
        policy = load_policy("lab-operations")
        order = orch.submit(
            WorkOrder.new(
                objective="audit",
                agent="lab-operations",
                allowed_tools=list(policy.allowed_tools),
            )
        )
        events = store.list_audit(order.id)
        self.assertTrue(any(e["event"] == "submitted" for e in events))


if __name__ == "__main__":
    unittest.main()
