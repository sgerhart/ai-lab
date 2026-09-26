"""DefenseClaw summary parsing and the Security posture API."""

from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.defenseclaw_glossary import explain_rule  # noqa: E402
from ai_lab_platform.defenseclaw_report import (  # noqa: E402
    PostureFile,
    build_report,
    episode_card,
    narrate_episode,
    posture_view,
    read_block_episodes,
    read_decision_summary,
    read_finding_summary,
)

VERSION = """
  cli        0.8.10           ok       defenseclaw (python)
  gateway    0.8.10           ok       /Users/someone/.local/bin/defenseclaw-gateway
"""

STATUS = """
    Blocked skills:  0
    Allowed skills:  1
    Blocked MCPs:    2
    Allowed MCPs:    3
    Total scans:     10
    Active alerts:   4
"""

ALERTS = """
│ 1 │ LOW      │ 13:23 │ scan-finding │        │ finding.observed   │
"""

CONFIG = """
claw:
  mode: antigravity
guardrail:
  enabled: true
  mode: action
  hook_fail_mode: open
  connectors:
    cursor:
      mode: action
      hilt:
        enabled: true
        min_severity: HIGH
llm:
  api_key_env: DEFENSECLAW_LLM_KEY
  api_key: sk-live-notreally
ai_discovery:
  enabled: true
  mode: enhanced
  scan_roots:
  - '~'
"""

GUARDRAIL = """
  • enabled:    yes
      Connector    Key          State    Mode    Fail  Rule pack  HILT     Scan        Judge
      Cursor       cursor       enabled  action  open  default    on@HIGH  regex_only  off
  • port:       4000
"""

STATUS_AGENTS = STATUS + """
  Scanners
  --------
    skill-scanner   installed
    codeguard       built-in
  Sidecar:      running
                Cursor (cursor) - mode=action fail-mode=open provenance=config source=manual - RUNNING
                  requests: 10  errors: 1  tool inspections: 4  tool blocks: 2  subprocess blocks: 0
"""


