# IWO-117 — Coding Training Console Specification and Phased Plan

**Status:** Completed  
**Priority:** P2  
**Effort:** L  
**Owner:** Steven Gerhart  
**Feature:** FEAT-024  
**Services / Areas:** `coding-training/console/`, FastAPI controller, web

## Problem

Operating the coding model training platform currently relies on scripts and raw REST API calls. To enable frictionless observation, model testing, training experiment management, live telemetry monitoring, and dataset exploration without exposing the operator to database queries or raw message queues, a web console is required.

## Decision Context

- Chosen approach: React 18+, TypeScript, and Vite sub-project at `coding-training/console/`.
- Built to static assets (`console/dist/`) and served directly by the FastAPI controller at `/console/`.
- 6 dedicated views: Dashboard, Playground, Experiments, Live Monitor, Models, and Datasets.
- Zero local code execution in the browser: all candidate generation and test evaluation route strictly to the isolated Linux sandbox worker on Proxmox.
- Gap analysis completed in `coding-training/docs/gap-analysis-console-api.md`.

## Phased Implementation Plan

1. **Sub-Phase 10.1 (UI Prototype & Mock Client):**
   - Scaffold Vite + React + TS under `coding-training/console/`.
   - Implement the 6 view components with mock API adapters (`MockApiClient`).
   - Validate responsive design, dark mode, and error/empty states.
2. **Sub-Phase 10.2 (Wire Controller REST & SSE Endpoints):**
   - Connect frontend to FastAPI endpoints implemented in WO-04 (`/v1/system/health`, `/v1/tasks`, `/v1/playground/*`, `/v1/events/stream`).
   - Validate live playground model prompt -> code generation -> sandbox execution -> reward scoring.
3. **Sub-Phase 10.3 (Experiments Wizard, Checkpoint Promotion & E2E Tests):**
   - Wire experiment configuration wizard and mandatory approval confirmation modal.
   - Wire checkpoint provenance display and promotion workflow.
   - Add automated browser tests and deployment build step.

## Outcomes and Delivered Surface

- **Console Frontend**: React 18, Vite, TypeScript console application scaffolded at `coding-training/console/`. Built production bundle at `coding-training/console/dist/` in 488ms.
- **6 Core Views Delivered**:
  - `DashboardView.tsx`: KPI cards, cluster host topology status (`mac-mini: 8000`, `mac-studio: 8001`, `proxmox: 8002`), recent training runs.
  - `PlaygroundView.tsx`: Task selector, model selector, candidate code editor, sandbox execution dispatcher, test case breakdown bar, stdout/stderr console, deterministic reward score.
  - `ExperimentsView.tsx`: SFT LoRA / RL GRPO launcher wizard, human approval modal (`TRAINING_ENABLED`), SVG loss/reward curves, runs table.
  - `MonitorView.tsx`: SSE real-time telemetry streaming (`/v1/events/stream`), worker status, live filtered terminal log with regex search.
  - `ModelsView.tsx`: Base models catalog, fine-tuned LoRA checkpoints with cryptographic SHA-256 hashes, parameter divergence verification.
  - `DatasetsView.tsx`: 105 verified Python tasks browser, split filters (`train`, `val`, `test`), difficulty filter, quarantined test boundary inspection.
- **Controller Integration**: Mounted static bundle at `/console` on controller FastAPI app, root redirect `/` -> `/console/`, added `/v1/tasks`, `/v1/models`, and `/v1/events/stream`.
- **Gate Record**: `coding-training/docs/gates/WO-10.md`.
- **Validation**: 71/71 tests pass in `coding-training/` (`make check`). Zero browser execution; all sandbox execution routes to isolated Proxmox Linux VM.

## Expected Change Surface

- Expected: `coding-training/console/`, `coding-training/docs/gates/WO-10.md`, `coding-training/services/controller/app.py`, `coding-training/tests/unit/test_controller.py`.
- Tests: `npm run build`, `make check`.
- Docs/status: `docs/features/index.md`, `docs/features/FEAT-024-execution-verified-coding-model-training.md`.

## Do NOT Change

- Do not disrupt ongoing backend milestones (WO-02 through WO-08).
- Do not execute candidate code inside the frontend or on Mac hosts.
- Do not publish the console to `0.0.0.0`; bind to `127.0.0.1` and access via Tailscale.

