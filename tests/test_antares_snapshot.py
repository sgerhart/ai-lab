"""GitHub snapshot rules and the blank-class sweep command."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "antares-job-server.py"


def _load():
    spec = importlib.util.spec_from_file_location("antares_job_server", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class SnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = _load()

    def test_https_github_url_has_no_credential(self) -> None:
        owner, repo, clone = self.mod.parse_github_repo("https://github.com/sgerhart/ai-lab.git")
        self.assertEqual((owner, repo), ("sgerhart", "ai-lab"))
        self.assertEqual(clone, "https://github.com/sgerhart/ai-lab.git")

    def test_ssh_github_url_stays_on_github(self) -> None:
        _owner, _repo, clone = self.mod.parse_github_repo("git@github.com:sgerhart/ai-lab.git")
        self.assertEqual(clone, "git@github.com:sgerhart/ai-lab.git")

    def test_credential_in_the_url_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.mod.parse_github_repo("https://token@github.com/sgerhart/ai-lab.git")

    def test_other_hosts_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.mod.parse_github_repo("https://example.com/sgerhart/ai-lab.git")

    def test_blank_class_uses_sweep(self) -> None:
        cmd, _timeout = self.mod.antares_command(
            repo=Path("/tmp/repo"),
            out_dir=Path("/tmp/out"),
            cwe="",
            profile="lab-antares-1b",
        )
        self.assertEqual(cmd[1], "sweep")
        self.assertNotIn("--cwe", cmd)
        self.assertIn("auto", cmd)

    def test_named_classes_stay_a_query(self) -> None:
        cmd, _timeout = self.mod.antares_command(
            repo=Path("/tmp/repo"),
            out_dir=Path("/tmp/out"),
            cwe="CWE-78,CWE-89",
            profile="lab-antares-1b",
        )
        self.assertEqual(cmd[1], "query")
        self.assertIn("CWE-78,CWE-89", cmd)


if __name__ == "__main__":
    unittest.main()
