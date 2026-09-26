"""DefenseClaw posture for the mini Security page (ADR 0040).

The Air reads its own status, operator config, and finding titles, then sends
JSON. The mini does not keep config.yaml, the device key, or audit.db.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .defenseclaw_glossary import INVENTORY, annotate_row, explain_rule

STALE_AFTER_SEC = 15 * 60
_SECRET_KEY = re.compile(r"(secret|token|password|api[_-]?key|credential|private[_-]?key)", re.I)
_SECRET_VALUE = re.compile(r"(?i)(sk-|ghp_|github_pat_|xox[baprs]-|AKIA[0-9A-Z]{16}|BEGIN [A-Z ]*PRIVATE KEY)")
_ENV_NAME = re.compile(r"[A-Z][A-Z0-9_]{2,64}")
_CARDISH = re.compile(r"\b(?:\d[ -]?){13,19}\b")
_HOME = re.compile(r"/Users/[^\s'\"]+")
_AGENT_LINE = re.compile(
    r"^(?P<name>.+?)\s+\((?P<id>[a-z0-9_-]+)\)\s+-\s+mode=(?P<mode>\S+)\s+fail-mode=(?P<fail>\S+).+-\s+(?P<state>\S+)\s*$"
)
_AGENT_COUNTS = re.compile(
    r"requests:\s*(?P<requests>\d+)\s+errors:\s*(?P<errors>\d+).*tool inspections:\s*(?P<inspections>\d+)\s+tool blocks:\s*(?P<blocks>\d+)"
)
_VERSION_ROW = re.compile(
    r"^\s*(cli|gateway|plugin)\s{2,}(\S+)\s{2,}(\S+)",
    re.I | re.M,
)
_COUNT = re.compile(r"^\s*(Blocked skills|Allowed skills|Blocked MCPs|Allowed MCPs|Total scans|Active alerts):\s*(\d+)", re.I | re.M)


def utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _clip(value: str, limit: int = 180) -> str:
    text = " ".join((value or "").split())
    return text[:limit]


def parse_version(text: str) -> dict[str, str]:
    found: dict[str, str] = {}
    status: dict[str, str] = {}
    for match in _VERSION_ROW.finditer(text or ""):
        name = match.group(1).lower()
        found[name] = match.group(2)
        status[name] = match.group(3).lower()
    return {
        "cli": found.get("cli", ""),
        "gateway": found.get("gateway", ""),
        "gateway_status": status.get("gateway", ""),
    }


def parse_status(text: str) -> dict[str, Any]:
    counts: dict[str, int] = {}
    labels = {
        "blocked skills": "blocked_skills",
        "allowed skills": "allowed_skills",
        "blocked mcps": "blocked_mcps",
        "allowed mcps": "allowed_mcps",
        "total scans": "total_scans",
        "active alerts": "active_alerts",
    }
    for match in _COUNT.finditer(text or ""):
        key = labels.get(match.group(1).lower())
        if key:
            counts[key] = int(match.group(2))
    return counts


def parse_alerts(text: str, *, limit: int = 8) -> list[dict[str, str]]:
    """Read the table rows. Skip the header and rule lines."""
    rows: list[dict[str, str]] = []
    for line in (text or "").splitlines():
        if "│" not in line or "Severity" in line:
            continue
        parts = [part.strip() for part in line.strip("│ ").split("│")]
        if len(parts) < 6 or not parts[0].isdigit():
            continue
        rows.append(
            {
                "severity": _clip(parts[1], 16),
                "time": _clip(parts[2], 32),
                "action": _clip(parts[3], 64),
                "target": _clip(parts[4], 80),
                "detail": _clip(parts[5], 120),
            }
        )
        if len(rows) >= limit:
            break
    return rows


def parse_runtime(text: str) -> dict[str, Any]:
    """Scanners, sidecar, and per-agent counters from `defenseclaw status`."""
    scanners: list[dict[str, str]] = []
    overrides = ""
    agents: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    in_scanners = False
    runtime: dict[str, Any] = {
        "environment": "",
        "scope": "",
        "sandbox": "",
        "sidecar": "",
        "app_protect": "",
        "observability": "",
    }
    for raw in (text or "").splitlines():
        line = raw.strip()
        if line == "Scanners":
            in_scanners = True
            continue
        if line == "Enforcement":
            in_scanners = False
        if in_scanners and line and not set(line) <= {"-"}:
            name, _, rest = line.partition(" ")
            rest = rest.strip()
            if name == "overrides":
                overrides = _clip(rest, 400)
            elif name and rest and " " not in name:
                scanners.append({"name": name, "state": _clip(rest, 80)})
        if line.startswith("Environment:"):
            runtime["environment"] = _clip(line.split(":", 1)[1], 40)
        elif line.startswith("Scope:"):
            runtime["scope"] = _clip(line.split(":", 1)[1], 80)
        elif line.startswith("Sandbox:"):
            runtime["sandbox"] = _clip(line.split(":", 1)[1], 80)
        elif line.startswith("Sidecar:"):
            runtime["sidecar"] = _clip(line.split(":", 1)[1], 40)
        elif line.startswith("App protect:"):
            runtime["app_protect"] = _clip(line.split(":", 1)[1], 80)
        elif "retention:" in line and "plan:" in line:
            runtime["observability"] = _clip(line, 120)
        agent = _AGENT_LINE.match(line)
        if agent and "mode=" in line:
            current = {
                "name": _clip(agent.group("name"), 40),
                "id": agent.group("id"),
                "mode": agent.group("mode"),
                "fail_mode": agent.group("fail"),
                "state": agent.group("state"),
                "requests": 0,
                "errors": 0,
                "inspections": 0,
                "blocks": 0,
            }
            agents.append(current)
            continue
        counts = _AGENT_COUNTS.search(line)
        if counts and current is not None:
            current["requests"] = int(counts.group("requests"))
            current["errors"] = int(counts.group("errors"))
            current["inspections"] = int(counts.group("inspections"))
            current["blocks"] = int(counts.group("blocks"))
    runtime["scanners"] = scanners
    runtime["overrides"] = overrides
    runtime["agents"] = agents
    return runtime


def parse_guardrail(text: str) -> dict[str, Any]:
    enabled = ""
    port = ""
    connectors: list[dict[str, str]] = []
    for raw in (text or "").splitlines():
        line = raw.strip().lstrip("•").strip()
        if line.lower().startswith("enabled:"):
            enabled = _clip(line.split(":", 1)[1], 16)
        elif line.lower().startswith("port:"):
            port = _clip(line.split(":", 1)[1], 16)
        elif line.lower().startswith("connector"):
            continue
        parts = re.split(r"\s{2,}", line)
        if len(parts) >= 8 and set(parts[0]) <= {"-"}:
            continue
        if len(parts) >= 8 and re.fullmatch(r"[a-z0-9_-]+", parts[1]):
            connectors.append(
                {
                    "name": _clip(parts[0], 40),
                    "key": parts[1],
                    "state": parts[2],
                    "mode": parts[3],
                    "fail": parts[4],
                    "rules": parts[5],
                    "hilt": parts[6],
                    "scan": parts[7],
                    "judge": parts[8] if len(parts) > 8 else "",
                }
            )
    return {"enabled": enabled, "port": port, "connectors": connectors}


def parse_config(text: str) -> dict[str, Any]:
    """Operator settings. Secret values are withheld; env-var names stay."""
    parsed = _simple_yaml(text or "")
    if not isinstance(parsed, dict):
        return {}
    redacted = _redact_tree(parsed)
    return redacted if isinstance(redacted, dict) else {}


def read_finding_summary(db_path: str | Path, *, recent_limit: int = 40) -> dict[str, Any]:
    """Titles and rules from the Air audit DB. The database itself is not copied."""
    path = Path(db_path)
    if not path.is_file():
        return {"by_title": [], "recent": []}
    uri = f"file:{path}?mode=ro"
    con = sqlite3.connect(uri, uri=True)
    try:
        counts = [
            {
                "severity": str(sev or ""),
                "title": _clip(str(title or ""), 120),
                "rule": _clip(str(rule or ""), 64),
                "count": int(count),
            }
            for sev, title, rule, count in con.execute(
                """
                SELECT severity, title, rule_id, COUNT(*)
                FROM scan_findings
                GROUP BY severity, title, rule_id
                ORDER BY COUNT(*) DESC
                """
            )
        ]
        recent = [
            {
                "severity": str(sev or ""),
                "title": _clip(str(title or ""), 120),
                "rule": _clip(str(rule or ""), 64),
                "where": _clean_text(str(target or ""), 80),
                "when": _clip(str(stamp or ""), 32),
                "matched": _clean_text(str(evidence or ""), 80),
            }
            for sev, title, rule, target, stamp, evidence in con.execute(
                """
                SELECT severity, title, rule_id, target, timestamp, substr(evidence_summary, 1, 80)
                FROM scan_findings
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (recent_limit,),
            )
        ]
    except sqlite3.Error:
        return {"by_title": [], "recent": []}
    finally:
        con.close()
    return {"by_title": counts, "recent": recent}


