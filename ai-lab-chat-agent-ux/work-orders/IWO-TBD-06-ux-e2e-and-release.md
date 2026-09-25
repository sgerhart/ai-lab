# IWO-TBD-06 — Chat-first end-to-end validation and release
**Status:** Proposed · **Depends on:** IWO-TBD-01 through -05; security verification

## Objective
Prove that AI Lab is useful as a chat-first personal assistant on the actual three-machine topology.

## Work
1. Add deterministic fixture MCP/built-in tools, simulated Studio offline, stale health, denied action, and read-only lab-health task.
2. Test first-run onboarding, chat history, badges, actual tool use, background task, Air disconnect/reconnect, approval, Jupyter launch.
3. Run CI and repository validation; perform separately authorized live mini/Studio smoke test.
4. Reconcile README, feature index, roadmap, runbook and status: implemented vs deployed vs live verified.
5. Record operator feedback and defer cosmetic extras that do not improve the core task.

## Acceptance
- Operator completes the end-to-end lab-health scenario without visiting agent-definition settings.
- Same run/result appears after Air disconnect; no duplicate run.
- Badges reflect available/used/authorized states accurately.
- Unauthorized action denied; no secret leak; no paid fallback.
- Jupyter launch preserved; accessibility checks pass.
- Live worker restart behavior reported truthfully, with remaining risks as follow-on IWOs.

## Out of scope / gates
No live Clarion test, autonomous coding writes, PR merge, deployment or spending unless separately authorized.
