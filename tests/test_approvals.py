import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.approvals import requires_approval
from ai_lab_platform.model_router import CompletionRequest, ModelRouter


class ApprovalsTests(unittest.TestCase):
    def test_unknown_tool_needs_approval(self) -> None:
        self.assertTrue(requires_approval("rm_rf", ["repo_read"], set()))

    def test_approved_privileged(self) -> None:
        self.assertFalse(requires_approval("git_push", ["git_push"], {"git_push"}))


class RouterTests(unittest.TestCase):
    def test_fake_backend(self) -> None:
        router = ModelRouter()
        resp = router.complete(CompletionRequest(model="local-test", prompt="hello", backend="ollama"))
        self.assertIn("fake:ollama", resp.text)


if __name__ == "__main__":
    unittest.main()
