# WO-10 — AI Lab Coding Training Console

**Work Order:** WO-10  
**Parent Feature:** FEAT-024 (Execution-Verified Coding Model Training Platform)  
**Parent Sub-Platform:** `coding-training/`  
**Status:** Specified & Planned (Ready for phased frontend implementation alongside WO-04)  
**Effort:** L  
**Priority:** P2  

---

## 1. Objective

Provide a complete, production-grade graphical user interface for operating and observing the Coding Model Training Platform without requiring direct interaction with internal command-line scripts, database tables, or raw message queues.

The console enables the operator to:
1. Observe the real-time health and reachability of all three tiers (Mac Mini controller, Mac Studio model compute, and Proxmox Linux sandbox worker).
2. Interactively test models and inspect sandbox execution traces in a live Playground.
3. Configure, start, monitor, and cancel SFT LoRA and RL training jobs with explicit confirmation gates.
4. Monitor live generation throughput, reward distributions, and training loss curves over SSE/WebSocket.
5. Manage and promote trained adapter checkpoints with cryptographic provenance verification.
6. Browse curated task banks, review test metadata, and verify disjoint train/val/test splits.

---

## 2. Technical Stack & Frontend Architecture

| Layer | Technology | Rationale |
| :--- | :--- | :--- |
| **Framework** | React 18+ & TypeScript | Strict type safety aligned with Pydantic contracts |
| **Build Tool** | Vite 5+ | Fast HMR during development; optimized static build |
| **Styling** | Vanilla CSS / CSS Modules or TailwindCSS | Premium dark-mode aesthetic consistent with AI Lab Studio |
| **Icons & Visuals**| Lucide-React | Crisp, modern operational iconography |
| **Data Fetching** | TanStack Query (React Query) | Cache management, polling fallbacks, optimistic updates |
| **Real-Time** | Server-Sent Events (SSE) | Built-in browser reconnection; reuses AI Lab SSE patterns |
| **Code Display** | PrismJS / Monaco Editor / Highlight.js | Syntax-highlighted Python candidate code and test diffs |
| **Hosting** | Static mount under FastAPI | Built to `coding-training/console/dist/` and served at `/console/` on Mac Mini |

---

## 3. View Specifications

### 3.1 View 1: Dashboard (`/console/`)
- **System Tier Cards:**
  - **Mac Mini Controller (`mac-mini:8092`):** API uptime, PostgreSQL connection pool, Redis cache status, active worker leases.
  - **Mac Studio Model Service (`mac-studio:8090`):** Loaded base model (`Qwen3-0.6B`), GPU/Unified Memory footprint, inference latency, MLX trainer readiness.
  - **Linux Sandbox Worker (`192.168.99.10:8095`):** Worker attestation digest, OCI container image hash, cgroups v2 availability, network egress verification (`deny_all` verified).
- **Recent Activity Feed:** Last 10 candidate executions, recent evaluations, and latest checkpoints.
- **Safety Status Banner:** Prominent indicators for `EXECUTION_ENABLED`, `TRAINING_ENABLED`, and `RL_ENABLED`.

### 3.2 View 2: Playground (`/console/playground`)
- **Model Selector:** Dropdown of cataloged base models and fine-tuned checkpoints.
- **Prompt Editor:** Prompt template, function signature, and problem docstring.
- **Generation Controls:** Sampling sliders (`temperature`, `top_p`, `max_tokens`, `seed`).
- **Interactive Execution:**
  - **"Generate Candidate"** button -> prompts model, displays extracted Python code with AST syntax validation badge.
  - **"Execute in Sandbox"** button -> dispatches code to Linux sandbox worker, streaming execution stdout/stderr out-of-band.
  - **Results Drawer:** Exit code, elapsed ms, memory peak, test pass count (`passed / total`), and deterministic reward score.

### 3.3 View 3: Experiments (`/console/experiments`)
- **Experiment List:** Filterable by status (`DRAFT`, `RUNNING`, `COMPLETED`, `FAILED`).
- **New Experiment Wizard:**
  - Select task dataset and split.
  - Choose training mode (Verified SFT LoRA vs. Execution-Reward RL).
  - Configure hyperparameters (rank, alpha, learning rate, batch size, epochs / group size, beta).
- **Approval Gate Modal:** Mandatory confirmation dialog displaying estimated compute time, memory requirements, and parameter change warning. Self-approval is prevented.
- **Experiment Detail View:** Run configuration, artifact checksums, parameter loss graphs, and checkpoint milestones.

### 3.4 View 4: Live Monitor (`/console/monitor`)
- **Real-Time Stream:** Live SSE feed connected to `/v1/events/stream`.
- **Telemetry Visualizations:**
  - Tokens generated per second.
  - Candidate test pass rate trendline.
  - Reward score distribution histogram (0.0 to 1.0).
  - Training step loss and gradient norm curve.
  - Infrastructure error rate (quarantined jobs).

### 3.5 View 5: Models & Checkpoints (`/console/models`)
- **Catalog Table:** Base models, revisions, licenses, and MLX quantization support.
- **Adapters & Checkpoints:**
  - Checkpoint ID, training run reference, step number, initial/final adapter SHA-256 hashes.
  - Held-out evaluation benchmarks: `pass@1` and `pass@k` comparisons vs base model.
- **Promotion Workflow:** Mark verified adapter as candidate for inference deployment with audit record.

### 3.6 View 6: Datasets & Tasks (`/console/datasets`)
- **Task Browser:** Search and filter curated Python challenges by difficulty, tags, and family ID.
- **Task Inspector:** Prompt, function signature, and non-sensitive test metadata (number of assertions, test bundle SHA-256). Hidden test bodies remain inaccessible.
- **Partition Visualizer:** Graphical breakdown of `train` (70%), `val` (15%), and `test` (15%) splits with family-disjoint verification badge.

---

## 4. Operational & Security Requirements

1. **Authentication:** Uses AI Lab session cookie or Tailscale identity header (`Tailscale-User-Login`). Unauthenticated requests redirect to login.
2. **Confined Execution:** The console NEVER invokes local shells or host interpreters. All execution requests route through the FastAPI controller to the attested sandbox worker.
3. **No Fabricated Data:** Empty states and service-down indicators are shown honestly when backends are unreachable.
4. **Safety Confirmation:** Mutating operations (starting training, cancelling jobs, promoting checkpoints) require explicit confirmation modals.
5. **Private Network Binding:** The console is bound to `127.0.0.1` and accessed via Tailscale MagicDNS (`http://mac-mini:8092/console/`), never published to `0.0.0.0`.

---

## 5. Acceptance Criteria

- [ ] Console loads cleanly in Chrome/Safari on macOS and iPad/mobile viewport.
- [ ] Operator can select a model, enter a task prompt, generate code, execute it in the sandbox worker, and view out-of-band test results and rewards.
- [ ] Operator can configure and launch a training experiment with explicit confirmation.
- [ ] Live telemetry updates dynamically via SSE without manual browser refresh.
- [ ] Model evaluation comparison view correctly contrasts base model vs SFT checkpoint pass@1 scores.
- [ ] 100% of frontend unit tests and end-to-end integration tests pass.
- [ ] Zero untrusted code execution occurs on the browser or host machine.
