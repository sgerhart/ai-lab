# Operator Runbook — Coding Model Training Platform

**Sub-Platform:** `coding-training/`  
**Feature:** FEAT-024 (Execution-Verified Coding Model Training)  
**Target Hosts:** `mac-mini` (Controller), `mac-studio` (Model Worker), `proxmox-vm` (Sandbox Worker)  
**Author:** Steven Gerhart <sgerhart@gmail.com>  
**Last Updated:** 2026-11-01  

---

## 1. System Topology & Default Bindings

In compliance with `AGENTS.md` and ADR 0010, all listeners bind to loopback (`127.0.0.1`) by default during local development and preflight. Deployments to physical lab hosts require explicit operator approval.

```
+-------------------------------------------------------------------------------+
|                                  AI LAB TOPOLOGY                              |
|                                                                               |
|  +--------------------+      +--------------------+      +-----------------+  |
|  |     mac-mini       |      |     mac-studio     |      |   proxmox-vm    |  |
|  |  (Control Plane)   | ---> |   (Model Compute)  |      | (Sandbox Jails) |  |
|  |  Port: 8000        |      |   Port: 8001       |      | Port: 8002      |  |
|  +--------------------+      +--------------------+      +-----------------+  |
|            |                                                      ^           |
|            +------------------------------------------------------+           |
|                       Dispatches Test Executions                              |
+-------------------------------------------------------------------------------+
```

| Service | Host | Port | Binary / Module | Default Bind |
| :--- | :--- | :--- | :--- | :--- |
| **Controller** | `mac-mini` | `8000` | `uvicorn services.controller.app:app` | `127.0.0.1` |
| **Model Worker** | `mac-studio` | `8001` | `uvicorn services.model.app:app` | `127.0.0.1` |
| **Sandbox Worker** | `proxmox-vm` | `8002` | `uvicorn services.sandbox_worker.app:app` | `127.0.0.1` |

---

## 2. Safety Switches & Invariant Enforcements

The platform enforces fail-closed defaults across all services:

1. **`EXECUTION_ENABLED=false` (Default):** Untrusted code execution is blocked unless explicitly enabled via environment variable `EXECUTION_ENABLED=true` or `--enforce-execution-flag=false` in sandboxed integration tests.
2. **`TRAINING_ENABLED=false` (Default):** Optimizer updates and checkpoint writes are gated by human approval.
3. **Weight Divergence Enforcement:** SFT and GRPO training runs must demonstrably modify adapter weights (`initial_adapter_hash != final_adapter_hash`). Runs producing identical weights fail closed immediately.
4. **Zero Holdout Contamination:** Training sets are mined exclusively from `Split.TRAIN`. Any task belonging to `Split.VAL` or `Split.TEST` is strictly quarantined.
5. **Infrastructure Failure Isolation:** Infrastructure errors (`INFRA_ERROR`) are unscorable and must never be assigned `0.0` reward, preventing policy gradient contamination.

---

## 3. Clean-Start Operator Walkthrough

Follow these steps sequentially to initialize and operate the platform from a clean git checkout.

### Step 1: Preflight & Test Verification
```bash
# From workspace root:
./scripts/preflight.sh
./scripts/validate-repo.sh

# Run comprehensive coding-training test suite (71 unit tests):
cd coding-training
make check
```

### Step 2: Compile Datasets & Verify Cryptographic Hashes
```bash
python3 scripts/compile_datasets.py
```
*Expected Output:*
- 105 curated Python tasks loaded.
- 0 family ID overlap across `train`, `validation`, and `test` splits.
- 100% reference solutions pass against immutable test bundles.
- Manifest written to `datasets/manifests/dataset_v1.json`.

### Step 3: Run Reproducible Holdout Baseline Evaluation
```bash
# Run reference ceiling evaluation (100% pass@1 expected):
python3 scripts/evaluate_baseline.py --use-reference --splits validation test

# Run untrained base model mock (0% pass@1 expected):
python3 scripts/evaluate_baseline.py --splits validation test --output reports/baseline_holdout_untrained.json
```

