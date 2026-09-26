"""Operator prose for DefenseClaw rule ids.

Sentences describe what a rule is for. They do not include match patterns.
"""

from __future__ import annotations

from typing import Any

FALLBACK = "No explanation for this rule yet."

INVENTORY: dict[str, str] = {
    "meaning": "This is an inventory count of skills, plugins, tools, or MCP servers DefenseClaw saw. It is not an enforcement decision.",
    "usual_case": "The same inventory lines repeat on every scan, including zeros.",
    "class": "inventory",
}

# meaning, usual_case. class is enforcement unless noted.
_ENTRIES: dict[str, tuple[str, str]] = {
    "CMD-ENV-DUMP": (
        "A command that prints the process environment, which can include secrets.",
        "Lab scripts sometimes print the environment while debugging a shell step.",
    ),
    "CMD-PYTHON-C": (
        "Python started with a program passed on the command line.",
        "One-off checks in this lab often run a short inline Python program.",
    ),
    "CMD-EVAL": (
        "A shell asked to evaluate a string that was assembled at runtime.",
        "Uncommon in normal editing. Worth a look when it appears.",
    ),
    "CMD-RM-RF": (
        "A recursive delete aimed at a filesystem root or another critical path.",
        "Uncommon in normal editing. Worth a look when it appears.",
    ),
    "CMD-PIPE-CURL": (
        "Fetched content handed straight to a shell interpreter.",
        "Uncommon in normal editing. Worth a look when it appears.",
    ),
    "CMD-NETCAT-LISTEN": (
        "A network tool started so it can accept an inbound connection.",
        "Uncommon in normal editing. Worth a look when it appears.",
    ),
    "CMD-SOCAT-EXEC": (
        "A socket tool started in a mode that runs a program.",
        "Uncommon in normal editing. Worth a look when it appears.",
    ),
    "COG-AGENTS-MD": (
        "A read or write of the lab agent instructions file.",
        "Cursor and other agents open that file on almost every task in this repo.",
    ),
    "COG-MEMORY": (
        "A read or write of an agent memory file.",
        "Agents open memory notes while resuming a task.",
    ),
    "COG-IDENTITY": (
        "A read or write of an agent identity file.",
        "Uncommon. Worth a look, because that file is meant to stay small and stable.",
    ),
    "COG-CLAUDE-MD": (
        "A read or write of a Claude project instructions file.",
        "Expected when an agent session is using those instructions.",
    ),
    "COG-SOUL": (
        "A read or write of an agent persona file.",
        "Expected only in projects that keep a persona file.",
    ),
    "COG-TOOLS-MD": (
        "A read or write of an agent tools list.",
        "Expected when an agent session loads its tool instructions.",
    ),
    "PATH-SSH-DIR": (
        "A path inside the SSH configuration directory.",
        "Sometimes a tool lists that directory. A read of a key file is a different rule.",
    ),
    "PATH-SSH-KEY": (
        "A path that points at a private key file.",
        "Uncommon in normal editing. Worth a look when it appears.",
    ),
    "PATH-ENV-FILE": (
        "A path that points at an environment file, which often holds secrets.",
        "Opening a local env file to check a setting is a common lab case.",
    ),
    "CG-NET-001": (
        "An outbound web request whose address was built from a variable.",
        "Lab code that calls a host from configuration can trip this.",
    ),
    "CG-PATH-001": (
        "A path that may climb out of the directory it was meant to stay in.",
        "Path joins in scripts can look like this without leaving the repo.",
    ),
    "CG-EXEC-001": (
        "A command built from outside text and handed to a shell.",
        "Uncommon in normal editing. Worth a look when it appears.",
    ),
    "CG-SQL-001": (
        "A database query built by pasting text into the statement.",
        "Uncommon in normal editing. Worth a look when it appears.",
    ),
    "CORR-DESTRUCTIVE-FLOW": (
        "Several steps in one session lined up as a destructive sequence.",
        "The row may have no extra evidence. Read the nearby blocks and confirms.",
    ),
    "CORR-ESCALATION-CHAIN": (
        "Several steps in one session lined up as a privilege or access escalation.",
        "The row may have no extra evidence. Read the nearby blocks and confirms.",
    ),
    "ENT-CC-VISA": (
        "Text shaped like a payment card number.",
        "A test fixture or a redacted sample can trip this. Confirm it is not a real number.",
    ),
}


def explain_rule(rule_id: str) -> dict[str, str]:
    """Return meaning, usual_case, and class for one rule id."""
    rule = (rule_id or "").strip()
    if rule.startswith("aibom-"):
        return dict(INVENTORY)
    entry = _ENTRIES.get(rule)
    if entry is None:
        meaning = f"{FALLBACK} {rule}".strip()
        return {"meaning": meaning, "usual_case": "", "class": "enforcement"}
    meaning, usual = entry
    return {"meaning": meaning, "usual_case": usual, "class": "enforcement"}


def annotate_row(row: dict[str, Any], *, rule_key: str = "rule") -> dict[str, Any]:
    explained = dict(row)
    explained.update(explain_rule(str(row.get(rule_key) or "")))
    return explained
