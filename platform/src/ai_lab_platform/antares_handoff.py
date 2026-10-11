"""Turn an Antares localization report into draft Work Orders.

Antares names files. This module does not confirm a defect, edit a repository,
or describe how to attack one. Drafts stay in Draft until a person accepts them.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

_P0 = "P0"
_P1 = "P1"

# Defensive next steps only. No reproduction steps.
_FAMILIES: tuple[dict[str, Any], ...] = (
    {
        "id": "privilege",
        "title": "Privilege and access checks",
        "priority": _P0,
        "cwes": frozenset({"CWE-269", "CWE-284", "CWE-285", "CWE-862", "CWE-863", "CWE-306", "CWE-282"}),
        "fix": "Confirm each cited action is limited to the intended role. Refuse it when the caller is not authorized, and add a test for that refusal.",
    },
    {
        "id": "secrets",
        "title": "Secrets, hashing, and transport",
        "priority": _P0,
        "cwes": frozenset({"CWE-312", "CWE-798", "CWE-319", "CWE-295", "CWE-327", "CWE-328", "CWE-326", "CWE-916", "CWE-759", "CWE-321", "CWE-522"}),
        "fix": "Keep secrets out of the cited code, logs, and URLs. Use the repository secret store and a current hash or certificate check. Add a test that the secret is not written out.",
    },
    {
        "id": "logs",
        "title": "Sensitive data in logs",
        "priority": _P0,
        "cwes": frozenset({"CWE-532", "CWE-117"}),
        "fix": "Stop writing the sensitive value into the log line. Add a test that the log record does not contain it.",
    },
    {
        "id": "injection",
        "title": "Command and query construction",
        "priority": _P0,
        "cwes": frozenset({"CWE-78", "CWE-77", "CWE-88", "CWE-89", "CWE-90", "CWE-943"}),
        "fix": "Do not pass the cited input through a command interpreter or a concatenated query. Use a fixed argument list or a parameterized query, and test that the untrusted input is refused.",
    },
    {
        "id": "redirect-path",
        "title": "Redirects and path access",
        "priority": _P1,
        "cwes": frozenset({"CWE-601", "CWE-22", "CWE-73", "CWE-36"}),
        "fix": "Allow only known destinations and paths inside the intended root. Reject the others and cover that with a test.",
    },
    {
        "id": "input",
        "title": "Input and output checks",
        "priority": _P1,
        "cwes": frozenset(),
        "fix": "Check the cited input before it is used, and add a test for the rejected value.",
    },
)

_FAMILY_BY_CWE = {
    cwe: family["id"]
    for family in _FAMILIES
    if family["id"] != "input"
    for cwe in family["cwes"]
}


def build_handoff(
    *,
    run_id: str,
    source_url: str,
    findings: list[Any],
    summary: dict[str, Any] | None,
    present: dict[str, bool],
) -> dict[str, Any]:
    """Group leads into draft Work Orders. None are confirmed."""
    rows = [_row(item, present) for item in findings if isinstance(item, dict)]
    confirmed = [row for row in rows if row["verdict"] == "confirmed"]
    rejected = [row for row in rows if row["verdict"] == "rejected"]
    uncertain = [row for row in rows if row["verdict"] == "uncertain"]
    orders = _orders(run_id, source_url, confirmed + uncertain)
    repo = _github_name(source_url) or "the product repository"
    scan = summary if isinstance(summary, dict) else {}
    return {
        "run_id": run_id,
        "repository": repo,
        "protocol_state": "Draft",
        "confirmed": len(confirmed),
        "uncertain": len(uncertain),
        "rejected": len(rejected),
        "summary": _summary(repo, rows, rejected, uncertain, confirmed, orders, scan),
        "rejected_findings": rejected,
        "triage": rows,
        "orders": orders,
        "implement": False,
    }


def _row(item: dict[str, Any], present: dict[str, bool]) -> dict[str, Any]:
    path = _safe_path(str(item.get("file_path") or ""))
    cwe = str(item.get("cwe") or "").strip().upper()
    if not cwe:
        cwes = [str(cwe_id).upper() for cwe_id in (item.get("cwe_ids") or []) if str(cwe_id).strip()]
        cwe = cwes[0] if cwes else ""
    title = " ".join(str(item.get("title") or cwe or "Untitled lead").split())[:160]
    family = _FAMILY_BY_CWE.get(cwe, "input")
    reviewed = _reviewed(item)
    if not path:
        verdict, line, reason = "rejected", "", "The finding has no repository path."
    elif path not in present:
        verdict, line, reason = reviewed or ("uncertain", "", "The Studio did not confirm this file.")
    elif not present[path]:
        verdict, line, reason = "rejected", "", "The cited path is not a file in the snapshot."
    elif reviewed:
        verdict, line, reason = reviewed
    else:
        verdict, line, reason = (
            "uncertain",
            "",
            "The file is in the snapshot. Antares recorded no line and no excerpt, so this is not confirmed.",
        )
    return {
        "file_path": path,
        "cwe": cwe,
        "title": title,
        "family": family,
        "verdict": verdict,
        "line": line,
        "reason": reason,
    }


def _reviewed(item: dict[str, Any]) -> tuple[str, str, str] | None:
    """Keep a finished detailed review. The line is the one that review recorded."""
    verdict = str(item.get("verdict") or "").strip().lower()
    if verdict not in {"confirmed", "rejected", "uncertain"}:
        return None
    reason = " ".join(str(item.get("reason") or "").split())[:240]
    if not reason:
        return None
    line_value = item.get("line")
    line = str(line_value) if isinstance(line_value, int) and not isinstance(line_value, bool) and line_value > 0 else ""
    if verdict in {"confirmed", "rejected"} and not line:
        return "uncertain", "", "The reviewer did not name a line in the file."
    return verdict, line, reason


def _safe_path(raw: str) -> str:
    path = raw.strip().replace("\\", "/")
    if not path or path.startswith("/") or path.startswith("~"):
        return ""
    parts = [part for part in path.split("/") if part and part != "."]
    if not parts or any(part == ".." for part in parts):
        return ""
    return "/".join(parts)[:240]


def _orders(run_id: str, source_url: str, rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    orders = []
    short = re.sub(r"[^a-f0-9]", "", run_id.lower())[:8] or "run"
    for family in _FAMILIES:
        grouped = [row for row in rows if row["family"] == family["id"]]
        if not grouped:
            continue
        order_id = f"WO-antares-{short}-{family['id']}"
        orders.append(
            {
                "id": order_id,
                "title": str(family["title"]),
                "priority": str(family["priority"]),
                "status": "Draft",
                "finding_count": str(len(grouped)),
                "markdown": _markdown(order_id, source_url, family, grouped),
            }
        )
    return orders


def _markdown(order_id: str, source_url: str, family: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    repo = _github_name(source_url) or "the product repository"
    named = [row for row in rows if row.get("line")]
    lines = [
        f"# {order_id} — {family['title']}",
        "",
        "**Status:** Draft",
        f"**Priority:** {family['priority']}",
        "**Owner:** human",
        f"**Repository:** {repo}",
        "",
        "## Problem",
        "",
        f"The detailed review kept {len(rows)} lead{'s' if len(rows) != 1 else ''} in {repo} for this group. "
        f"{len(named)} name a line.",
        "",
        "## What To Build / Fix",
        "",
        str(family["fix"]),
        "A person accepts this order before any code change.",
        "",
        "## Out Of Scope",
        "",
        "- Editing the repository before this order is Accepted.",
        "- Findings that belong in another draft order.",
        "- Describing how to attack the code.",
        "",
        "## Leads",
        "",
    ]
    for row in rows:
        label = row["cwe"] or "unspecified class"
        where = f"line {row['line']}" if row.get("line") else "no line"
        lines.append(f"- `{row['file_path']}` — {label} — {where} — {row['verdict']} — {row['reason']}")
    lines.extend(
        [
            "",
            "## Acceptance Criteria",
            "",
            "1. Each lead above is marked confirmed or rejected, with the file and the reason.",
            "2. A confirmed lead has a test that shows the corrected behavior.",
            "3. This order stays Draft until a person accepts it.",
            "",
            "## Protocol",
            "",
            "Observation is done. This document is Draft. Readiness Review is next. "
            "Implementation starts only after Accepted. Push, merge, and deploy still wait for a person.",
            "",
        ]
    )
    return "\n".join(lines)


def _summary(
    repo: str,
    rows: list[dict[str, Any]],
    rejected: list[dict[str, Any]],
    uncertain: list[dict[str, Any]],
    confirmed: list[dict[str, Any]],
    orders: list[dict[str, str]],
    scan: dict[str, Any],
) -> str:
    failed = scan.get("failed_workers")
    tools = scan.get("failed_tool_calls")
    extra = ""
    if isinstance(failed, int) or isinstance(tools, int):
        extra = f" The sweep reported {failed if isinstance(failed, int) else 0} failed class workers and {tools if isinstance(tools, int) else 0} failed tool calls."
    return (
        f"{repo}: {len(rows)} leads, {len(uncertain)} still uncertain, {len(rejected)} rejected, "
        f"{len(confirmed)} confirmed. {len(orders)} draft Work Orders are ready for a Readiness Review. "
        "Product code stays unchanged until a person accepts an order."
        + extra
    )


def _github_name(url: str) -> str:
    match = re.search(
        r"(?:https://github\.com/|git@github\.com:)([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?$",
        (url or "").strip(),
    )
    if match is None:
        return ""
    owner, repo = match.group(1), match.group(2)
    if owner in {".", ".."} or repo in {".", ".."}:
        return ""
    return f"{owner}/{repo}"


def publish_audit(repo: Path, handoff: dict[str, Any], *, today: str) -> dict[str, Any]:
    """Write draft Work Orders and a security-audit index into the product repo."""
    root = Path(repo).resolve()
    run_id = str(handoff.get("run_id") or "")
    if not re.fullmatch(r"[a-f0-9]{8,32}", run_id):
        raise ValueError("run id is not valid")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", today):
        raise ValueError("date is not valid")
    existing = sorted(root.joinpath("docs/security-audits").glob(f"*-{run_id}.md")) if root.joinpath("docs/security-audits").is_dir() else []
    if existing:
        return {
            "already_recorded": True,
            "files": [path.relative_to(root).as_posix() for path in existing],
            "branch": f"security-audit/antares-{run_id}",
        }
    orders = [order for order in (handoff.get("orders") or []) if isinstance(order, dict)]
    start = _next_wo_number(root)
    written: list[str] = []
    numbered: list[tuple[str, str, str]] = []
    for offset, order in enumerate(orders):
        number = start + offset
        slug = re.sub(r"[^a-z0-9-]", "", str(order.get("id") or "lead").split("-")[-1].lower()) or "lead"
        rel = f"docs/work_orders/WO-{number}-security-audit-{slug}.md"
        body = _factory_order(number, order, run_id, today, str(handoff.get("repository") or ""))
        _write_repo_file(root, rel, body)
        written.append(rel)
        numbered.append((f"WO-{number}", str(order.get("priority") or ""), str(order.get("title") or "")))
    index_rel = f"docs/security-audits/{today}-{run_id}.md"
    _write_repo_file(root, index_rel, _audit_index(handoff, today, numbered))
    written.append(index_rel)
    readme_rel = "docs/security-audits/README.md"
    _write_repo_file(root, readme_rel, _audit_readme(root, today, run_id, handoff, numbered))
    written.append(readme_rel)
    _insert_progress(root, numbered, index_rel)
    written.append("docs/project_management/PROGRESS.md")
    return {
        "already_recorded": False,
        "files": written,
        "work_orders": [row[0] for row in numbered],
        "branch": f"security-audit/antares-{run_id}",
    }


def commit_audit(repo: Path, paths: list[str], *, branch: str, message: str, push: bool) -> dict[str, Any]:
    """Commit the audit files on a branch. Push only that branch."""
    import subprocess

    root = Path(repo).resolve()
    if not re.fullmatch(r"security-audit/antares-[a-f0-9]{8,32}", branch):
        raise ValueError("branch is not valid")
    safe_paths = [_audit_rel(path) for path in paths]
    _git(root, ["checkout", "-b", branch]) if _git(root, ["rev-parse", "--verify", branch], check=False).returncode else _git(root, ["checkout", branch])
    _git(root, ["add", "--", *safe_paths])
    committed = _git(root, ["commit", "-m", message], check=False)
    pushed = False
    push_error = ""
    if push and committed.returncode == 0:
        remote = _git(root, ["push", "-u", "origin", branch], check=False)
        pushed = remote.returncode == 0
        if not pushed:
            push_error = (remote.stderr or remote.stdout or "push failed").strip().splitlines()[-1][:300]
    if committed.returncode not in {0, 1}:
        detail = (committed.stderr or committed.stdout or "commit failed").strip().splitlines()
        raise RuntimeError(detail[-1][:300] if detail else "commit failed")
    return {
        "branch": branch,
        "committed": committed.returncode == 0,
        "pushed": pushed,
        "push_error": push_error,
    }


def _next_wo_number(root: Path) -> int:
    highest = 1100
    folder = root / "docs/work_orders"
    if not folder.is_dir():
        return highest + 1
    for path in folder.glob("WO-*.md"):
        match = re.match(r"WO-(\d+)", path.name)
        if match:
            highest = max(highest, int(match.group(1)))
    return highest + 1


def _factory_order(number: int, order: dict[str, Any], run_id: str, today: str, repository: str) -> str:
    title = " ".join(str(order.get("title") or "Security audit").split())[:120]
    priority = str(order.get("priority") or "P1")
    leads = str(order.get("markdown") or "")
    lead_block = ""
    if "## Leads" in leads:
        lead_block = leads.split("## Leads", 1)[1].split("## ", 1)[0].strip()
    return "\n".join(
        [
            f"# WO-{number} — Security audit: {title}",
            "",
            f"**Created:** {today}",
            f"**Priority:** {priority}",
            "**Status:** Draft",
            "**Source:** Security Audit",
            f"**Audit run:** {run_id}",
            f"**Repository:** {repository or 'this repository'}",
            "",
            "## Problem",
            "",
            "This draft came from a Security Audit. Antares named files in a read-only snapshot. "
            "None of these leads is a confirmed defect.",
            "",
            "## What to Build",
            "",
            "A person confirms or rejects each lead. A confirmed lead gets a test for the corrected behavior. "
            "Do not change product code while this order is Draft.",
            "",
            "## Out of scope",
            "",
            "- Implementing a lead before this order is Accepted.",
            "- Leads that belong in another security-audit order.",
            "",
            "## Leads",
            "",
            lead_block or "- No leads recorded.",
            "",
        ]
    )


def _audit_index(handoff: dict[str, Any], today: str, numbered: list[tuple[str, str, str]]) -> str:
    lines = [
        f"# Security Audit {today}",
        "",
        f"**Source:** Security Audit",
        "**Tool:** Antares",
        f"**Run:** {handoff.get('run_id')}",
        f"**Repository:** {handoff.get('repository') or ''}",
        "",
        str(handoff.get("summary") or ""),
        "",
        "## Draft work orders",
        "",
        "| Work order | Priority | Title |",
        "|---|---|---|",
    ]
    for number, priority, title in numbered:
        lines.append(f"| {number} | {priority} | {title} |")
    lines.extend(["", "## Triage", "", "| File | Class | Verdict | Reason |", "|---|---|---|---|"])
    for row in handoff.get("triage") or []:
        if not isinstance(row, dict):
            continue
        lines.append(
            "| {file} | {cwe} | {verdict} | {reason} |".format(
                file=str(row.get("file_path") or "").replace("|", "/"),
                cwe=str(row.get("cwe") or ""),
                verdict=str(row.get("verdict") or ""),
                reason=str(row.get("reason") or "").replace("|", "/"),
            )
        )
    lines.append("")
    return "\n".join(lines)


def _audit_readme(root: Path, today: str, run_id: str, handoff: dict[str, Any], numbered: list[tuple[str, str, str]]) -> str:
    path = root / "docs/security-audits/README.md"
    row = (
        f"| {today} | {run_id} | Antares | {handoff.get('confirmed', 0)} | "
        f"{handoff.get('uncertain', 0)} | {handoff.get('rejected', 0)} | "
        f"{numbered[0][0] if numbered else '—'}–{numbered[-1][0] if numbered else '—'} |"
    )
    if path.is_file() and run_id in path.read_text(encoding="utf-8"):
        return path.read_text(encoding="utf-8")
    header = "\n".join(
        [
            "# Security audits",
            "",
            "Each row is a Security Audit. The linked work orders are drafts until a person accepts them.",
            "",
            "| Date | Run | Tool | Confirmed | Uncertain | Rejected | Drafts |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    if path.is_file():
        current = path.read_text(encoding="utf-8").rstrip()
        return current + "\n" + row + "\n"
    return header + "\n" + row + "\n"


def _insert_progress(root: Path, numbered: list[tuple[str, str, str]], index_rel: str) -> None:
    path = root / "docs/project_management/PROGRESS.md"
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    block_lines = [
        "## Security audits",
        "",
        "Drafts from a Security Audit. They are not started, and product code waits until a person accepts one.",
        "",
        f"Index: `{index_rel}`",
        "",
        "| WO | Title | Priority | Status |",
        "|---|---|---|---|",
    ]
    for number, priority, title in numbered:
        block_lines.append(f"| {number} | Security audit: {title} | {priority} | 🔵 Open |")
    block = "\n".join(block_lines) + "\n\n"
    if "## Security audits" in text:
        return
    marker = "\n## Milestones"
    if marker in text:
        text = text.replace(marker, "\n" + block + "## Milestones", 1)
    else:
        text = text.rstrip() + "\n\n" + block
    path.write_text(text, encoding="utf-8")


def _write_repo_file(root: Path, rel: str, content: str) -> None:
    relative = _audit_rel(rel)
    dest = (root / relative).resolve()
    dest.relative_to(root)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(content, encoding="utf-8")


def _audit_rel(rel: str) -> str:
    path = str(rel or "").strip().replace("\\", "/")
    allowed = path.startswith("docs/work_orders/WO-") or path.startswith("docs/security-audits/") or path == "docs/project_management/PROGRESS.md"
    if not allowed or ".." in path.split("/"):
        raise ValueError("audit path is not allowed")
    return path


def _git(root: Path, args: list[str], *, check: bool = True) -> Any:
    import subprocess

    proc = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    if check and proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "git failed").strip().splitlines()
        raise RuntimeError(detail[-1][:300] if detail else "git failed")
    return proc
