# Security event envelope

**Status:** In Git (IWO-066). Not a live collector.  
**Schema id:** `ai-lab://security/event-envelope/v1`  
**Code:** `platform/src/ai_lab_platform/security/events.py` (`EVENT_SCHEMA`)

One JSON object correlates an agent, a run, a tool, a job, and an approval. Evidence is a locator plus a hash and a byte length. The object does not carry file bytes, samples, or secret values.

| Field | Meaning |
|-------|---------|
| `schema_version` | Always `1` |
| `event_id` | Stable id |
| `occurred_at` | UTC timestamp |
| `provider` | `antares`, `defenseclaw`, `vise`, `mcp`, `approval`, or `platform` |
| `severity` | `info`, `low`, `medium`, `high`, or `critical` |
| `classification` | `policy`, `approval`, `mcp`, `finding`, `evidence`, or `inventory` |
| `agent_id` | Agent identity. At least one of `agent_id` or `resource_id` is required |
| `resource_id` | MCP server, snapshot, job VM, or other resource |
| `run_id` | Existing agent-run id, when this event belongs to one |
| `job_id` | Existing Vise or Antares job id, when this event belongs to one |
| `tool` | Tool or capability name |
| `approval_id` | Existing approval id, when a gate applied |
| `summary` | Short operator text |
| `evidence` | External references only: `evidence_id`, `locator`, `sha256`, `media_type`, `byte_length` |
| `retention` | `until-operator-purge` unless the caller sets another label |
| `details` | Small JSON object. Secret-like keys are stored as `[redacted]`. Embedded payload fields are refused |

`locator` is an external reference such as `quarantine://operator-supplied/object`. The quarantine location itself is [D-023](../open-decisions.md) and is not invented here.

Read API, behind the same authentication as the rest of the control plane:

- `GET /v1/security/providers`
- `GET /v1/security/events/schema`
- `GET /v1/security/events`
- `POST /v1/security/events`
- `GET /v1/security/mcp`

These routes ship in Git. They are not a separate process and this change does not restart the mini.
