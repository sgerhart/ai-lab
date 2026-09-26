"""Scoring for the Studio model comparison. Does not call Ollama."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.model_bench import load_cases, score_case, score_text  # noqa: E402


class BenchScoreTests(unittest.TestCase):
    def test_text_accepts_digits_inside_a_sentence(self) -> None:
        self.assertTrue(score_text("The answer is 437.", "437"))
        self.assertTrue(score_text("ready", "ready"))
        self.assertFalse(score_text("not yet", "ready"))

    def test_code_runs_the_named_function(self) -> None:
        reply = "```python\ndef add(a, b):\n    return a + b\n```"
        scored = score_case(
            {"id": "add", "kind": "code", "function": "add", "calls": [[2, 3]], "expect": [5]},
            reply,
        )
        self.assertTrue(scored["ok"])

    def test_code_refuses_imports(self) -> None:
        reply = "```python\nimport os\ndef add(a, b):\n    return a + b\n```"
        scored = score_case(
            {"id": "add", "kind": "code", "function": "add", "calls": [[1, 1]], "expect": [2]},
            reply,
        )
        self.assertFalse(scored["ok"])
        self.assertEqual(scored["note"], "refused")

    def test_fixture_covers_both_tracks(self) -> None:
        kinds = {case["kind"] for case in load_cases()}
        self.assertEqual(kinds, {"text", "code"})


if __name__ == "__main__":
    unittest.main()
