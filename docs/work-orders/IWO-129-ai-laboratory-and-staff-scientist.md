# IWO-129 — AI Laboratory Workbench & Staff Scientist Peer Agent

**Status:** Draft  
**Priority:** P2  
**Effort:** M  
**Owner:** Steven Gerhart  
**Feature:** FEAT-025  
**Services / Areas:** platform, docs, web  

Canonical AI Lab implementation Work Order for FEAT-025.

## Problem

The operator needs a functional, easy-to-use **AI Laboratory** workbench covering all AI model paradigms (Language & SLMs, Vision, Diffusion/Generative, Audio, Multimodal, and Reinforcement Learning), paired with a collaborative **Staff Scientist** (Lab Manager / Research Partner) peer agent.

The previous prototype ("Classroom") attempted to simulate handwriting on a canvas whiteboard with robotic browser speech, which failed to provide serious engineering utility and caused frustration. The operator already owns **192 books and research papers** indexed on disk in Knowledge Nexus (`~/.ai-lab/nexus/`). The laboratory must integrate directly with these books, live internet research, and local models to enable interactive, back-and-forth scientific dialogue, mathematical breakdowns with numerical intuition, and quick sandbox verification without toy gimmicks.

## Decision Context

- **Chosen approach:**
  1. Build a clean, high-density **AI Laboratory** interface (`/lab`) linked in the primary navigation bar.
  2. Implement an in-memory **Laboratory Model & Concept Catalog** (`lab_workbench.py`) spanning Language, Vision, Diffusion, Audio, Multimodal, and RL. Each concept provides:
     - Architecture & tensor flow summary (e.g. $[B, S, D]$ transitions).
     - First-principles mathematical explanation with variable definitions and real-number examples.
     - Runnable 10–30 line PyTorch/MLX sandbox verification snippet.
     - Direct chapter citations to the operator's 192 books and research papers in Knowledge Nexus.
  3. Implement the **Staff Scientist** peer agent (`scientist_agent.py`) using local models on Ollama (`qwen3.6:35b-a3b`, `llama3.1`). The persona is a collegial research scientist working alongside the operator in back-and-forth dialogue, equipped with:
     - `search_nexus_books(query)`: RAG search across the 192 local books/papers on disk.
     - `search_web(query)`: Factual web search for modern updates, arXiv preprints, and documentation.
- **Alternatives rejected:**
  - Canvas whiteboard animations (unreliable, slow, visual clutter).
  - Browser SpeechSynthesis (unnatural, robotic cadence).
  - Hardcoded LLM-only curriculum (ignoring vision, diffusion, audio, and RL).
- **Assumptions:**
  - Knowledge Nexus local mirror exists at `~/.ai-lab/nexus/` with `disk-books.json`.
  - FastEmbed/Qdrant or hash embeddings available for book retrieval; DuckDuckGo/Wikipedia available for web lookup.
- **Open decisions:**
  - None blocking drafting.

## What To Build / Fix

1. **Backend Modules:**
   - `platform/src/ai_lab_platform/lab_workbench.py`:
     - Multi-paradigm catalog data structure (`LabConcept`, `ArchitectureCard`).
     - Pre-populated concepts across Language (Self-Attention, RoPE, SwiGLU, SFT, LoRA), Vision (ViT, Patch Projections), Diffusion (DDPM Noise Schedule, Flow Matching), Multimodal (Cross-Attention), Audio (Spectrogram to Token), and RL (PPO, DeepSeek GRPO).
     - Linkages to Nexus book titles and chapters.
   - `platform/src/ai_lab_platform/scientist_agent.py`:
     - Staff Scientist agent loop with peer scientist system prompt.
     - Tool binding: `search_nexus_books` and `search_web`.
     - Context grounding with the currently selected workbench concept.
   - `platform/src/ai_lab_platform/control_app.py`:
     - `GET /lab`: Serves `lab.html`.
     - `GET /v1/lab/catalog`: Returns paradigms, models, and concepts.
     - `POST /v1/lab/scientist/chat`: Handles conversational turns with the Staff Scientist.
