"""Antares leads become draft Work Orders. None are confirmed."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

from ai_lab_platform.antares_handoff import build_handoff

ROOT = Path(__file__).resolve().parents[1]


def _server():
    path = ROOT / "scripts" / "antares-job-server.py"
    spec = importlib.util.spec_from_file_location("antares_job_server", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class HandoffTests(unittest.TestCase):
    def test_groups_uncertain_leads_and_rejects_missing_files(self) -> None:
        handoff = build_handoff(
            run_id="c3203fc3c8ce",
            source_url="git@github.com:dentroio/agentic-factory.git",
            findings=[
                {"file_path": "services/runner.py", "cwe_ids": ["CWE-269"], "title": "Improper Privilege Management"},
                {"file_path": "missing.py", "cwe_ids": ["CWE-328"], "title": "Use of Weak Hash"},
                {"file_path": "../secrets.env", "cwe_ids": ["CWE-312"], "title": "Cleartext storage"},
            ],
            summary={"failed_workers": 14, "failed_tool_calls": 562},
            present={"services/runner.py": True, "missing.py": False},
        )
        self.assertEqual(handoff["confirmed"], 0)
        self.assertEqual(handoff["uncertain"], 1)
        self.assertEqual(handoff["rejected"], 2)
        self.assertFalse(handoff["implement"])
        self.assertEqual(handoff["repository"], "dentroio/agentic-factory")
        self.assertEqual([order["priority"] for order in handoff["orders"]], ["P0"])
        text = handoff["orders"][0]["markdown"]
        self.assertIn("**Status:** Draft", text)
        self.assertIn("services/runner.py", text)
        self.assertNotIn("missing.py", text)
        self.assertNotIn("../secrets.env", text)
        self.assertIn("Readiness Review", text)
        self.assertIn("14 failed class workers", handoff["summary"])
        self.assertIn("0 confirmed", handoff["summary"])

    def test_a_detailed_review_keeps_its_line_and_verdict(self) -> None:
        handoff = build_handoff(
            run_id="d6886cb6c64d",
            source_url="git@github.com:dentroio/agentic-factory.git",
            findings=[
                {
                    "file_path": "services/agent-runner/prompt_builder.py",
                    "cwe": "CWE-94",
                    "title": "Code Injection",
                    "verdict": "confirmed",
                    "line": 11,
                    "reason": "The assignment copies the directory of the current file.",
                }
            ],
            summary={"failed_workers": 14, "failed_tool_calls": 474},
            present={"services/agent-runner/prompt_builder.py": True},
        )
        row = handoff["triage"][0]
        self.assertEqual(handoff["confirmed"], 1)
        self.assertEqual(row["line"], "11")
        self.assertEqual(row["verdict"], "confirmed")
        self.assertNotIn("no line and no excerpt", row["reason"])
        self.assertIn("line 11", handoff["orders"][0]["markdown"])
        self.assertIn("1 confirmed", handoff["summary"])

    def test_presence_stays_inside_the_snapshot(self) -> None:
        import tempfile

        server = _server()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "app.py").write_text("print('ok')\n", encoding="utf-8")
            present = server.paths_present(
                repo,
                ["app.py", "missing.py", "../app.py", "/etc/passwd"],
            )
        self.assertTrue(present["app.py"])
        self.assertFalse(present["missing.py"])
        self.assertFalse(present["../app.py"])
        self.assertFalse(present["/etc/passwd"])

    def test_a_saved_report_can_be_reloaded(self) -> None:
        import tempfile

        server = _server()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshots = root / "snapshots" / "dentroio" / "agentic-factory"
            snapshots.mkdir(parents=True)
            run = root / "runs" / "c3203fc3c8ce"
            run.mkdir(parents=True)
            (run / "report.json").write_text(
                '{"findings":[{"file_path":"app.py","cwe_ids":["CWE-269"]}],"summary":{"total_findings":1},"metadata":{"target":"agentic-factory"}}',
                encoding="utf-8",
            )
            server.SNAPSHOTS = snapshots.parent.parent
            server.RUNS_ROOT = root / "runs"
            jobs = server._saved_jobs()
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["status"], "completed")
        self.assertTrue(str(jobs[0]["repo"]).endswith("agentic-factory"))
        self.assertEqual(jobs[0]["source_url"], "git@github.com:dentroio/agentic-factory.git")
        self.assertEqual(len(jobs[0]["findings"]), 1)
        self.assertIsInstance(jobs[0]["created_at"], float)
        self.assertTrue(str(jobs[0]["output_dir"]).endswith("c3203fc3c8ce"))

    def test_publish_marks_a_security_audit_without_changing_code(self) -> None:
        import tempfile

        from ai_lab_platform.antares_handoff import publish_audit

        handoff = build_handoff(
            run_id="c3203fc3c8ce",
            source_url="git@github.com:dentroio/agentic-factory.git",
            findings=[{"file_path": "app.py", "cwe_ids": ["CWE-269"], "title": "Privilege"}],
            summary={},
            present={"app.py": True},
        )
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            orders = repo / "docs" / "work_orders"
            orders.mkdir(parents=True)
            (orders / "WO-1106.md").write_text("# existing\n", encoding="utf-8")
            progress = repo / "docs" / "project_management"
            progress.mkdir(parents=True)
            (progress / "PROGRESS.md").write_text("# Progress\n\n## Milestones\n\nLater.\n", encoding="utf-8")
            first = publish_audit(repo, handoff, today="2026-10-01")
            text = (repo / "docs/work_orders/WO-1107-security-audit-privilege.md").read_text(encoding="utf-8")
            readme = (repo / "docs/security-audits/README.md").read_text(encoding="utf-8")
            tracker = (repo / "docs/project_management/PROGRESS.md").read_text(encoding="utf-8")
            second = publish_audit(repo, handoff, today="2026-10-01")
        self.assertIn("docs/work_orders/WO-1107-security-audit-privilege.md", first["files"])
        self.assertTrue(first["branch"].startswith("security-audit/antares-"))
        self.assertIn("**Source:** Security Audit", text)
        self.assertIn("**Status:** Draft", text)
        self.assertIn("Security Audit", readme)
        self.assertIn("## Security audits", tracker)
        self.assertIn("WO-1107", tracker)
        self.assertLess(tracker.index("## Security audits"), tracker.index("## Milestones"))
        self.assertTrue(second["already_recorded"])
