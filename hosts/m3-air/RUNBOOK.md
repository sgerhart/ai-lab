# M3 MacBook Air — human / development runbook

**Inventory name:** `m3-air`  
**Role:** IDE, Git, SSH, dashboards, human approvals.  
**Does not:** run always-on control-plane compose or lab inference.

A new engineer clones `ai-lab` and follows this file only.

## Status of this runbook

| Step | Status |
|------|--------|
| Preflight | **Implemented and tested** on this workspace host (Apple M3). |
| Brewfile apply | **Implemented**, **not applied** by the repo build. |
| Local harness CLI | **Implemented and tested** (`scripts/platform.sh`). |
| Control-plane TestClient slice | **Implemented and tested** on this Air (not a substitute for M1 deploy). |
| Unified memory | **16 GB** attested (ADR 0031). |
| Ollama on this laptop | Present; listens `*:11434` (F-003, **accepted** ADR 0029). **Not** lab serving. |
| Tailscale name | `mac-air` (ADR 0032) |

Do **not** `docker compose up` `infrastructure/compose.yaml` on this laptop (port collisions with Clarion).

## 1. Prerequisites

- MacBook Air, Apple M3, 16 GB, 512 GB (confirmed, ADR 0031).
- Cloned `ai-lab`.
- GitHub access for `sgerhart/ai-lab` (prefer `sgerhart` identity, ADR 0022).

## 2. Preflight (safe)

```bash
cd /path/to/ai-lab
./hosts/m3-air/setup.sh --preflight
./scripts/validate-repo.sh
python3 -m unittest discover -s tests -v
```

If LangGraph tests skip, install platform extras (laptop-only, does not deploy):

```bash
cd platform
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cd ..
PYTHONPATH=platform/src platform/.venv/bin/python -m unittest discover -s tests -v
```

## 3. Installation (authorize `--apply`)

```bash
./hosts/m3-air/setup.sh --dry-run
./hosts/m3-air/setup.sh --apply
```

Installs: git, gh, jq, uv, tailscale.

## 4. Configuration

```bash
gh auth status   # prefer the sgerhart identity for this repo (ADR 0022)
```

Join Tailscale: [../../docs/runbooks/join-tailnet.md](../../docs/runbooks/join-tailnet.md).  
Record names in `hosts/m3-air/local.inventory.yaml` (gitignored).

Optional local SQLite harness (not the M1 control plane):

```bash
./scripts/platform.sh --db /tmp/ai-lab-harness.sqlite submit --agent lab-operations --objective "health snapshot"
./scripts/platform.sh --db /tmp/ai-lab-harness.sqlite tick
```

## 5. Service startup

**None required.** This host must sleep without taking the lab down.

Optional: browse `http://mac-mini:8088/health` when the mini is up (MagicDNS; tailnet suffix still not in Git).

Human approval:

```bash
curl -sS -X POST http://mac-mini:8088/v1/work-orders/{id}/approve \
  -H 'Content-Type: application/json' \
  -d '{"decision":"approved"}'
```

## 6. Verification

```bash
git -C /path/to/ai-lab rev-parse --show-toplevel   # must end in ai-lab
./scripts/validate-repo.sh
```

## 7. Backup / recovery

This host is not the backup source for Postgres. Keep the git working tree; do not commit `.env` or overlays.

## 8. Troubleshooting

| Symptom | Check |
|---------|--------|
| `gh` posts as dentroio | Use `github-sgerhart` / sgerhart identity (ADR 0022) |
| Compose ports busy | You started control-plane compose on the Air — stop it |
| Ollama wildcard listen | F-003; optional local bind to 127.0.0.1; not Studio |

## 9. Rollback

Leave developer tools installed. `tailscale logout` if this machine should leave the tailnet.