2. **Frontend UI:**
   - `platform/src/ai_lab_platform/web/lab.html`:
     - Clean, dark-theme three-column layout:
       - Left: Paradigm & concept navigator with instant search.
       - Center: Laboratory Workbench (Tensor flow, Plain-English math with numbers, runnable snippet, Nexus book citations).
       - Right: Collegial Staff Scientist dialogue console with citation cards.
   - `platform/src/ai_lab_platform/web/static/lab.js`:
     - Reactive state management, KaTeX math formatting, snippet copy/run, and scientist chat stream.
   - `platform/src/ai_lab_platform/web/static/chrome.js`:
     - Add `{ href: "/lab", label: "Laboratory", active: /^\/lab$/.test(path) }`.
3. **Tests & Validation:**
   - `tests/test_lab_workbench.py`: Test catalog lookup, schema validity, and book citation resolution.
   - `tests/test_scientist_agent.py`: Test peer scientist prompt structure, tool execution (mocked RAG and web search), and response parsing.

## Expected Change Surface

- Expected:
  - `platform/src/ai_lab_platform/lab_workbench.py`
  - `platform/src/ai_lab_platform/scientist_agent.py`
  - `platform/src/ai_lab_platform/control_app.py`
  - `platform/src/ai_lab_platform/web/lab.html`
  - `platform/src/ai_lab_platform/web/static/lab.js`
  - `platform/src/ai_lab_platform/web/static/chrome.js`
- Tests:
  - `tests/test_lab_workbench.py`
  - `tests/test_scientist_agent.py`
- Docs/status:
  - `docs/features/FEAT-025-ai-laboratory-and-staff-scientist.md`
  - `docs/work-orders/IWO-129-ai-laboratory-and-staff-scientist.md`
  - `docs/features/index.md`
  - `docs/work-orders/README.md`

## Out Of Scope

- Canvas handwriting animations or browser speech synthesis.
- Downloading gigabytes of new model checkpoints to disk without separate authorization.
- Hypervisor / bare-metal virtualization changes.

## Do NOT Change

- Bounded tool execution rules in `tools.py` and `AGENTS.md`.
- No secrets committed to Git.
- Binds stay on loopback or Tailscale IPv4 (`100.80.117.123`).
- Host deployment remains gated and unauthorized until separate user confirmation.

## Acceptance Criteria

1. `GET /lab` returns 200 OK and serves the AI Laboratory workbench HTML.
2. `GET /v1/lab/catalog` returns structured concepts for Language, Vision, Diffusion, Audio, Multimodal, and RL.
3. Each concept includes tensor flow, plain-English math with numbers, runnable code snippet, and Nexus book references.
4. `POST /v1/lab/scientist/chat` returns grounded peer dialogue citing local books or web search.
5. Top navigation in `chrome.js` includes the `Laboratory` link.
6. `python3 -m unittest discover -s tests -v` passes with 0 failures.
7. `./scripts/validate-repo.sh` passes with `RESULT: OK`.

## Validation Plan

- Automated:
  - `python3 -m unittest tests/test_lab_workbench.py tests/test_scientist_agent.py -v`
  - `python3 -m unittest discover -s tests -v`
  - `./scripts/validate-repo.sh`
- Manual:
  - Open `http://127.0.0.1:8088/lab` (or `http://100.80.117.123:8088/lab` when deployed).
  - Verify paradigm switching (Language, Vision, Diffusion, etc.).
  - Ask the Staff Scientist a question about a concept and verify citations from local Nexus books.
- Evidence to include:
  - Test output logs and endpoint responses.

## AI Lab gates (required)

- **Creates runtime job on mac-mini?** No
- **Host deploy / mutate authorized by this IWO alone?** **No** — always requires a separate human authorization.
- **Privileged tools expected?** none
- **May run on Air?** Yes (offline unit tests and local mock verification).

## Execution

- **Branch:** `main` (or feature branch if preferred by operator)
- **Risk tier:** P2
- **Pre-PR / pre-merge gate:** `./scripts/validate-repo.sh && python3 -m unittest discover -s tests -v`
- **Depends on:** FEAT-008, FEAT-010, FEAT-022
- **Human verification required:** Yes (review and deploy authorization)
- **Reviewer / approver:** Steven Gerhart
- **Project status record:** `docs/features/index.md`
- **Other status surfaces:** `docs/work-orders/README.md`

## Closeout

- Verification evidence: (Pending execution)
- Follow-ons filed: none
- Residual risks: none
- Docs/status updated: (Pending execution)
- Status surfaces reconciled: (Pending execution)
- Summary metadata reviewed: (Pending execution)

