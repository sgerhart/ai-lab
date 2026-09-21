# Repository complete vs deploy blocked

**Updated:** 2026-09-21

Git work for phases 0–7 is **done**. No host has been authorized. Building files is not permission to deploy.

## Done in Git

| Area | Evidence |
|------|----------|
| Foundation, ADRs 0001–0027 | `docs/decisions/` |
| Host Brewfiles + dry-run setup | `hosts/*` |
| Compose Postgres/Redis/Qdrant | `infrastructure/compose.yaml` |
| LangGraph slice + FastAPI + Postgres store | `platform/`, `tests/test_langgraph_slice.py` |
| Three agent plans | `agent_plans.py`, Studio worker |
| Model catalog (empty of pulls) | `models/catalog.json` |
| Eval/train refuse-pull | `scripts/eval-dry-run.sh`, `scripts/train.sh` |
| Throwaway dump→restore | `scripts/test-backup-restore.sh` |
| MCP | deny-unlisted, **zero** servers |
| Ollama client | loopback only, `pull` refused |
| Git identity | local `sgerhart@gmail.com` (ADR 0022) |

## Blocked on a human decision (not inventable)

| ID | Need |
|----|------|
| [D-001](../open-decisions.md) | Public vs private GitHub |
| [D-009](../open-decisions.md) | Bind Air Ollama off `*:11434` (live hygiene) |
| [D-011](../open-decisions.md) | Backup destination **not** the M1 disk |
| [D-015](../open-decisions.md) | Attest M3 Air unified memory |
| [D-016](../open-decisions.md) | Real Tailscale names / tailnet / ACLs |
| [D-018](../open-decisions.md) | Whether Studio Thunderbolt NVMe exists |

## Blocked on host authorization

[WO-001](../work-orders/WO-001-phase-1-host-bootstrap.md) `--apply` on the M1, then compose `up`, then Studio, then an explicit model pull.

Do not start control-plane compose on the Air (ADR 0025).
