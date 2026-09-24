"""Unit tests for Antares completions JSON shaping (no GPU)."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


def _load():
    path = Path(__file__).resolve().parents[1] / "scripts" / "antares-completions-server.py"
    spec = importlib.util.spec_from_file_location("antares_completions_server", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class CompletionsShapeTests(unittest.TestCase):
    def test_completion_response_shape(self) -> None:
        mod = _load()
        body = mod.completion_response(model="antares-1b", text="hello", finish_reason="stop")
        self.assertEqual(body["object"], "text_completion")
        self.assertEqual(body["model"], "antares-1b")
        self.assertEqual(body["choices"][0]["text"], "hello")
        self.assertEqual(body["choices"][0]["finish_reason"], "stop")
        self.assertTrue(str(body["id"]).startswith("cmpl-"))


if __name__ == "__main__":
    unittest.main()
