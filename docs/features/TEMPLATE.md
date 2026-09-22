# Feature specification template

Copy to `FEAT-NNN-short-kebab-name.md`. Do not invent hostnames, IPs, or credentials.

```markdown
# FEAT-NNN — Title

- **Status:** Idea | Specified | Approved for implementation | In progress | Implemented in Git | Deploy authorized | Live verified | Deferred | Rejected
- **Created:** YYYY-MM-DD
- **Owner:** (human)
- **GitHub issue:** (link or "draft only")

## Purpose

One paragraph: desired capability / user outcome.

## User workflow

Step-by-step what a human or agent does once this exists.

## Target host(s)

| Role | Host alias | Why |
|------|------------|-----|
| … | `mac-mini` / `mac-studio` / `mac-air` | … |

## Dependencies

- Features: `FEAT-…`
- ADRs / policies:
- Hosts / services that must already be live:

## Proposed deliverables

- Docs / ADRs
- Code modules
- Tests
- Runbooks

## Proposed implementation work orders

| ID (proposed) | Title | Depends on | Acceptance (sketch) |
|---------------|-------|------------|---------------------|
| IWO-… | … | … | … |

## Acceptance criteria

- [ ] …
- [ ] Human approval gates listed (no self-approval)

## Out of scope

Explicit non-goals for this feature.

## Implementation status (honest)

| Layer | Status | Evidence |
|-------|--------|----------|
| Spec in Git | … | this file |
| Code | not started / partial / done | paths or "n/a" |
| Host deploy | not authorized / partial / done | host + date or "n/a" |
| Live verified | no / yes | command + date or "n/a" |

## Notes

Placeholder facts, open decisions, links to adjacent systems.
```