_DECISION_ACTIONS = frozenset({"block", "confirm"})
_DECISION_FIELDS = ("action", "rule", "hook", "severity", "count", "latest")


def read_decision_summary(db_path: str | Path) -> list[dict[str, Any]]:
    """Block and confirm totals. Match text and the rest of the payload stay in the database."""
    path = Path(db_path)
    if not path.is_file():
        return []
    uri = f"file:{path}?mode=ro"
    con = sqlite3.connect(uri, uri=True)
    groups: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    try:
        rows = con.execute(
            """
            SELECT timestamp, payload_json
            FROM audit_events
            WHERE event_name = ?
            """,
            ("hook_decision",),
        )
        for stamp, payload in rows:
            parsed = _object(payload)
            if parsed is None:
                continue
            action = str(parsed.get("defenseclaw.guardrail.effective_action") or "")
            if action not in _DECISION_ACTIONS:
                continue
            rules = parsed.get("defenseclaw.guardrail.rule_ids")
            rule_ids = [str(rule) for rule in rules] if isinstance(rules, list) and rules else [""]
            hook = _clip(str(parsed.get("defenseclaw.hook.event") or ""), 64)
            severity = _clip(str(parsed.get("defenseclaw.security.severity") or ""), 16)
            when = _clip(str(stamp or ""), 32)
            for rule in rule_ids:
                rule_id = _clip(rule, 64)
                key = (action, rule_id, hook, severity)
                slot = groups.get(key)
                if slot is None:
                    groups[key] = {
                        "action": action,
                        "rule": rule_id,
                        "hook": hook,
                        "severity": severity,
                        "count": 1,
                        "latest": when,
                    }
                else:
                    slot["count"] = int(slot["count"]) + 1
                    if when > str(slot["latest"]):
                        slot["latest"] = when
    except sqlite3.Error:
        return []
    finally:
        con.close()
    ranked = sorted(groups.values(), key=lambda row: (0 if row["action"] == "block" else 1, -int(row["count"]), str(row["rule"])))
    return [{field: row[field] for field in _DECISION_FIELDS} for row in ranked]


