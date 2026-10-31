# System Architecture: Execution-Verified Coding Model Training Platform

**Version:** 1.0  
**Date:** 2026-10-30  
**Parent Platform:** AI Lab (`ai-lab`)  
**Status:** Approved for WO-00 (Architecture Baseline)

---

## 1. Physical & Logical Topology

The platform spans three physical AI Lab tiers plus an isolated hypervisor security plane:

```text
+-------------------------------------------------------------------------+
| MacBook Air M3 (16 GB)                                                  |
| - Development client (Cursor / Antigravity IDE)                         |
| - Operator review, approvals, and report visualization                  |
+------------------------------------+------------------------------------+
                                     | Authenticated Tailnet / HTTPS
                                     v
+-------------------------------------------------------------------------+
| Mac Mini M1 (16 GB) — Control Plane (:8088 / :8092)                     |
| - Controller API (FastAPI, job orchestration, audit logging)            |
| - PostgreSQL (durable runs, tasks, lease management, immutable records) |
| - Redis (ephemeral cache / lease locks)                                 |
| - Reward Scorer & Evaluation Engine                                     |
| - Content-Addressed Artifact Store (/var/ai-lab/artifacts or local)    |
+-------------------+---------------------------------+-------------------+
                    |                                 |
  Model RPC         |                                 | Worker RPC
  (Tailnet/HTTPS)   |                                 | (Dedicated Segment)
                    v                                 v
+------------------------------------+  +---------------------------------+
| Mac Studio M5 Max (64 GB)          |  | Proxmox Security Compute        |
| - Model Worker Service             |  | - Dedicated Non-prod Linux VM   |
| - Inference (MLX / Ollama fallback)|  | - Worker Daemon (:8095)         |
| - SFT Trainer (MLX-LM LoRA/QLoRA)  |  | - Disposable execution jail:    |
| - RL Trainer (mlxrl spike candidate|  |   * cgroups v2 resource limits  |
| - Adapter checkpoints              |  |   * seccomp strict filter       |
+------------------------------------+  |   * no-network namespace        |
                                        |   * read-only root + tmpfs      |
                                        +---------------------------------+
```

### Verified Host Inventory & Roles

| Host | Architecture | Primary Role | Connectivity | Security Constraints |
|------|--------------|--------------|--------------|----------------------|
| **`mac-mini`** | M1 16 GB | Control Plane, DB, Queue, Scoring | Tailscale (`100.80.117.123`) | No candidate execution. Bind to loopback/Tailscale IP |
| **`mac-studio`**| M5 Max 64 GB | Model Inference & MLX Training | Tailscale (`100.64.198.100`) | No candidate execution. Adapter weights only |
| **`mac-air`** | M3 16 GB | Operator / Cursor Client | Tailscale | Client-only; no daemon execution |
| **`proxmox-vm`**| Linux (x86_64, 4 vCPU, 8 GB) | Sandbox Execution Worker | Isolated VLAN / Host-only bridge | Zero egress to Internet/LAN; disposable jails |

---

## 2. Trust Boundaries

```text
[Operator / Cursor] 
         │ (Boundary A)
         ▼
┌──────────────────┐       (Boundary B)        ┌─────────────────┐
│ Control Plane    │ ────────────────────────> │ Model Worker    │
│ (Mini)           │                           │ (Studio)        │
└────────┬─────────┘                           └─────────────────┘
         │
         │ (Boundary C: RPC to worker; candidate code is UNTRUSTED)
         ▼
┌────────────────────────────────────────────────────────────────┐
│ Linux Sandbox Worker VM                                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Disposable Container / Jail (Boundary D: Out-of-band)    │  │
│  │ [Candidate Code] <─── isolated execution ───> [Tests]    │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
         │
         │ (Boundary E: Content-addressed manifests & hashes)
         ▼
┌──────────────────┐
│ Checkpoints &    │
│ Verified SFT/RL  │
└──────────────────┘
```

