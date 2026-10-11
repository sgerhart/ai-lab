"""A coding-model reply becomes a line-level finding, or it is discarded."""

from __future__ import annotations

import unittest

from ai_lab_platform.antares_detail import numbered_excerpt, parse_review, review_prompt


class DetailReviewTests(unittest.TestCase):
    def test_confirmed_line_must_exist(self) -> None:
        parsed = parse_review('{"verdict":"confirmed","line":2,"reason":"The function checks the role before the call."}', line_count=4)
        self.assertEqual(parsed["verdict"], "confirmed")
        self.assertEqual(parsed["line"], 2)

    def test_line_outside_the_file_is_uncertain(self) -> None:
        parsed = parse_review('{"verdict":"confirmed","line":40,"reason":"The check is skipped."}', line_count=4)
        self.assertEqual(parsed["verdict"], "uncertain")
        self.assertIsNone(parsed["line"])

    def test_attack_text_is_discarded(self) -> None:
        parsed = parse_review('{"verdict":"confirmed","line":2,"reason":"Send this payload to exploit the check."}', line_count=4)
        self.assertEqual(parsed["verdict"], "uncertain")
        self.assertNotIn("payload", parsed["reason"])

    def test_excerpt_is_numbered_and_bounded(self) -> None:
        excerpt, count = numbered_excerpt("a\nb\nc\n", limit=2)
        self.assertEqual(count, 3)
        self.assertIn("1|a", excerpt)
        self.assertIn("more lines", excerpt)
        self.assertIn("Do not describe an attack", review_prompt(path="app.py", cwe="CWE-269", title="Privilege", excerpt=excerpt))


if __name__ == "__main__":
    unittest.main()