_HOOK_PHRASE = {
    "beforeReadFile": "file read",
    "beforeShellExecution": "shell command",
    "preToolUse": "tool call",
    "afterFileEdit": "file edit",
    "postToolUse": "finished tool call",
}


def read_block_episodes(db_path: str | Path, *, limit: int = 8) -> list[dict[str, Any]]:
    """Recent blocks and confirms, plus whether that turn kept going.

    Match text stays in the database. A turn end means the agent finished a reply.
    """
    path = Path(db_path)
    if not path.is_file():
        return []
    uri = f"file:{path}?mode=ro"
    con = sqlite3.connect(uri, uri=True)
    try:
        hits: list[tuple[str, str, dict[str, Any]]] = []
        for stamp, turn_id, payload in con.execute(
            """
            SELECT timestamp, turn_id, payload_json
            FROM audit_events
            WHERE event_name = ?
            ORDER BY timestamp DESC
            """,
            ("hook_decision",),
        ):
            parsed = _object(payload)
            if parsed is None:
                continue
            action = str(parsed.get("defenseclaw.guardrail.effective_action") or "")
            if action not in _DECISION_ACTIONS:
                continue
            hits.append((str(stamp or ""), str(turn_id or ""), parsed))
            if len(hits) >= limit:
                break
        if not hits:
            return []
        turns = tuple({turn for _, turn, _ in hits if turn})
        aftermath: dict[str, list[tuple[str, str]]] = {turn: [] for turn in turns}
        if turns:
            marks = ",".join("?" * len(turns))
            for turn_id, stamp, event_name in con.execute(
                f"""
                SELECT turn_id, timestamp, event_name
                FROM audit_events
                WHERE turn_id IN ({marks})
                  AND event_name IN ('tool.invocation.completed', 'tool.invocation.failed', 'turn_end')
                """,
                turns,
            ):
                aftermath.setdefault(str(turn_id or ""), []).append((str(stamp or ""), str(event_name or "")))
    except sqlite3.Error:
        return []
    finally:
        con.close()
    episodes: list[dict[str, Any]] = []
    for stamp, turn_id, parsed in hits:
        rules = parsed.get("defenseclaw.guardrail.rule_ids")
        rule_ids = [_clip(str(rule), 64) for rule in rules] if isinstance(rules, list) else []
        later = aftermath.get(turn_id, [])
        episodes.append(
            {
                "when": _clip(stamp, 32),
                "action": str(parsed.get("defenseclaw.guardrail.effective_action") or ""),
                "rules": rule_ids,
                "hook": _clip(str(parsed.get("defenseclaw.hook.event") or ""), 64),
                "severity": _clip(str(parsed.get("defenseclaw.security.severity") or ""), 16),
                "enforced": bool(parsed.get("defenseclaw.guardrail.enforced")),
                "later_completed": sum(1 for when, name in later if when > stamp and name == "tool.invocation.completed"),
                "later_failed": sum(1 for when, name in later if when > stamp and name == "tool.invocation.failed"),
                "turn_ended": any(when >= stamp and name == "turn_end" for when, name in later),
            }
        )
    return episodes