- **Boundary A (Operator to Controller):** Authenticated via operator session token / Tailscale identity. Mutating operations and approvals require audit records.
- **Boundary B (Controller to Model Worker):** Authenticated internal RPC. Prompt inputs are structured; generated outputs are untrusted raw strings subject to strict schema parsing.
- **Boundary C (Worker to Untrusted Execution):** Network isolation plus disposable container jail. Untrusted code cannot access worker credentials, parent filesystem, or network sockets.
- **Boundary D (Grading Inputs & Out-of-Band Capture):** Test bundles are verified by SHA-256 before staging. Hidden tests are mounted read-only for the runner but never disclosed to model output or API logs. Result captures exit code, execution time, and stdout/stderr limits out-of-band.
- **Boundary E (Training Data & Checkpoints):** Checkpoints and SFT training pairs require immutable cryptographic provenance (dataset hash, candidate hash, test-bundle hash, seed, optimizer parameters).

---

## 3. Component Lifecycle & State Machines

### 3.1 Candidate Execution Lifecycle

```text
[CREATED] ──> [GENERATING] ──> [READY_TO_TEST] ──> [TESTING] ──> [SCORED] ──> [RECORDED]
     │              │                  │               │
     v              v                  v               v
  [FAILED]     [TIMED_OUT]        [CANCELLED]    [INFRA_ERROR]
```

- **Candidate Failure vs. Infrastructure Failure:**
  - A candidate syntax error, test assertion error, or infinite loop produces status `SCORED` with `reward = 0.0` (or partial pass fraction).
  - An infrastructure failure (worker heartbeat timeout, corrupted test bundle hash, container crash, OS memory killer) produces status `INFRA_ERROR` with `reward = null` (`unscorable`).
  - **Invariance Rule:** `INFRA_ERROR` is NEVER assigned a numerical reward of `0.0`. It is rescheduled or quarantined.

### 3.2 Training Job Lifecycle

```text
[DRAFT] ──> [PREFLIGHT] ──> [AWAITING_APPROVAL] ──> [RUNNING] ──> [CHECKPOINTING] ──> [EVALUATING] ──> [COMPLETE]
                                     │                     │
                                     v                     v
                                 [DENIED]               [FAILED]
```

- **Approval Gate:** Moving from `PREFLIGHT` to `RUNNING` requires an explicit signed human approval record in the database.
- **Weight Verification:** Checkpoints record adapter parameter checksums before and after training steps. A run with 0 optimizer steps or identical weights is flagged as invalid.

---

## 4. Key Typed Interfaces

### 4.1 ModelBackend (`packages/contracts/model.py`)

```python
class ModelBackend(Protocol):
    def load(self, model_ref: str, tokenizer_ref: str, quantization: str | None = None) -> None: ...
    def generate(self, prompt: str, seed: int, config: GenerationConfig) -> GenerationResult: ...
    def train_sft(self, manifest: SFTManifest, config: SFTConfig) -> CheckpointResult: ...
    def train_rl(self, rollout: RolloutManifest, config: RLConfig) -> CheckpointResult: ...
    def capabilities(self) -> ModelCapabilities: ...
    def health(self) -> HealthStatus: ...
```

### 4.2 SandboxBackend (`packages/contracts/sandbox.py`)

```python
class SandboxBackend(Protocol):
    def execute(
        self,
        candidate_code: str,
        test_bundle: TestBundleRef,
        policy: SandboxPolicy,
    ) -> ExecutionResult: ...
    def attest(self) -> WorkerAttestation: ...
    def health(self) -> HealthStatus: ...
```

### 4.3 RewardScorer (`services/rewards/scorer.py`)

```python
class RewardScorer:
    def score(self, execution: ExecutionResult, test_bundle: TestBundle) -> RewardResult:
        if execution.is_infra_error:
            return RewardResult(reward=None, status="unscorable", reason=execution.error_class)
        if execution.total_tests == 0:
            return RewardResult(reward=None, status="unscorable", reason="empty_test_bundle")
        
        passed_fraction = max(0.0, min(1.0, execution.passed_tests / execution.total_tests))
        return RewardResult(reward=passed_fraction, status="scored", scoring_version="reward-v1")
```

---

## 5. Storage & Artifact Hierarchy

```text
runs/{run_id}/
  manifest.json          # Experiment config, model revision, dataset hash, git SHA
  generations.jsonl      # Raw candidates, token counts, extraction status
  executions.jsonl       # Worker run results, timing, memory peak, exit codes
  rewards.jsonl          # Scored rewards, test counts, score version
  evaluations.json       # Holdout evaluation metrics (pass@1, pass@k)
  checkpoints/
    adapter_config.json
    adapters.safetensors
    checksum.sha256
```
