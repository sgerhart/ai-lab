# Repository complete vs deploy blocked

**Updated:** 2026-09-21

Git work for phases 0–7 is **done**. M1 `--apply` was authorized 2026-09-21 and **not executed** (agent is on the Air; SSH to `mac-mini` denied). Building files is not permission to deploy.

## Done in Git

| Area | Evidence |
|------|----------|
| Foundation, ADRs 0001–0033 | `docs/decisions/` |
| Host Brewfiles + dry-run setup | `hosts/*` |
| Public-safe inventory names | `hosts/*/inventory.yaml` (`mac-mini` / `mac-studio` / `mac-air`) |
| Compose Postgres/Redis/Qdrant | `infrastructure/compose.yaml` |
| LangGraph slice + FastAPI + Postgres store | `platform/`, `tests/test_langgraph_slice.py` |
| Three agent plans | `agent_plans.py`, Studio worker |
| Model catalog (empty of pulls) | `models/catalog.json` |
| Eval/train refuse-pull | `scripts/eval-dry-run.sh`, `scripts/train.sh` |
| Throwaway dump→restore | `scripts/test-backup-restore.sh` |
| iCloud backup default | `scripts/backup.sh` (ADR 0030); `--execute` not authorized |
| MCP | deny-unlisted, **zero** servers |
| Ollama client | loopback only, `pull` refused |
| Git identity | local `sgerhart@gmail.com` (ADR 0022) |

## Remaining human facts (not inventable)

| Need | Status |
|------|--------|
| GitHub public vs private | **Resolved** — stays public (ADR 0028) |
| Air Ollama `*:11434` | **Resolved** — accepted on Air (ADR 0029) |
| Backup destination | **Resolved** — iCloud Drive (ADR 0030). Live restore still untested |
| M3 Air RAM | **Resolved** — 16 GB (ADR 0031) |
| Tailscale machine names | **Resolved** — `mac-mini` / `mac-studio` / `mac-air` (ADR 0032) |
| Tailnet DNS suffix / IPv4 / ACL file | Suffix/IPv4 observed 2026-09-21, **overlay only** (not `dentroio`). Studio not on tailnet. ACL still open |
| Studio Thunderbolt NVMe | **Deferred** — not initial setup (ADR 0033) |

## Blocked on host authorization

[WO-001](../work-orders/WO-001-phase-1-host-bootstrap.md) `--apply` on the M1 requires a session **on the mini** (or working SSH). Do not `--force` the M1 Brewfile on the Air.

Do not start control-plane compose on the Air (ADR 0025).