def narrate_episode(episode: dict[str, Any]) -> str:
    """Say what the block did to the turn. Do not claim the task succeeded."""
    action = str(episode.get("action") or "decision")
    rules = [str(rule) for rule in (episode.get("rules") or []) if str(rule)]
    hook = _HOOK_PHRASE.get(str(episode.get("hook") or ""), "step")
    names = ", ".join(rules) or "an unnamed rule"
    if action == "block":
        lead = f"DefenseClaw blocked this {hook} ({names})."
        if episode.get("enforced"):
            lead += " That step did not run."
        else:
            lead += " The log does not mark the block as enforced, so the step may still have run."
    else:
        lead = f"DefenseClaw asked for confirmation before this {hook} ({names})."
    completed = int(episode.get("later_completed") or 0)
    failed = int(episode.get("later_failed") or 0)
    lead += f" After that, the same turn completed {completed} tool calls"
    if failed:
        lead += f" and {failed} failed"
    lead += "."
    if episode.get("turn_ended"):
        lead += " The turn then ended, so the agent finished a reply. That is not proof the task was correct."
    else:
        lead += " The log has no turn end after this, so it is not clear the agent finished."
    if rules:
        lead += " " + explain_rule(rules[0])["meaning"]
    return lead


_EPISODE_FIELDS = (
    "when",
    "action",
    "rules",
    "hook",
    "severity",
    "enforced",
    "later_completed",
    "later_failed",
    "turn_ended",
)