### Step 4: Mine SFT Datasets & Execute Verified LoRA Training
```bash
# Mine instruction-completion pairs strictly from Split.TRAIN and fine-tune adapter:
python3 scripts/train_sft.py --mine --model-id Qwen/Qwen3-0.6B --lora-rank 8 --evaluate-holdout
```
*Verification Check:*
- Ensure `weights_diverged: True` is displayed.
- Checkpoint is saved under `~/.ai-lab/models/adapters/ckpt-run-sft-<timestamp>-step50/`.
- Summary comparison report written to `reports/sft_holdout_comparison.json`.

### Step 5: Execute RL Compatibility Spike
```bash
python3 scripts/run_rl_spike.py --group-size 4 --beta 0.04
```
*Verification Check:*
- Confirms non-zero gradient norm $\|\nabla_\theta \mathcal{L}\|_2 > 0$ and parameter divergence.
- Report generated at `reports/rl_spike_report.json`.

### Step 6: Execute Execution-Reward GRPO Training
```bash
python3 scripts/train_rl.py --base-model Qwen/Qwen3-0.6B --group-size 4 --max-steps 25 --eval-holdout
```
*Verification Check:*
- Groups processed: 25.
- Checkpoint verified on disk under `~/.ai-lab/models/adapters/ckpt-run-rl-<timestamp>-step25/`.
- Validation report saved to `reports/rl_holdout_comparison.json`.

---

## 4. Starting Service Daemons & Coding Training Console

### Coding Training Console (Web UI)
The web console is built with React 18, Vite, and TypeScript. Once built, it is statically served directly by the Controller at `/console/`.

```bash
# Build the console frontend:
cd coding-training/console
npm run build

# Or using the Makefile target:
cd coding-training
make console-build
```

### Controller Plane Daemon (Mac Mini)
```bash
uvicorn services.controller.app:app --host 127.0.0.1 --port 8000 --workers 1
```
Endpoints:
- `GET /` -> Redirects to `/console/`
- `GET /console/` -> Coding Training Console web interface
- `GET /v1/health` -> Health status of controller, model worker, and sandbox worker
- `GET /v1/metrics` -> Platform-wide execution and reward summary
- `GET /v1/tasks` -> Curated task catalog with split and difficulty filters
- `GET /v1/models` -> Base models and verified adapter checkpoints
- `GET /v1/events/stream` -> Real-time SSE telemetry stream
- `POST /v1/jobs/submit` -> Pipeline submission (prompt -> sandbox -> reward)
- `GET /v1/jobs/{job_id}` -> Comprehensive job record
- `GET /v1/audit/events` -> Immutable security audit log

### Model Worker Daemon (Mac Studio)
```bash
uvicorn services.model.app:app --host 127.0.0.1 --port 8001 --workers 1
```
Endpoints:
- `GET /v1/health`
- `GET /v1/capabilities`
- `POST /v1/models/load`
- `POST /v1/generate`
- `POST /v1/train/sft`
- `POST /v1/train/rl`
- `GET /v1/checkpoints`
- `GET /v1/checkpoints/{id}`

### Sandbox Worker Daemon (Linux VM)
```bash
EXECUTION_ENABLED=true uvicorn services.sandbox_worker.app:app --host 127.0.0.1 --port 8002 --workers 2
```
Endpoints:
- `GET /v1/health`
- `GET /v1/attestation`
- `POST /v1/execute`


---

## 5. Troubleshooting & Diagnostics

### Issue: `validate-repo.sh` fails with `forbidden artifact present`
- **Cause:** Binary weights (`*.safetensors`, `*.gguf`, `*.ckpt`) were saved inside the repository tree.
- **Remedy:** Ensure `AI_LAB_CHECKPOINTS_DIR` points to `~/.ai-lab/models/adapters/` (outside the git tree). Run `rm -rf coding-training/checkpoints/` if present.

### Issue: `ValueError: Weight divergence check FAILED`
- **Cause:** An optimizer run produced zero weight changes or failed to complete gradient steps.
- **Remedy:** Inspect learning rate, optimizer hyperparameters, or dataset size. Training fails closed rather than producing a fraudulent checkpoint.

### Issue: Sandbox returns `status: "infra_error"`
- **Cause:** Missing test bundle or tampered bundle SHA-256 digest.
- **Remedy:** Run `python3 scripts/compile_datasets.py` to regenerate immutable test bundles and update dataset manifests.
