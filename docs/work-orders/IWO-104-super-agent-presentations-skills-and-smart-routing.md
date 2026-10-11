# Implementation Work Order: IWO-104 — Super Agent: Presentations, Dynamic Skills, and Smart Model Routing

**Title:** Super Agent Expansion: Presentation Generation, Dynamic Skill Library, Safe MCP, and Smart Model Routing
**Status:** Completed
**Assigned to:** Pair / Agent
**Date:** 2026-10-11
**Related Documents:**
- `docs/features/FEAT-008-research-retrieval-memory.md`
- `docs/features/FEAT-011-frontier-model-access.md`
- `docs/features/FEAT-013-agent-definitions.md`
- `docs/work-orders/IWO-103-conversational-scheduling-and-durable-memory.md`
- `AGENTS.md`

---

## 1. Objective

Enhance the AI Lab agent harness to support high-tier creative, procedural, and cognitive capabilities while maintaining 100% strict security boundaries:
1. **Interactive Presentations & Slides (`presentation_write`, `presentation_list`)**: Generate standalone HTML slide decks and markdown slides for executive briefings, architecture proposals, and roadmaps.
2. **Dynamic Skill Library (`skill_create`, `skill_list`, `skill_read`)**: Enable the agent to construct, persist, list, and read custom procedural skills under `~/.ai-lab/skills/`.
3. **Safe MCP Discovery & Inspection (`mcp_list_tools`, `mcp_server_status`)**: Allow agents to query allowed MCP tools and server statuses.
4. **Smart Auto Model Routing**: Intelligently route user prompts to the best local model (`qwen3-coder:30b` for code/git, `llama3.2:3b` for fast tasks, `qwen3.6:35b-a3b` for complex second brain reasoning) with clear composer UI labels.
5. **100% Integrated Security**: Full path confinement, sanitized output rendering, strict MCP allowlist enforcement, and explicit approval gates for high-risk actions.

---

## 2. Requirements & Deliverables

1. `platform/src/ai_lab_platform/presentations.py`:
   - `PresentationLibrary`: Manage slide decks under `~/.ai-lab/presentations`. Generate clean, standalone HTML slide presentations with keyboard navigation.
2. `platform/src/ai_lab_platform/skills_library.py`:
   - `SkillLibrary`: Manage procedural skills under `~/.ai-lab/skills/`. Format standard `SKILL.md` documents.
3. `platform/src/ai_lab_platform/tool_runtime.py`:
   - Register `presentation_write`, `presentation_list`, `skill_create`, `skill_list`, `skill_read`.
4. `agents/personal/policy.json`:
   - Add new tool permissions to the personal agent policy.
5. Smart Model Routing in `control_app.py` & `agents.html`:
   - Support `auto` model selection.
   - Clarify `Mode:` and `Model:` in chat composer footer.

---

## 3. Validation

- Comprehensive unit tests covering presentation creation, skill saving/reading, and model routing.
- `./scripts/validate-repo.sh && ./tests/test_structure.sh` pass.
- Verified and deployed to Mac mini control plane daemon.