def episode_card(body: dict[str, Any]) -> dict[str, Any]:
    """Keep the fields an explainer may see. Drop match text and anything else."""
    if not isinstance(body, dict):
        raise ValueError("episode must be an object")
    rules = body.get("rules") or []
    if not isinstance(rules, list):
        raise ValueError("rules must be a list")
    card = {
        "when": _clip(str(body.get("when") or ""), 32),
        "action": _clip(str(body.get("action") or ""), 16),
        "rules": [_clip(str(rule), 64) for rule in rules[:8]],
        "hook": _clip(str(body.get("hook") or ""), 64),
        "severity": _clip(str(body.get("severity") or ""), 16),
        "enforced": bool(body.get("enforced")),
        "later_completed": int(body.get("later_completed") or 0),
        "later_failed": int(body.get("later_failed") or 0),
        "turn_ended": bool(body.get("turn_ended")),
    }
    assert_no_secrets(card)
    return {field: card[field] for field in _EPISODE_FIELDS}


def _object(payload: str | None) -> dict[str, Any] | None:
    if not payload:
        return None
    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict):
        return None
    return parsed


def _clean_text(value: str, limit: int) -> str:
    text = _HOME.sub("~/", value or "")
    text = _CARDISH.sub("[number withheld]", text)
    if _SECRET_VALUE.search(text):
        return ""
    return _clip(text, limit)


def _redact_tree(value: Any) -> Any:
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, item in value.items():
            name = str(key)
            if _SECRET_KEY.search(name):
                if isinstance(item, str) and _ENV_NAME.fullmatch(item.strip().strip("'\"")):
                    out[name] = item.strip().strip("'\"")
                else:
                    out[name] = "[withheld]"
                continue
            out[name] = _redact_tree(item)
        return out
    if isinstance(value, list):
        return [_redact_tree(item) for item in value]
    if isinstance(value, str):
        return _clean_text(value, 240)
    return value


def _simple_yaml(text: str) -> Any:
    """Enough YAML for DefenseClaw's short config.yaml. Not a general parser."""
    lines = [line for line in text.splitlines() if line.strip() and not line.strip().startswith("#")]
    index = 0

    def indent_of(pos: int) -> int:
        raw = lines[pos]
        return len(raw) - len(raw.lstrip(" "))

    def parse_list(item_indent: int) -> list[Any]:
        nonlocal index
        items: list[Any] = []
        while index < len(lines):
            if indent_of(index) != item_indent or not lines[index].strip().startswith("- "):
                break
            items.append(_scalar(lines[index].strip()[2:]))
            index += 1
        return items

    def parse_map(min_indent: int) -> dict[str, Any]:
        nonlocal index
        mapping: dict[str, Any] = {}
        while index < len(lines):
            if indent_of(index) != min_indent or lines[index].strip().startswith("- "):
                break
            key, _, rest = lines[index].strip().partition(":")
            key_indent = indent_of(index)
            index += 1
            rest = rest.strip()
            if rest not in {"", "|", ">"}:
                mapping[key.strip()] = _scalar(rest)
                continue
            if index < len(lines) and lines[index].strip().startswith("- ") and indent_of(index) >= key_indent:
                mapping[key.strip()] = parse_list(indent_of(index))
            elif index < len(lines) and indent_of(index) > key_indent:
                mapping[key.strip()] = parse_map(indent_of(index))
            else:
                mapping[key.strip()] = {}
        return mapping

    if not lines:
        return {}
    return parse_map(indent_of(0))


def _scalar(token: str) -> Any:
    token = token.strip()
    if token in {"{}", ""}:
        return {}
    if token == "[]":
        return []
    if len(token) >= 2 and token[0] == token[-1] and token[0] in {"'", '"'}:
        return token[1:-1]
    lowered = token.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"null", "~"}:
        return None
    if re.fullmatch(r"-?\d+", token):
        return int(token)
    return token


