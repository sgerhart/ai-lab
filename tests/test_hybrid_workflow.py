"""Test hybrid workflow: Local LLM + Frontier (OpenAI/Anthropic) collaboration."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from ai_lab_platform.conversation import BillingClass
from ai_lab_platform.model_catalog import resolve_smart_model
from ai_lab_platform.model_router import CompletionResponse, ModelRouter
from ai_lab_platform.policy import load_policy
from ai_lab_platform.tool_runtime import execute_allowed_tool
from ai_lab_platform.tools import ToolContext


class HybridWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.ctx = ToolContext(
            workspace_root=self.root,
            artifact_root=self.root / "artifacts",
        )
        self.policy = load_policy("personal")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_personal_policy_includes_consult_frontier(self) -> None:
        self.assertIn("consult_frontier", self.policy.allowed_tools)

    def test_resolve_smart_model_handles_hybrid(self) -> None:
        model, backend = resolve_smart_model("Build an executive presentation", "ollama::hybrid", ["qwen3.6:35b-a3b"])
        self.assertEqual(backend, "ollama")
        self.assertEqual(model, "qwen3.6:35b-a3b")

        model2, backend2 = resolve_smart_model("Strategic analysis", "hybrid", ["llama3.2:3b"])
        self.assertEqual(backend2, "ollama")
        self.assertEqual(model2, "llama3.2:3b")

    def test_consult_frontier_executes_with_router(self) -> None:
        mock_router = MagicMock(spec=ModelRouter)
        mock_router.list_providers.return_value = [
            {
                "id": "openai",
                "billing_class": "usage_billed_api",
                "enabled": True,
                "models": ["gpt-4o"],
            }
        ]
        mock_router.complete.return_value = CompletionResponse(
            model="gpt-4o",
            backend="openai",
            text="# Executive Slide Deck\n- Point 1\n- Point 2",
            billing_class=BillingClass.USAGE_BILLED_API,
        )
        self.ctx.model_router = mock_router

        result = execute_allowed_tool(
            "consult_frontier",
            {
                "task": "Create 5 slide presentation on Cisco strategy",
                "context": "Local search found revenue of $53.8B and security growth +14%",
                "backend": "openai",
            },
            allowed_tools=list(self.policy.allowed_tools),
            approved_tools={"consult_frontier"},
            ctx=self.ctx,
        )

        self.assertTrue(result.ok)
        self.assertIn("Frontier Consultation Result (openai :: gpt-4o)", result.observation)
        self.assertIn("Executive Slide Deck", result.observation)

        # Verify that router complete was invoked with combined context
        call_req = mock_router.complete.call_args[0][0]
        self.assertEqual(call_req.backend, "openai")
        self.assertEqual(call_req.model, "gpt-4o")
        self.assertIn("Context and data gathered locally by agent:", call_req.prompt)
        self.assertIn("Local search found revenue of $53.8B", call_req.prompt)
        self.assertIn("Create 5 slide presentation on Cisco strategy", call_req.prompt)

    def test_consult_frontier_fails_closed_when_cloud_unauthorized(self) -> None:
        mock_router = MagicMock(spec=ModelRouter)
        mock_router.list_providers.return_value = [
            {
                "id": "openai",
                "billing_class": "usage_billed_api",
                "enabled": False,
                "models": [],
            }
        ]
        mock_store = MagicMock()
        mock_store.usage_billed_authorized.return_value = False
        mock_router.secret_store = mock_store
        self.ctx.model_router = mock_router

        result = execute_allowed_tool(
            "consult_frontier",
            {"task": "Summarize strategy"},
            allowed_tools=list(self.policy.allowed_tools),
            approved_tools={"consult_frontier"},
            ctx=self.ctx,
        )

        self.assertTrue(result.ok)
        self.assertIn("Frontier models are disabled until authorized on /secrets", result.observation)


if __name__ == "__main__":
    unittest.main()
