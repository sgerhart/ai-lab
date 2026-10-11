"""CWE means Common Weakness Enumeration, and each id keeps its MITRE name."""

from __future__ import annotations

import unittest
from pathlib import Path

from ai_lab_platform.cwe_glossary import STANDS_FOR, UNKNOWN, catalog_payload, explain


class CweGlossaryTests(unittest.TestCase):
    def test_acronym_and_known_class(self) -> None:
        self.assertEqual(STANDS_FOR, "Common Weakness Enumeration")
        row = explain("cwe-78")
        self.assertEqual(row["id"], "CWE-78")
        self.assertIn("OS Command Injection", row["name"])
        self.assertIn("OS command", row["meaning"])
        privilege = explain("269")
        self.assertEqual(privilege["name"], "Improper Privilege Management")

    def test_unknown_class_is_not_invented(self) -> None:
        row = explain("CWE-999999")
        self.assertEqual(row["name"], "")
        self.assertEqual(row["meaning"], UNKNOWN)

    def test_notice_travels_with_the_copy(self) -> None:
        notice = Path("platform/src/ai_lab_platform/data/CWE_NOTICE.txt").read_text(encoding="utf-8")
        self.assertIn("The MITRE Corporation", notice)
        payload = catalog_payload()
        self.assertEqual(payload["stands_for"], STANDS_FOR)
        classes = payload["classes"]
        self.assertIn("CWE-269", classes)
        self.assertNotIn("potential_mitigations", classes["CWE-269"])


if __name__ == "__main__":
    unittest.main()
