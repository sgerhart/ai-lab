# Mac Studio — compute plane runbook

**Inventory name:** `studio`  
**Role:** Inference, MLX, isolated workers.  
**Does not:** own PostgreSQL data or the work-order queue.

A new engineer clones `ai-lab` and follows this file only.

## Status of this runbook

**SSH:** use `stevengerhart@mac-studio` (not `sgerhart`). Air and mini publickey OK (F-015 closed). Ollama/Jupyter also on Tailscale.

## Status of this runbook

| Step | Status |
|------|--------|
| Preflight / Brewfile | **Implemented.** **Not applied** on a Studio. M5 Max compatibility **unverified** (this workspace is M3). |
| Ollama install | In Brewfile. **No model pulls** in setup. |
| Studio worker API | **Implemented** (`scripts/studio-worker.sh`). Executes catalog agent plans (not an LLM). Unit-tested. **Not running on a Studio.** |
| Ollama bind | **Live.** `OLLAMA_HOST=0.0.0.0:11434` (ADR 0041). LAN and Tailscale. |
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

`com.ai-lab.ollama` sets `OLLAMA_HOST=0.0.0.0:11434` (ADR 0041). Ollama takes
one address, so all interfaces is how loopback, the Studio LAN, and Tailscale
share the process. Do not pin it back to the Tailscale address only.

The same agent should set `OLLAMA_MAX_LOADED_MODELS=1`. Chat, agents, and a
notebook that calls Ollama then share one resident tag. A second tag waits
until the idle model unloads (default keep-alive is about five minutes).
This variable is not on the live agent yet. Adding it means editing the
LaunchAgent and restarting Ollama, which unloads the current model. An MLX
model inside a Jupyter kernel is outside this cap.

```bash
curl -sS http://127.0.0.1:11434/api/tags          # on the Studio
curl -sS http://mac-studio:11434/api/tags         # from the tailnet
# From a machine on the same LAN as the Studio, use that host's local address.
```

A client on a different subnet cannot open the LAN address. The Air and the
Studio were on different `192.168` networks when this bind was set. Tailnet
access is unchanged: the mini still uses `STUDIO_OLLAMA_URL=http://mac-studio:11434`.

```bash
export PATH="/opt/homebrew/bin:$PATH"
ollama list
# Seen 2026-09-24: llama3.2:3b, qwen3.8:27b, qwen3-coder:30b.
# ollama pull <name>   # only after owner authorizes the pull
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

curl -sS http://127.0.0.1:11434/api/tags
curl -sS http://mac-studio:11434/api/tags
```

From the M1 (when Tailscale and binds are set): POST `/v1/work-orders` on the control plane should reach this worker. If this host is down, the control plane **re-queues** the work order with `studio_unavailable` — it must not disappear. If the plan itself fails, the work order is persisted as `failed` with `plan_failed`.

## 7. Backup / recovery

Weights are rebuildable via catalog + `ollama pull` unless you choose a backup target. Checkpoints and queues live on the **M1**, not here. Studio disk wipe: reinstall via this runbook, then re-pull catalogued models.

## 8. Troubleshooting

| Symptom | Check |
|---------|--------|
| Chip is not M5 | You are not on the Studio |
| LAN client cannot reach `:11434` | Same subnet as the Studio, then its local address. `0.0.0.0` does not join two networks |
| Worker connection refused from M1 | Tailscale, bind address, ACL tags |
| Work order `failed` + `plan_failed` | Worker ran; the deterministic plan errored. Inspect `final_result`. |
| Unified memory pressure | One Ollama tag at a time (`OLLAMA_MAX_LOADED_MODELS=1`, not yet on the live agent). An MLX notebook is a second allocator (ADR 0010) |

## 9. Rollback

Stop the worker (Ctrl-C / launchd). Leave Ollama installed. Do not delete `~/.ollama` unless you intend to drop weights.

## Antares (FEAT-015)

Weights under `~/.ai-lab/antares/antares-1b/` (not in Git). Operator helpers:

- Completions: `127.0.0.1:8001` (`scripts/antares-completions-server.py`)
- Jobs: Tailscale `:8002` (`scripts/antares-job-server.py`) for mini `/antares`
- Sandbox profile: `hosts/studio/antares-sandbox.sb`

See [../../docs/runbooks/antares-vuln-localize.md](../../docs/runbooks/antares-vuln-localize.md).

