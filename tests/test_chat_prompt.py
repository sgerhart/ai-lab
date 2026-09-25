"""Chat prompts keep attached files on later turns while they fit."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.attachments import (  # noqa: E402
    DEFAULT_CONTEXT_TOKENS,
    build_chat_prompt,
    prompt_char_budget,
)


class ChatPromptTests(unittest.TestCase):
    def test_later_turn_still_includes_the_file(self) -> None:
        files = {"a": "[attachment notes.md]\nWork orders structure the work."}

        def attachment_text(ids):
            return "\n".join(files[i] for i in ids if i in files)

        prompt = build_chat_prompt(
            [
                ("user", "What does the attached blog post talk about?", ["a"]),
                ("assistant", "It is about work orders.", []),
                ("user", "Give me 3 important points.", []),
            ],
            attachment_text,
        )
        self.assertIn("Work orders structure the work.", prompt)
        self.assertIn("Give me 3 important points.", prompt)
        self.assertLess(prompt.index("Work orders"), prompt.index("Give me 3"))

    def test_oldest_file_drops_when_the_window_is_full(self) -> None:
        def attachment_text(ids):
            return "FILE-" + ids[0] + ("x" * 80)

        prompt = build_chat_prompt(
            [
                ("user", "first", ["old"]),
                ("assistant", "ok", []),
                ("user", "second question", ["new"]),
            ],
            attachment_text,
            max_chars=120,
        )
        self.assertIn("FILE-new", prompt)
        self.assertNotIn("FILE-old", prompt)
        self.assertIn("second question", prompt)

    def test_budget_is_the_default_window_minus_a_reply(self) -> None:
        self.assertEqual(DEFAULT_CONTEXT_TOKENS, 131072)
        self.assertEqual(prompt_char_budget(), (131072 - 2048) * 4)


if __name__ == "__main__":
    unittest.main()
