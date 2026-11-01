"""Unit tests for ModelBackend implementations and ModelWorker API."""

from __future__ import annotations

import unittest
from unittest import mock
from fastapi.testclient import TestClient

from packages.contracts import (
    GenerationConfig,
    GenerationResult,
    HealthStatus,
    ModelCapabilities,
)
from services.model.app import app, set_model_backend
from services.model.backend import (
    HttpModelBackend,
    MLXModelBackend,
    MockModelBackend,
    extract_python_code,
)


class TestModelBackend(unittest.TestCase):
    """Verifies model backend abstractions, code extraction, and API endpoints."""

    def test_extract_python_code_various_formats(self) -> None:
        # 1. Standard python markdown fence
        raw_1 = "Here is the solution:\n```python\ndef solve(x):\n    return x * 2\n```\nAll done!"
        code_1, valid_1 = extract_python_code(raw_1)
        self.assertTrue(valid_1)
        self.assertEqual(code_1, "def solve(x):\n    return x * 2")

        # 2. Generic markdown fence without language identifier
        raw_2 = "```\ndef square(n):\n    return n ** 2\n```"
        code_2, valid_2 = extract_python_code(raw_2)
        self.assertTrue(valid_2)
        self.assertEqual(code_2, "def square(n):\n    return n ** 2")

        # 3. Raw Python code without fences
        raw_3 = "def identity(val):\n    return val"
        code_3, valid_3 = extract_python_code(raw_3)
        self.assertTrue(valid_3)
        self.assertEqual(code_3, "def identity(val):\n    return val")

        # 4. Incomplete / syntax error code
        raw_4 = "```python\ndef unclosed_paren(a, b:\n    return a + b\n```"
        code_4, valid_4 = extract_python_code(raw_4)
        self.assertFalse(valid_4)
        self.assertIn("def unclosed_paren", code_4)

    def test_mock_model_backend_with_solutions(self) -> None:
        solutions = {
            "fibonacci": "def fibonacci(n):\n    return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)",
            "factorial": "def factorial(n):\n    return 1 if n <= 1 else n * factorial(n-1)",
        }
        backend = MockModelBackend(task_solutions=solutions)
        backend.load("Qwen/Qwen3-0.6B", "rev-test")

        # Prompt referencing fibonacci
        prompt_1 = "Please implement def fibonacci(n: int) -> int:"
        res_1 = backend.generate(prompt_1, seed=42, config=GenerationConfig())
        self.assertTrue(res_1.syntax_valid)
        self.assertIn("fibonacci", res_1.extracted_code)
        self.assertEqual(res_1.model_version, "Qwen/Qwen3-0.6B@rev-test")

        # Prompt referencing factorial
        prompt_2 = "Contract:\ndef factorial(n: int) -> int:"
        res_2 = backend.generate(prompt_2, seed=42, config=GenerationConfig())
        self.assertTrue(res_2.syntax_valid)
        self.assertIn("factorial", res_2.extracted_code)

        # Health check
        health = backend.health()
        self.assertTrue(health.healthy)
        self.assertEqual(health.details.get("configured_solutions"), 2)

    def test_mlx_model_backend_lifecycle_and_fallback(self) -> None:
        backend = MLXModelBackend(dry_run_fallback=True)
        caps = backend.capabilities()
        self.assertIsInstance(caps, ModelCapabilities)
        self.assertTrue(caps.supports_inference)

        # When dry_run_fallback is enabled, load() does not raise
        backend.load("Qwen/Qwen3-0.6B", "test-rev")
        
        # Generation produces a dry-run result when MLX is not installed
        res = backend.generate("def test():", seed=42, config=GenerationConfig())
        self.assertIsInstance(res, GenerationResult)
        self.assertTrue(res.syntax_valid)

        health = backend.health()
        self.assertTrue(health.healthy)

    def test_model_worker_api_endpoints(self) -> None:
        mock_backend = MockModelBackend(
            responses={"custom prompt": "```python\ndef custom(): return 42\n```"}
        )
        set_model_backend(mock_backend)
        client = TestClient(app)

        # GET /v1/health
        h_resp = client.get("/v1/health")
        self.assertEqual(h_resp.status_code, 200)
        self.assertTrue(h_resp.json()["healthy"])

        # GET /v1/capabilities
        c_resp = client.get("/v1/capabilities")
        self.assertEqual(c_resp.status_code, 200)
        self.assertTrue(c_resp.json()["supports_inference"])

        # POST /v1/models/load
        l_resp = client.post(
            "/v1/models/load",
            json={"model_id": "Qwen/Qwen3-0.6B", "revision": "rev-test"},
        )
        self.assertEqual(l_resp.status_code, 200)
        self.assertEqual(l_resp.json()["status"], "loaded")

        # POST /v1/generate
        g_resp = client.post(
            "/v1/generate",
            json={
                "prompt": "custom prompt",
                "seed": 42,
                "config": {"temperature": 0.2, "seed": 42},
            },
        )
        self.assertEqual(g_resp.status_code, 200)
        gen_data = g_resp.json()
        self.assertTrue(gen_data["syntax_valid"])
        self.assertEqual(gen_data["extracted_code"], "def custom(): return 42")

    def test_http_model_backend(self) -> None:
        backend = HttpModelBackend(base_url="http://mac-studio:8090")
        
        # Test capabilities mapping
        caps_dict = {
            "supports_inference": True,
            "supports_sft": True,
            "supports_lora": True,
            "supports_qlora": False,
            "supports_grpo": False,
            "supports_logprobs": False,
            "device_arch": "apple_silicon",
        }
        with mock.patch.object(backend, "_get", return_value=caps_dict):
            caps = backend.capabilities()
            self.assertIsInstance(caps, ModelCapabilities)
            self.assertTrue(caps.supports_inference)
            self.assertEqual(caps.device_arch, "apple_silicon")

        # Test health mapping
        health_dict = {"healthy": True, "status": "ok", "details": {"mlx": True}}
        with mock.patch.object(backend, "_get", return_value=health_dict):
            health = backend.health()
            self.assertIsInstance(health, HealthStatus)
            self.assertTrue(health.healthy)

        # Test generate mapping
        gen_dict = {
            "raw_text": "```python\ndef solve(): return 1\n```",
            "extracted_code": "def solve(): return 1",
            "syntax_valid": True,
            "prompt_tokens": 10,
            "completion_tokens": 8,
            "latency_ms": 12,
            "model_version": "Qwen/Qwen3-0.6B@main",
            "stop_reason": "stop",
        }
        with mock.patch.object(backend, "_post", return_value=gen_dict):
            res = backend.generate("solve this", seed=42, config=GenerationConfig())
            self.assertIsInstance(res, GenerationResult)
            self.assertTrue(res.syntax_valid)
            self.assertEqual(res.extracted_code, "def solve(): return 1")