class ParseTests(unittest.TestCase):
    def test_report_keeps_counts_and_drops_secrets(self) -> None:
        report = build_report(version_text=VERSION, status_text=STATUS, alerts_text=ALERTS)
        self.assertEqual(report["version"]["cli"], "0.8.10")
        self.assertEqual(report["version"]["gateway_status"], "ok")
        self.assertEqual(report["summary"]["active_alerts"], 4)
        self.assertEqual(report["summary"]["total_scans"], 10)
        self.assertEqual(report["alerts"][0]["severity"], "LOW")
        self.assertNotIn("/Users/someone", str(report["version"]))

    def test_secret_value_is_refused(self) -> None:
        dirty = STATUS + "\n    note: sk-live-secretvalue"
        with self.assertRaises(ValueError):
            build_report(version_text=VERSION, status_text=dirty, alerts_text=ALERTS)

    def test_config_keeps_env_names_and_withholds_secrets(self) -> None:
        report = build_report(
            version_text=VERSION,
            status_text=STATUS_AGENTS,
            alerts_text=ALERTS,
            guardrail_text=GUARDRAIL,
            config_text=CONFIG,
        )
        self.assertEqual(report["config"]["llm"]["api_key_env"], "DEFENSECLAW_LLM_KEY")
        self.assertEqual(report["config"]["llm"]["api_key"], "[withheld]")
        self.assertEqual(report["config"]["claw"]["mode"], "antigravity")
        self.assertEqual(report["config"]["ai_discovery"]["scan_roots"], ["~"])
        self.assertEqual(report["guardrail"]["connectors"][0]["hilt"], "on@HIGH")
        self.assertEqual(report["runtime"]["agents"][0]["blocks"], 2)
        self.assertEqual(report["runtime"]["sidecar"], "running")
        self.assertNotIn("sk-live", json.dumps(report))

    def test_finding_titles_come_from_the_audit_table(self) -> None:
        db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        db.close()
        con = sqlite3.connect(db.name)
        con.execute(
            """
            CREATE TABLE scan_findings (
              severity TEXT, title TEXT, rule_id TEXT, target TEXT,
              timestamp TEXT, evidence_summary TEXT
            )
            """
        )
        con.execute(
            "INSERT INTO scan_findings VALUES (?,?,?,?,?,?)",
            ("HIGH", "AGENTS.md access", "COG-AGENTS-MD", "cursor:beforeReadFile", "2026-09-25T13:26:08Z", "ok"),
        )
        con.commit()
        con.close()
        findings = read_finding_summary(db.name)
        self.assertEqual(findings["by_title"][0]["title"], "AGENTS.md access")
        self.assertEqual(findings["recent"][0]["where"], "cursor:beforeReadFile")

    def test_glossary_explains_known_rule_and_falls_back(self) -> None:
        known = explain_rule("CMD-ENV-DUMP")
        self.assertTrue(known["meaning"])
        self.assertNotIn("|", known["meaning"])
        self.assertNotIn(" -c", known["meaning"])
        missing = explain_rule("NO-SUCH-RULE")
        self.assertIn("No explanation for this rule yet.", missing["meaning"])
        self.assertIn("NO-SUCH-RULE", missing["meaning"])

    def test_inventory_rows_collapse_to_one_card(self) -> None:
        findings = {"by_title": [], "recent": []}
        for index in range(7):
            findings["by_title"].append(
                {
                    "severity": "INFO",
                    "title": f"Inventory {index}",
                    "rule": f"aibom-claw.finding.item-{index}",
                    "count": 1,
                }
            )
        findings["by_title"].append(
            {"severity": "HIGH", "title": "Environment variable dump", "rule": "CMD-ENV-DUMP", "count": 3}
        )
        report = build_report(version_text=VERSION, status_text=STATUS, alerts_text=ALERTS, findings=findings)
        view = posture_view(report)
        titles = [row["title"] for row in view["report"]["findings"]["by_title"]]
        self.assertEqual(titles.count("Inventory"), 1)
        self.assertNotIn("Inventory 0", titles)
        inventory = next(row for row in view["report"]["findings"]["by_title"] if row["title"] == "Inventory")
        self.assertEqual(inventory["count"], 7)
        self.assertEqual(inventory["class"], "inventory")
        dump = next(row for row in view["report"]["findings"]["by_title"] if row["rule"] == "CMD-ENV-DUMP")
        self.assertIn("environment", dump["meaning"].lower())

    def test_decisions_drop_match_text(self) -> None:
        db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        db.close()
        con = sqlite3.connect(db.name)
        con.execute("CREATE TABLE audit_events (timestamp TEXT, event_name TEXT, payload_json TEXT)")
        reason = "matched curl example into a shell"
        payload = json.dumps(
            {
                "defenseclaw.guardrail.effective_action": "block",
                "defenseclaw.guardrail.rule_ids": ["CMD-ENV-DUMP"],
                "defenseclaw.guardrail.reason": reason,
                "defenseclaw.hook.event": "beforeReadFile",
                "defenseclaw.security.severity": "HIGH",
            }
        )
        con.execute(
            "INSERT INTO audit_events VALUES (?,?,?)",
            ("2026-09-25T16:46:52Z", "hook_decision", payload),
        )
        con.execute(
            "INSERT INTO audit_events VALUES (?,?,?)",
            (
                "2026-09-25T16:00:00Z",
                "hook_decision",
                json.dumps({"defenseclaw.guardrail.effective_action": "allow", "defenseclaw.guardrail.reason": reason}),
            ),
        )
        con.commit()
        con.close()
        decisions = read_decision_summary(db.name)
        self.assertEqual(len(decisions), 1)
        self.assertEqual(set(decisions[0]), {"action", "rule", "hook", "severity", "count", "latest"})
        self.assertEqual(decisions[0]["action"], "block")
        self.assertEqual(decisions[0]["rule"], "CMD-ENV-DUMP")
        self.assertEqual(decisions[0]["count"], 1)
        posted = json.dumps(
            build_report(
                version_text=VERSION,
                status_text=STATUS,
                alerts_text=ALERTS,
                decisions=decisions,
            )
        )
        self.assertNotIn("reason", posted)
        self.assertNotIn("curl", posted)

    def test_block_episode_says_the_turn_continued(self) -> None:
        db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        db.close()
        con = sqlite3.connect(db.name)
        con.execute(
            "CREATE TABLE audit_events (timestamp TEXT, event_name TEXT, turn_id TEXT, payload_json TEXT)"
        )
        reason = "matched curl example into a shell"
        block = json.dumps(
            {
                "defenseclaw.guardrail.effective_action": "block",
                "defenseclaw.guardrail.enforced": True,
                "defenseclaw.guardrail.rule_ids": ["CMD-ENV-DUMP"],
                "defenseclaw.guardrail.reason": reason,
                "defenseclaw.hook.event": "beforeReadFile",
                "defenseclaw.security.severity": "HIGH",
            }
        )
        con.execute(
            "INSERT INTO audit_events VALUES (?,?,?,?)",
            ("2026-09-25T15:37:20Z", "hook_decision", "turn-1", block),
        )
        con.execute(
            "INSERT INTO audit_events VALUES (?,?,?,?)",
            ("2026-09-25T15:46:39Z", "tool.invocation.completed", "turn-1", "{}"),
        )
        con.execute(
            "INSERT INTO audit_events VALUES (?,?,?,?)",
            ("2026-09-25T15:47:34Z", "turn_end", "turn-1", "{}"),
        )
        con.commit()
        con.close()
        episodes = read_block_episodes(db.name)
        self.assertEqual(len(episodes), 1)
        self.assertEqual(episodes[0]["later_completed"], 1)
        self.assertTrue(episodes[0]["turn_ended"])
        self.assertNotIn("reason", episodes[0])
        posted = json.dumps(
            build_report(version_text=VERSION, status_text=STATUS, alerts_text=ALERTS, episodes=episodes)
        )
        self.assertNotIn("curl", posted)
        view = posture_view(
            build_report(version_text=VERSION, status_text=STATUS, alerts_text=ALERTS, episodes=episodes)
        )
        narration = view["report"]["episodes"][0]["narration"]
        self.assertIn("did not run", narration)
        self.assertIn("finished a reply", narration)
        self.assertIn("not proof the task was correct", narration)
        self.assertNotIn("curl", narration)

    def test_explain_drops_match_text_and_refuses_secrets(self) -> None:
        card = episode_card(
            {
                "action": "block",
                "rules": ["PATH-SSH-KEY"],
                "hook": "beforeReadFile",
                "enforced": True,
                "later_completed": 2,
                "turn_ended": True,
                "reason": "matched private key path",
            }
        )
        self.assertNotIn("reason", card)
        text = narrate_episode(card)
        self.assertNotIn("private key path", text)
        with self.assertRaises(ValueError):
            episode_card({"action": "block", "rules": ["sk-live-secretvalue"], "hook": "beforeReadFile"})

    def test_secret_in_a_decision_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            build_report(
                version_text=VERSION,
                status_text=STATUS,
                alerts_text=ALERTS,
                decisions=[{"action": "block", "rule": "sk-live-secretvalue", "hook": "beforeReadFile", "severity": "HIGH", "count": 1, "latest": "2026-09-25T00:00:00Z"}],
            )


