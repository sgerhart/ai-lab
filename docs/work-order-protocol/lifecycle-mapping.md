# Lifecycle mapping — protocol vs AI Lab runtime

The Work Order Protocol describes how **implementation** contracts move from
idea to verified closeout in Git. AI Lab **runtime** work orders are separate
Postgres rows executed by the M1 control plane.

## Protocol lifecycle (implementation)

From upstream `dentroio/work-order-protocol`:

```text
Observation
  -> Draft
  -> Readiness Review
  -> Accepted
  -> Claimed / Assigned
  -> Implemented
  -> Verified
  -> Reviewed
  -> Closed
  -> Follow-ons Filed
```

These states live on Markdown IWOs / GitHub issues. They are **not** columns in
Postgres.

## Runtime lifecycle (execution)

From `platform/src/ai_lab_platform/work_order.py` (`Status`):

```text
created
  -> queued
  -> running
  -> awaiting_approval   # privileged tool / human gate (ADR 0018)
  -> completed | failed | cancelled
```

Also: Studio down leaves the row **`queued`** with a visible `studio_unavailable`
error (does not vanish).

## Mapping (conceptual)

| Protocol (implementation IWO) | Runtime job (Postgres UUID) |
|-------------------------------|-----------------------------|
| Observation / Draft | No runtime row |
| Accepted / Claimed / Implemented / Verified / Reviewed / Closed | Still no runtime row unless a human (or authorized client) **submits** |
| — | `POST /v1/work-orders` → `created` / `queued` |
| — | Worker runs → `running` |
| Human approval of privileged *tool* use | `awaiting_approval` → resume |
| — | `completed` / `failed` / `cancelled` |

**Critical rule:** Closing or accepting an Implementation Work Order does
**not** create or complete a runtime job. Submitting to `mac-mini:8088` is a
separate operator action (FEAT-002).

## Features

`FEAT-*` specs sit above IWOs. One feature may require many IWOs. Features are
not runtime jobs either.

## Historical phase WOs

`WO-000`–`WO-007` document the initial repository/host build phases. Treat them
as archive + status evidence, not as the protocol template and not as live
UUID jobs.
