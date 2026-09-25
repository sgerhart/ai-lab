# IWO-TBD-01 — Chat-first shell and default assistant
**Status:** Proposed · **Depends on:** design approval · **Scope:** UI and thin existing API integration

## Objective
Make the existing chat the default way to use AI Lab. A new operator can ask the AI Lab Assistant without creating an agent definition. Preserve Jupyter launch and existing chat history.

## Work
1. Inspect current `web/agents.html`, routes, agent definitions and conversations. Identify the smallest additive UI change; do not rewrite the app.
2. Add a default assistant preset mapped to existing agent-definition mechanics; ensure a normal chat does not silently become a background job.
3. Present Chat, Jupyter and Activity as discoverable primary destinations; move configuration and traces to secondary views.
4. Show actual selected provider/model, local vs usage-billed, and truthful mini/Studio health.
5. Keep existing chat and Jupyter behavior intact, including error states and authentication.

## Acceptance
- First visit → chat → answer with no manual agent creation.
- Existing conversations and Jupyter launch still work.
- Model/provider labels match recorded run; no silent paid fallback.
- Responsive and keyboard-accessible basic navigation.
- Tests + repo validation green; docs distinguish code-complete from live-verified.

## Out of scope / gates
No model pulls, host mutation, new router, new agent framework, paid calls, write tools, or unapproved commits/pushes. Follow `AGENTS.md`.
