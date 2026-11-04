# IWO-128 — Coding Training Console Assistant and Chatbot Copilot

**Status:** Complete  
**Priority:** P2  
**Effort:** M  
**Owner:** Steven Gerhart  
**Feature:** FEAT-024  
**Services / Areas:** `coding-training/console/`, `coding-training/services/controller/`, web

## Problem

The Coding Model Training Console (`FEAT-024`) provides deep visibility into training topologies, sandbox containment, curated tasks, SFT/RL experiments, and live telemetry. However, operators exploring or managing training currently have no conversational copilot to ask questions about the training loop, explain reinforcement learning (GRPO) advantage calculation, diagnose sandbox failures or loss divergence, or get guided code assistance for candidate tasks.

## Decision Context

- Chosen approach:
  1. Add a dedicated **Assistant View** (`AssistantView.tsx`) in `coding-training/console/` accessible via the primary navigation bar.
  2. Add an omni-present **Floating Assistant Drawer** (`FloatingAssistantDrawer.tsx`) accessible from any view (Playground, Experiments, Monitor, Models, Datasets) with context-aware quick prompts for the active screen.
  3. Implement grounded, domain-specific intelligence covering Apple Silicon MLX LoRA, GRPO policy updates, sandbox containment (`CLONE_NEWNET`, cgroups v2), deterministic reward scoring (v1), and the 105 curated Python tasks.
  4. Expose `POST /v1/assistant/chat` in the FastAPI controller (`coding-training/services/controller/app.py`) with fallback to local client intelligence if offline.
- Alternatives rejected:
  - Third-party cloud LLM dependency in the frontend: violates air-gap and local-first architecture.
  - Separate external chat application: fragments operator workflow away from active experiments and sandboxes.
- Assumptions:
  - Assistant responds locally with grounded architecture knowledge and can query local model backend when available.

## What To Build / Fix

1. **Frontend Types & API Client:**
   - Update `coding-training/console/src/types.ts` to include `'assistant'` in `ViewType` and define `ChatMessage` contracts.
   - Update `coding-training/console/src/services/api.ts` with `askTrainingAssistant(message, context)`.
2. **Dedicated Full-Page Assistant View:**
   - Create `coding-training/console/src/views/AssistantView.tsx` with message stream, quick prompt starters, markdown code snippets with copy button, and cluster context drawer.
3. **Floating Omni-Present Assistant Drawer:**
   - Create `coding-training/console/src/components/FloatingAssistantDrawer.tsx` allowing one-click side-by-side questioning on any console screen.
4. **Header & Navigation Integration:**
   - Update `coding-training/console/src/components/Header.tsx` and `App.tsx` to mount the assistant tab and floating drawer.
5. **Controller Backend Endpoint:**
   - Add `POST /v1/assistant/chat` to `coding-training/services/controller/app.py`.
6. **Styling & Aesthetics:**
   - Add glassmorphic styling, glowing badges, code block presentation, and smooth transition animations in `coding-training/console/src/index.css`.
7. **Tests:**
   - Add unit test for `/v1/assistant/chat` in `coding-training/tests/unit/test_controller.py`.
   - Validate TypeScript compilation (`npm run build`).

## Expected Change Surface

- Expected:
  - `coding-training/console/src/types.ts`
  - `coding-training/console/src/services/api.ts`
  - `coding-training/console/src/views/AssistantView.tsx`
  - `coding-training/console/src/components/FloatingAssistantDrawer.tsx`
  - `coding-training/console/src/components/Header.tsx`
  - `coding-training/console/src/App.tsx`
  - `coding-training/console/src/index.css`
  - `coding-training/services/controller/app.py`
  - `coding-training/tests/unit/test_controller.py`
- Tests: `npm --prefix coding-training/console run build`, `python3 -m unittest discover -s tests -v`
- Docs/status: `docs/features/FEAT-024-execution-verified-coding-model-training.md`, `docs/work-orders/README.md`

## Out Of Scope

- External commercial cloud API keys or leaking hidden test bundles to prompts.
- Running untrusted code on macOS workstations.

## Do NOT Change

- Do not alter existing task bundles or hash verification mechanics.
- Maintain `127.0.0.1` binds and fail-closed safety switches.

## Acceptance Criteria

1. Navigating to the console displays the new "Training Copilot" navigation tab and the floating assistant trigger button.
2. Full Assistant View allows conversational querying with rendered code snippets, copy actions, and preset quick prompts.
3. Floating Assistant Drawer opens smoothly over any view (Playground, Experiments, Monitor) with contextual awareness of the active tab.
4. `POST /v1/assistant/chat` responds to platform architecture, GRPO, SFT, reward scoring, and task queries.
5. Console compiles cleanly (`tsc -b && vite build`) and controller unit tests pass.

## Validation Plan

- Automated: `npm --prefix coding-training/console run build && python3 -m unittest discover -s coding-training/tests -v`
- Manual: Browser test navigating the Assistant view and testing floating drawer in Playground.

## AI Lab gates (required)

- **Creates runtime job on mac-mini?** No
- **Host deploy / mutate authorized by this IWO alone?** No
- **Privileged tools expected?** none
- **May run on Air?** Yes (frontend dev and unit tests)

## Execution

- **Branch:** `main`
- **Risk tier:** P2
- **Pre-PR / pre-merge gate:** `./scripts/validate-repo.sh && ./tests/test_structure.sh`
- **Depends on:** `FEAT-024`, `IWO-117`
- **Human verification required:** Yes
- **Reviewer / approver:** Steven Gerhart
- **Project status record:** `docs/work-orders/README.md`

## Closeout

- Verification evidence:
  - Production console bundle built cleanly: `dist/index.html` (0.95 kB), `dist/assets/index-DIm9fH9_.js` (307.05 kB) in 244ms.
  - Python controller unit test passed: `test_controller_assistant_chat` verified in `coding-training/tests/unit/test_controller.py`.
  - Full coding training suite passed: 72/72 tests OK.
  - Live browser verified: Assistant workspace (`console_copilot_workspace`) and floating drawer (`console_floating_copilot`) responsive and active on `http://127.0.0.1:5173/`.
  - Repo validation: `./scripts/validate-repo.sh && ./tests/test_structure.sh` returned `RESULT: OK`.
- Follow-ons filed: none
- Residual risks: none; completely local-first and bounded to loopback.
- Docs/status updated: `docs/work-orders/README.md`, `docs/features/FEAT-024-execution-verified-coding-model-training.md`.
- Status surfaces reconciled: Yes
- Summary metadata reviewed: Yes
- Planning-only change? No
- Host deploy performed? No