class PostureApiTests(unittest.TestCase):
    def setUp(self) -> None:
        from fastapi.testclient import TestClient
        from ai_lab_platform.control_app import create_control_app
        from ai_lab_platform.settings import Settings
        from ai_lab_platform.store import SqliteStore

        self.tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
        self.tmp.close()
        self.posture = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.posture.close()
        Path(self.posture.name).unlink()
        settings = Settings(api_token="lab-token")
        app = create_control_app(store=SqliteStore(self.tmp.name), token="lab-token", settings=settings)
        app.state.security_posture = PostureFile(self.posture.name)
        self.client = TestClient(app)
        self.headers = {"Authorization": "Bearer lab-token"}

    def test_empty_then_store(self) -> None:
        empty = self.client.get("/v1/security/posture", headers=self.headers)
        self.assertEqual(empty.status_code, 200)
        self.assertFalse(empty.json()["ok"])
        report = build_report(version_text=VERSION, status_text=STATUS, alerts_text=ALERTS)
        saved = self.client.post("/v1/security/posture", headers=self.headers, json=report)
        self.assertEqual(saved.status_code, 200)
        body = saved.json()
        self.assertTrue(body["ok"])
        self.assertFalse(body["stale"])
        self.assertEqual(body["report"]["summary"]["blocked_mcps"], 2)

    def test_old_report_is_stale(self) -> None:
        old = (datetime.now(timezone.utc) - timedelta(hours=2)).replace(microsecond=0).isoformat()
        report = build_report(
            version_text=VERSION,
            status_text=STATUS,
            alerts_text=ALERTS,
            reported_at=old,
        )
        report["received_at"] = old
        view = posture_view(report, now=datetime.now(timezone.utc))
        self.assertTrue(view["stale"])

    def test_explain_uses_the_card_not_the_match_text(self) -> None:
        saved = self.client.post(
            "/v1/security/explain",
            headers=self.headers,
            json={
                "action": "block",
                "rules": ["CMD-ENV-DUMP"],
                "hook": "beforeReadFile",
                "enforced": True,
                "later_completed": 3,
                "turn_ended": True,
                "reason": "matched curl example into a shell",
            },
        )
        self.assertEqual(saved.status_code, 200)
        body = saved.json()
        self.assertIn("explanation", body)
        self.assertNotIn("curl", json.dumps(body))


if __name__ == "__main__":
    unittest.main()
