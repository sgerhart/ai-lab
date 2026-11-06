# FEAT-025 — AI Laboratory & Staff Scientist

- **Status:** Specified
- **Created:** 2026-11-05
- **Owner:** Steven Gerhart
- **GitHub issue:** draft only

## Purpose

Provide a functional, easy-to-use **AI Laboratory** workbench and a collaborative **Staff Scientist** (Lab Manager / Research Partner) peer agent integrated directly into the AI Lab platform. The laboratory covers all AI paradigms (Language & SLMs, Vision, Diffusion/Generative, Multimodal, Audio, and Reinforcement Learning). The Staff Scientist works alongside the human operator as a fellow scientist in active back-and-forth dialogue, able to research questions using the local 192-book Knowledge Nexus library or live web search, demystify mathematical concepts with numerical intuition, and run quick tensor tests in the lab sandbox.

## User workflow

1. **Accessing the Lab:** Operator navigates to `/lab` from the primary top navigation bar.
2. **Exploring Architectures & Models:** Operator filters or searches across AI paradigms (Language, Vision, Diffusion, Audio, Multimodal, RL, Math).
3. **Inspecting Mechanics:** For any selected concept or architecture, the workbench renders:
   - Architecture & Tensor Flow diagram (e.g. $[B, S, D]$ transitions).
   - First-principles mathematical breakdown with plain-English intuition, variable explanations, and real-number examples.
   - Runnable 10–30 line PyTorch/MLX sandbox verification snippet.
   - Grounded citations to the operator's local books and research papers in Knowledge Nexus.
4. **Peer Scientist Dialogue:** Operator chats with the Staff Scientist in an interactive, collegial dialogue panel:
   - Operator asks to dissect an equation, explain a paper, or compare architectures.
   - Staff Scientist queries local books via Nexus RAG (`nexus_rag.py`) or performs live web research (`web_lookup.py`) to answer with grounded citations.
   - Staff Scientist proposes and runs quick tensor/math experiments in the lab sandbox to verify behavior.

## Target host(s)

| Role | Host alias | Why |
|------|------------|-----|
| Control plane & Lab UI | `mac-mini` | Serves `/lab`, routes requests, orchestrates tools and dialogues |
| Model inference | `mac-mini` / `mac-studio` | Local Ollama models (`qwen3.6:35b-a3b`, `llama3.1`) power the Staff Scientist |
| Local Book Library | `mac-mini` | 192 books and papers mirrored at `~/.ai-lab/nexus/` |

## Dependencies

- Features: `FEAT-004` (Agent Chat & Dashboard), `FEAT-008` (Research Retrieval & Memory), `FEAT-010` (Mini Personal Agent Loop), `FEAT-022` (Steward & Nexus Study).
- ADRs / policies: ADR 0020 (LangGraph orchestration), ADR 0034 (Tailscale IPv4 bind), ADR 0037 (Mini owns personal agent loop).
- Hosts / services that must already be live: control plane on `mac-mini:8088`, Ollama inference server.

## Proposed deliverables

- **Docs:** This feature record (`FEAT-025`), Implementation Work Order (`IWO-129`).
- **Code modules:**
  - `platform/src/ai_lab_platform/lab_workbench.py`: Model catalog, architecture taxonomy, mathematical explainers, and sandbox runner.
  - `platform/src/ai_lab_platform/scientist_agent.py`: Staff Scientist peer agent loop with Nexus book search and web lookup tools.
  - `platform/src/ai_lab_platform/web/lab.html`: Clean, functional AI Laboratory workbench and collaborative dialogue UI.
  - `platform/src/ai_lab_platform/web/static/lab.js`: Interactive workbench state, KaTeX math rendering, model switcher, and scientist chat.
- **Navigation:** Add `{ href: "/lab", label: "Laboratory" }` to `platform/src/ai_lab_platform/web/static/chrome.js`.
- **Tests:** `tests/test_lab_workbench.py`, `tests/test_scientist_agent.py`.

## Proposed implementation work orders

| ID (proposed) | Title | Depends on | Acceptance (sketch) |
|---------------|-------|------------|---------------------|
| IWO-129 | AI Laboratory Workbench & Staff Scientist Peer Agent | FEAT-008, FEAT-010 | `/lab` route live; multi-paradigm catalog; scientist chat with Nexus and web search; unit tests pass |

## Acceptance criteria

- [ ] `/lab` is accessible via top navigation on the control plane.
- [ ] Multi-paradigm catalog covers Language, Vision, Diffusion, Audio, Multimodal, and RL with tensor flows, plain-English math with numbers, runnable snippets, and book citations.
- [ ] Staff Scientist agent engages in back-and-forth dialogue using both local Nexus books and live web search tools.
- [ ] All unit tests pass and `validate-repo.sh` succeeds.
- [ ] Human approval gates listed (no self-approval; separate deploy gate).

## Out of scope

- Re-creating toy whiteboard canvas animations or robotic browser text-to-speech.
- Pulling unvetted multi-gigabyte external model weights without separate operator authorization.
- Mutating remote hypervisors or cloud infrastructure.

## Implementation status (honest)

| Layer | Status | Evidence |
|-------|--------|----------|
| Spec in Git | Done | `docs/features/FEAT-025-ai-laboratory-and-staff-scientist.md` |
| Code | Not started | Awaiting IWO-129 acceptance |
| Deployed | No | Host deploy requires separate human authorization |

