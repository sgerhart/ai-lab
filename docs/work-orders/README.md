# Work orders

This directory holds **historical implementation-phase records** (`WO-000`–`WO-007`) from the initial repository build. They describe Git deliverables and (where noted) host deploy state.

They are **not**:

- Live PostgreSQL runtime work orders on `mac-mini` (those are UUIDs via `POST /v1/work-orders`)
- Future capability specs (see [`../features/`](../features/README.md), `FEAT-001`…)

Do not silently rename these files into `FEAT-*` IDs. New engineering tasks that implement a feature should be proposed as implementation work orders under that feature (for example `IWO-…`) or as GitHub issues linked from the feature index.

| ID | Title | Code in Git | Host deployed | Live verified |
|----|-------|-------------|---------------|---------------|
| [WO-000](WO-000-phase-0-repository-foundation.md) | Foundation | Yes | n/a | n/a |
| [WO-001](WO-001-phase-1-host-bootstrap.md) | Host bootstrap + network | Yes | **Partial** — M1 `--apply` + Air/mini on tailnet; Studio **not** | Mini SSH/Tailscale verified from Air |
| [WO-002](WO-002-phase-2-control-plane.md) | Control-plane compose | Yes | **Yes** — Colima compose on `mac-mini` | Healthchecks + first iCloud dump; **live restore untested** |
| [WO-003](WO-003-phase-3-compute.md) | Studio compute tooling | Yes | **No** | No |
| [WO-004](WO-004-phase-4-harness.md) | Agent harness | Yes (unit + ephemeral Postgres) | **Partial** — API on `mac-mini:8088` | `/health`, status board, submit from Air; Studio path not live |
| [WO-005](WO-005-phase-5-agents.md) | Three agents | Yes (deterministic plans) | **No** Studio worker | Plans tested in CI/laptop; not LLM |
| [WO-006](WO-006-phase-6-model-lab.md) | Training/eval | Catalog + refuse-pull | **No** | No weights / no pulls |
| [WO-007](WO-007-phase-7-hardening.md) | Hardening / recovery | CI + throwaway restore | Backup dest iCloud | First `--execute` dump written; restore drill **not** done |

Forward-looking capabilities: [`../features/index.md`](../features/index.md).
