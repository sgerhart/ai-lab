# Frontend Console — Backend API Gap Analysis & Implementation Plan

**Context:** WO-10 AI Lab Coding Training Console  
**Date:** 2026-10-30  
**Status:** Architecture Review Complete  

---

## 1. Executive Summary

To support the 6 views of the **Coding Training Console** (WO-10) without disrupting ongoing core backend milestones (WO-02 Dataset, WO-03 Sandbox Worker, WO-05 Model Adapter), this analysis compares the required frontend operations against existing typed contracts in `packages/contracts/` and defines the exact REST and SSE routes to be hosted by the FastAPI controller.

**Key Finding:** The underlying Pydantic contracts ([`Task`](file:///Users/stevengerhart/workspace/github/sgerhart/ai-lab/coding-training/packages/contracts/tasks.py#L21-L36), [`ExecutionRequest`](file:///Users/stevengerhart/workspace/github/sgerhart/ai-lab/coding-training/packages/contracts/executions.py#L32-L43), [`ExecutionResult`](file:///Users/stevengerhart/workspace/github/sgerhart/ai-lab/coding-training/packages/contracts/executions.py#L46-L68), [`RewardResult`](file:///Users/stevengerhart/workspace/github/sgerhart/ai-lab/coding-training/packages/contracts/rewards.py#L15-L35), [`CheckpointManifest`](file:///Users/stevengerhart/workspace/github/sgerhart/ai-lab/coding-training/packages/contracts/checkpoints.py#L8-L24), [`WorkerAttestation`](file:///Users/stevengerhart/workspace/github/sgerhart/ai-lab/coding-training/packages/contracts/attestation.py#L8-L17)) created in WO-01 already model 90% of the domain entities. What is missing is the HTTP routing and database query layer in the FastAPI controller, which is scheduled for **WO-04 (Control Plane and Queue)**.

---

## 2. View-by-View API Contract Mapping & Gap Analysis

### 2.1 View 1: Dashboard (`/console/`)

| Data Required | Existing Contract | Proposed Controller Route | Implementation Gap |
| :--- | :--- | :--- | :--- |
| **Mac Mini Controller Status** | `HealthStatus` | `GET /v1/system/health` | Route needed; checks Postgres connection pool, Redis ping, disk space. |
| **Mac Studio Service Status** | `HealthStatus`, `ModelCapabilities` | `GET /v1/system/compute-status` | Proxy check to `http://mac-studio:8090/health`. |
| **Sandbox Worker Status** | `WorkerAttestation` | `GET /v1/system/workers` | Query active worker heartbeat table in PostgreSQL. |
| **Summary Metrics & Recent Runs**| `AuditEvent` | `GET /v1/dashboard/summary` | Aggregate query: active jobs, 24h candidate count, recent runs. |

### 2.2 View 2: Playground (`/console/playground`)

| Data Required | Existing Contract | Proposed Controller Route | Implementation Gap |
| :--- | :--- | :--- | :--- |
| **Available Models List** | `ModelConfig` | `GET /v1/models` | List cataloged base models and fine-tuned checkpoints. |
| **Interactive Code Generation** | `GenerationConfig`, `GenerationResult` | `POST /v1/playground/generate` | Calls `ModelBackend.generate()`, returns extracted Python code. |
| **Interactive Sandbox Run** | `ExecutionRequest`, `ExecutionResult` | `POST /v1/playground/execute` | Enqueues one-off execution to sandbox worker without creating an experiment run. |
| **Deterministic Reward Scoring** | `RewardResult` | `POST /v1/playground/score` | Passes `ExecutionResult` to `RewardEngine.score()`. |

### 2.3 View 3: Experiments (`/console/experiments`)

| Data Required | Existing Contract | Proposed Controller Route | Implementation Gap |
| :--- | :--- | :--- | :--- |
| **List Experiments** | N/A | `GET /v1/experiments` | Query `experiments` table in PostgreSQL. |
| **Create Experiment** | `EnvironmentConfig`, `SFTConfig`, `RLConfig` | `POST /v1/experiments` | Validate config, compute config hash, store in Postgres. |
| **Experiment Detail & Telemetry** | N/A | `GET /v1/experiments/{id}` | Status, configuration, step milestones, loss history. |
| **Approval Gate** | `AuditEvent` | `POST /v1/training-jobs/{id}/approve`| Signed operator approval check; transitions state from `PREFLIGHT` to `RUNNING`. |
| **Cancel Job** | N/A | `POST /v1/training-jobs/{id}/cancel` | Sets job state to `CANCELLED`, signals worker to abort. |

### 2.4 View 4: Live Monitor (`/console/monitor`)

| Data Required | Existing Contract | Proposed Controller Route | Implementation Gap |
| :--- | :--- | :--- | :--- |
| **Real-time Event Stream** | `AuditEvent`, `ExecutionResult`, `RewardResult` | `GET /v1/events/stream` (SSE) | Server-Sent Events stream emitting job status transitions, test outcomes, and loss steps. |
| **Historical Metrics Timeline**| N/A | `GET /v1/telemetry/timeline` | Timeseries query: generation tokens/s, test pass rate moving average. |

### 2.5 View 5: Models & Checkpoints (`/console/models`)

| Data Required | Existing Contract | Proposed Controller Route | Implementation Gap |
| :--- | :--- | :--- | :--- |
| **List Model Catalog & Checkpoints** | `CheckpointManifest` | `GET /v1/checkpoints` | Query `checkpoints` table with initial vs final SHA-256 hashes. |
| **Checkpoint Detail & Provenance** | `CheckpointManifest` | `GET /v1/checkpoints/{id}` | Return full manifest, base commit, git SHA, and holdout evaluation scores. |
| **Promote Checkpoint** | `AuditEvent` | `POST /v1/checkpoints/{id}/promote` | Mark adapter as active for inference with operator audit log. |

### 2.6 View 6: Datasets & Tasks (`/console/datasets`)

| Data Required | Existing Contract | Proposed Controller Route | Implementation Gap |
| :--- | :--- | :--- | :--- |
| **Browse Tasks** | `Task`, `Split` | `GET /v1/tasks` | Filterable by difficulty, split, and family ID. |
| **Inspect Task & Test Metadata** | `Task`, `TestBundleRef` | `GET /v1/tasks/{id}` | Non-sensitive task details (prompt, signature, assertion count). Hidden tests omitted. |
| **Validate Dataset Split** | `DatasetManifest` | `POST /v1/datasets/validate` | Verify zero cross-split family leaks and hash integrity. |

---

## 3. Phased Implementation Plan

To prevent disrupting the core backend timeline, WO-10 is executed in three coordinated sub-phases:

```text
[Backend WO-02: Tasks]    [Backend WO-03: Sandbox]    [Backend WO-04: Controller APIs]
        │                           │                                │
        └───────────────────────────┼────────────────────────────────┘
                                    ▼
                ┌──────────────────────────────────────┐
                │ WO-10.1: Console Foundation & Mock   │
                │ - Vite + React 18 + TS setup         │
                │ - Shared layout, navigation, badges  │
                │ - Mock API client with mock data     │
                └──────────────────┬───────────────────┘
                                   │
                                   ▼
                ┌──────────────────────────────────────┐
                │ WO-10.2: Wire Live REST & SSE APIs   │
                │ - Typed OpenAPI fetch client         │
                │ - Dashboard, Playground, Datasets    │
                │ - Live Monitor with real SSE stream  │
                └──────────────────┬───────────────────┘
                                   │
                                   ▼
                ┌──────────────────────────────────────┐
                │ WO-10.3: Experiments & Checkpoints   │
                │ - Training configuration wizard      │
                │ - Approval modal gate                │
                │ - Build & mount under FastAPI        │
                └──────────────────────────────────────┘
```

### Sub-Phase WO-10.1: Console Foundation & UI Prototype (Parallel / Zero-Risk)
- Scaffold `coding-training/console/` with React, TypeScript, Vite, TailwindCSS, and Lucide icons.
- Build the 6 view layouts with mock API handlers (`MockApiClient`), allowing full visual and user-interaction verification before backend routes are completed.
- Test responsive layout and dark-mode styling.

### Sub-Phase WO-10.2: Wire Core APIs with WO-04 Controller
- Implement controller endpoints (`/v1/system/health`, `/v1/tasks`, `/v1/playground/*`, `/v1/events/stream`) in `services/controller/` as part of WO-04.
- Switch frontend API client from mock to live FastAPI endpoints.
- Validate end-to-end playground flow in the browser.

### Sub-Phase WO-10.3: Training Management, Packaging, and E2E Testing
- Wire experiment configuration wizard and approval modals.
- Set up Vite production build output to `coding-training/console/dist/`.
- Mount static files in FastAPI controller at `/console/`.
- Add automated end-to-end browser tests verifying user workflows.
