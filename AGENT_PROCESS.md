# Agent Process For Work Orders (AI Lab)

This is the front door for coding agents working in **`ai-lab`**. It adapts
[`dentroio/work-order-protocol`](https://github.com/dentroio/work-order-protocol)
`AGENT_PROCESS.md` to this repository.

Also read [`AGENTS.md`](AGENTS.md) (repo identity, secrets, deploy authorization).

## Three kinds of “work order” (do not conflate)

| Kind | Where | ID shape | Purpose |
|------|-------|----------|---------|
| **Feature** | `docs/features/` | `FEAT-NNN` | Desired capability / outcome |
| **Implementation Work Order** | `docs/work-orders/IWO-*.md` or GitHub issue from the WO template | `IWO-…` / issue | Bounded engineering contract (this protocol) |
| **Runtime work order** | Postgres on `mac-mini` via `POST /v1/work-orders` | UUID | Live execution record (LangGraph + approvals) |

Historical `WO-000`–`WO-007` are **phase build records**, not the protocol
template and not runtime jobs. See `docs/work-orders/README.md`.

Lifecycle mapping: [`docs/work-order-protocol/lifecycle-mapping.md`](docs/work-order-protocol/lifecycle-mapping.md).

## When Asked To Draft A Work Order

Drafting is **not** implementation authorization and **not** deploy
authorization.

1. Read this file, `templates/WO-template.md`, `docs/features/` (if relevant),
   and nearby ADRs / runbooks.
2. Inspect enough code and tests to ground the draft in evidence.
3. Separate verified facts from assumptions.
4. Mark open decisions that affect behavior, scope, risk, or acceptance.
5. Recommend a risk tier; do not silently reduce it. For AI Lab, anything that
   mutates hosts, pulls models, restores volumes, or changes network/SSH is at
   least **P0/P1** and always needs a human — see
   [`docs/work-order-protocol/risk-and-deploy-gates.md`](docs/work-order-protocol/risk-and-deploy-gates.md).
6. Leave the Work Order in `Draft` until a human accepts it.
7. Do **not** edit product/platform code, create an implementation branch, run
   `--apply` / compose `up` / model pull, or `POST` a runtime job unless the
   user **separately** authorizes that step.

## Rules (implementation)

1. Read the assigned Implementation Work Order before editing files.
2. Confirm dependencies and risk tier.
3. Stay inside scope; file follow-ons for adjacent work.
4. Preserve “Do NOT Change” items and AI Lab safety defaults (`AGENTS.md`).
5. Run the validation plan and quality gate.
6. Ask for human verification when required (always for deploy / privileged tools).
7. Update the project status surface (`docs/features/index.md` and/or the IWO
   Closeout) and leave verification evidence.
8. **Never** treat “IWO Accepted” as permission to deploy to `mac-mini`,
   `mac-studio`, or `mac-air`. Deploy requires an explicit human authorization
   in the conversation or a checked Deploy gate on the IWO that a human set to
   authorized.

## Implementation Checklist

```text
Read IWO / AGENT_PROCESS / AGENTS.md
  -> inspect current state
  -> claim or create branch (if implementing)
  -> implement within scope
  -> test / validate-repo
  -> human verification if required
  -> review
  -> update status / Closeout
  -> stop (do not deploy unless separately authorized)
```

## Never Do

- Do not treat vague acceptance criteria as permission to guess.
- Do not silently skip tests.
- Do not mix unrelated cleanup into the Work Order.
- Do not downgrade risk tier.
- Do not approve your own high-risk or deploy-gated spec.
- Do not claim completion without verification evidence.
- Do not let planning-only edits count as implementation completion.
- Do not invent hostnames, IPs, tailnet suffix, or credentials.
- Do not start Clarion/factory stacks from this repo, or lab compose on the Air.
- Do not create runtime Postgres jobs as a side effect of drafting an IWO.