def build_report(
    *,
    version_text: str,
    status_text: str,
    alerts_text: str,
    guardrail_text: str = "",
    config_text: str = "",
    findings: dict[str, Any] | None = None,
    decisions: list[dict[str, Any]] | None = None,
    episodes: list[dict[str, Any]] | None = None,
    reported_at: str | None = None,
) -> dict[str, Any]:
    for blob in (version_text, status_text, alerts_text, guardrail_text):
        assert_no_secrets(blob)
    report = {
        "source": "defenseclaw",
        "host": "mac-air",
        "reported_at": reported_at or utcnow(),
        "version": parse_version(version_text),
        "summary": parse_status(status_text),
        "runtime": parse_runtime(status_text),
        "guardrail": parse_guardrail(guardrail_text),
        "config": parse_config(config_text),
        "findings": findings or {"by_title": [], "recent": []},
        "decisions": decisions or [],
        "episodes": episodes or [],
        "alerts": parse_alerts(alerts_text),
    }
    assert_no_secrets(report)
    return report


def assert_no_secrets(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if _SECRET_KEY.search(str(key)):
                if item == "[withheld]":
                    continue
                if isinstance(item, str) and _ENV_NAME.fullmatch(item):
                    continue
                raise ValueError(f"refusing key {key}")
            assert_no_secrets(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_no_secrets(item)
        return
    if isinstance(value, str) and _SECRET_VALUE.search(value):
        raise ValueError("refusing secret-like value")


class PostureFile:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def save(self, report: dict[str, Any], *, received_at: str | None = None) -> dict[str, Any]:
        assert_no_secrets(report)
        body = dict(report)
        body["received_at"] = received_at or utcnow()
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
        os.chmod(self.path, 0o600)
        return body

    def load(self) -> dict[str, Any] | None:
        if not self.path.is_file():
            return None
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return None
        return data


def _explained_report(report: dict[str, Any]) -> dict[str, Any]:
    """Attach glossary text for the page. Inventory rows become one card."""
    body = dict(report)
    findings = dict(body.get("findings") or {})
    kept: list[dict[str, Any]] = []
    inventory: list[dict[str, Any]] = []
    for row in findings.get("by_title") or []:
        if not isinstance(row, dict):
            continue
        explained = annotate_row(row)
        if explained.get("class") == "inventory":
            inventory.append(explained)
        else:
            kept.append(explained)
    if inventory:
        kept.append(
            {
                "severity": "INFO",
                "title": "Inventory",
                "rule": "aibom-",
                "count": sum(int(row.get("count") or 0) for row in inventory),
                "meaning": INVENTORY["meaning"],
                "usual_case": INVENTORY["usual_case"],
                "class": "inventory",
            }
        )
    findings["by_title"] = kept
    findings["recent"] = [
        annotate_row(row) for row in (findings.get("recent") or []) if isinstance(row, dict)
    ]
    body["findings"] = findings
    body["decisions"] = [
        annotate_row(row) for row in (body.get("decisions") or []) if isinstance(row, dict)
    ]
    explained_episodes: list[dict[str, Any]] = []
    for row in body.get("episodes") or []:
        if not isinstance(row, dict):
            continue
        episode = dict(row)
        episode["narration"] = narrate_episode(episode)
        explained_episodes.append(episode)
    body["episodes"] = explained_episodes
    return body


def posture_view(report: dict[str, Any] | None, *, now: datetime | None = None) -> dict[str, Any]:
    if not report:
        return {"ok": False, "stale": True, "note": "No DefenseClaw report yet.", "report": None}
    stamp = str(report.get("received_at") or report.get("reported_at") or "")
    age = _age_seconds(stamp, now or datetime.now(timezone.utc))
    stale = age is None or age > STALE_AFTER_SEC
    return {
        "ok": True,
        "stale": stale,
        "age_sec": age,
        "note": "Last Air report is stale." if stale else "Air report is current.",
        "report": _explained_report(report),
    }


def _age_seconds(stamp: str, now: datetime) -> int | None:
    if not stamp:
        return None
    try:
        seen = datetime.fromisoformat(stamp)
    except ValueError:
        return None
    if seen.tzinfo is None:
        seen = seen.replace(tzinfo=timezone.utc)
    return int((now - seen).total_seconds())


def default_posture_path() -> Path:
    override = os.environ.get("AI_LAB_SECURITY_POSTURE_PATH", "").strip()
    if override:
        return Path(override)
    return Path.home() / ".ai-lab" / "security-posture.json"
