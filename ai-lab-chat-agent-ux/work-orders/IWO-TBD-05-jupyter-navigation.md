# IWO-TBD-05 — Jupyter and model workspace polish
**Status:** Proposed · **Depends on:** IWO-TBD-01; may run in parallel with -02

## Objective
Preserve one-click Studio Jupyter as a first-class AI Lab action without confusing notebook execution with mini-side agent execution.

## Work
1. Keep existing Jupyter launch endpoint and surface a prominent action from chat.
2. Show actual Studio reachability and clear unavailable state.
3. Review token-bearing launch URL handling, browser-history/log exposure, and redaction; coordinate security fixes rather than copying token URLs into badges or diagnostics.
4. Show selected model and local/usage-billed state consistently with `/v1/models`.

## Acceptance
- Launch succeeds when Studio is available; fails clearly when unavailable.
- No token in UI status, tool trace, or copied diagnostics.
- Chat and notebook remain separate execution paths, clearly labeled.
- No model pulls or Studio service changes without owner approval.
