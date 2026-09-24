# Mac Studio — compute plane runbook

**Inventory name:** `studio`  
**Role:** Inference, MLX, isolated workers.  
**Does not:** own PostgreSQL data or the work-order queue.

A new engineer clones `ai-lab` and follows this file only.

## Status of this runbook

**SSH from Air/mini currently fails (F-015).** Ollama and Jupyter remain reachable on Tailscale. Prefer fixing `authorized_keys` on console; Antares work uses Jupyter exec until then.

## Status of this runbook

| Step | Status |
|------|--------|
| Preflight / Brewfile | **Implemented.** **Not applied** on a Studio. M5 Max compatibility **unverified** (this workspace is M3). |
| Ollama install | In Brewfile. **No model pulls** in setup. |
| Studio worker API | **Implemented** (`scripts/studio-worker.sh`). Executes catalog agent plans (not an LLM). Unit-tested. **Not running on a Studio.** |
| Ollama bind | **Documented.** Must not be `*:11434`. |
| Tailscale | **Documented.** Machine name `mac-studio` (ADR 0032). |
| Thunderbolt NVMe | **Deferred** (ADR 0033). Initial setup uses internal 1 TB SSD. |

## 1. Prerequisites

- Mac Studio, Apple M5 Max, 18 CPU / 40 GPU, 64 GB, 1 TB (confirmed).
- Admin user, cloned `ai-lab`.
- Homebrew installed by you, or already present.
- Tailscale account.
- Control plane on the mini already defined (worker is useless without it, but can be started locally for tests).

## 2. Preflight (safe)

```bash
cd ~/workspace/github/sgerhart/ai-lab
./hosts/studio/setup.sh --preflight
```

Expected chip contains `M5`. On any other Mac: warning only unless `--apply`.

## 3. Installation (authorize `--apply`)

```bash
./hosts/studio/setup.sh --dry-run
./hosts/studio/setup.sh --apply
```

Installs: git, jq, uv, tailscale, ollama, cmake. **Does not `ollama pull`.**

```bash
cd platform
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## 4. Configuration

Ollama must listen on loopback (or later the Tailscale IPv4), never all interfaces:

```bash
# Example — exact launchctl/plist path is host-specific; record it in local.inventory.yaml
export OLLAMA_HOST=127.0.0.1:11434
```

Worker URL that the **M1** will call after Tailscale join:

```text
STUDIO_WORKER_URL=http://mac-studio:8090
```

Local tests still use `http://127.0.0.1:8090`. Tailnet suffix is not in Git.

Join Tailscale: [../../docs/runbooks/join-tailnet.md](../../docs/runbooks/join-tailnet.md).

## 5. Service startup (authorize)

```bash
# Worker (loopback)
./scripts/studio-worker.sh

# Ollama is a brew service / app; start it per `ollama --help` on that host.
# Do not pull models until [../../docs/runbooks/adding-a-model.md](../../docs/runbooks/adding-a-model.md).
```

`studio-worker.sh` refuses non-loopback binds.

## 6. Verification

```bash
curl -sS http://127.0.0.1:8090/health
# {"ok": true, "role": "studio-worker", "plans": "deterministic-local", "llm": false, "deployed": false}

curl -sS -X POST http://127.0.0.1:8090/v1/tasks \
  -H 'Content-Type: application/json' \
  -d '{"work_order_id":"demo","agent":"lab-operations","objective":"health"}'

curl -sS http://127.0.0.1:11434/api/tags   # after Ollama is running; empty list is OK
```

From the M1 (when Tailscale and binds are set): POST `/v1/work-orders` on the control plane should reach this worker. If this host is down, the control plane **re-queues** the work order with `studio_unavailable` — it must not disappear. If the plan itself fails, the work order is persisted as `failed` with `plan_failed`.

## 7. Backup / recovery

Weights are rebuildable via catalog + `ollama pull` unless you choose a backup target. Checkpoints and queues live on the **M1**, not here. Studio disk wipe: reinstall via this runbook, then re-pull catalogued models.

## 8. Troubleshooting

| Symptom | Check |
|---------|--------|
| Chip is not M5 | You are not on the Studio |
| Ollama on `*:11434` | Finding F-003 class issue; bind loopback |
| Worker connection refused from M1 | Tailscale, bind address, ACL tags |
| Work order `failed` + `plan_failed` | Worker ran; the deterministic plan errored. Inspect `final_result`. |
| Unified memory pressure | Do not autoload multiple large models (ADR 0010) |

## 9. Rollback

Stop the worker (Ctrl-C / launchd). Leave Ollama installed. Do not delete `~/.ollama` unless you intend to drop weights.
