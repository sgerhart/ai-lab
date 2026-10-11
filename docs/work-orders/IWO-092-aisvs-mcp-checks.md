# IWO-092 — AISVS checks on lab MCP

**Status:** Draft  
**Priority:** P2  
**Effort:** M  
**Owner:** human (operator)  
**Feature:** [FEAT-018](../features/FEAT-018-ai-security-platform.md)  
**Services / Areas:** platform, docs

## Problem

Lab MCP is stdio, intake can store an unlisted server, and tool payloads are not checked before the model sees them. AISVS Level 1 rows 10.1.1, 10.2.1, 10.2.2, 10.3.2, 10.4.1, 10.4.2, and 10.4.3 are gap or partial in [the gap register](../security/aisvs-level-1.md). Rows 10.2.3 and 10.3.1 stay not applicable until the lab runs an OAuth resource server or a remote MCP transport.

## Decision Context

- Chosen approach: Fail closed in the client. An unlisted or unsigned server is not callable. Tool-list and tool-call JSON must match the declared schema and a maximum size. Tool text is marked untrusted before it re-enters the model. Stdio remains the only transport this IWO allows.
- Alternatives rejected: Implementing OAuth 2.1 for MCP in this IWO. Copying MCP server binaries into Git.
- Assumptions: IWO-067 registry and IWO-079 intake stay the inventory.
- Open decisions: What “cryptographically verified” means for a local stdio command the operator installed. A pinned digest of the launch command’s target is enough if the operator records it. Do not invent a digest.

## What To Build / Fix

- Refuse `tools/call` for a server that is not allow-listed.
- Reject oversized or undeclared parameters in a unit test.
- Validate a fixture tool result against its schema and reject a mismatch.
- Mark tool result text so the agent loop treats it as untrusted data.
- Update the C10 rows this IWO changes. Leave 10.2.3 and 10.3.1 not applicable.

## Expected Change Surface

- Expected: MCP client and registry, tests, gap register
- Tests: unit tests with fake stdio frames. No live third-party server.
- Docs/status: gap register, `docs/architecture/mcp-servers.md` if the rule changes, this Closeout

## Out Of Scope

- Remote HTTP MCP and OAuth token storage (10.2.3, 10.3.1, and Level 2 C10 rows).
- DefenseClaw configuration on the Air.
- Host deploy.

## Do NOT Change

- Do not copy AISVS prose into Git.
- Do not vendor a third-party MCP server.
- Do not mark an empty allowlist as authorizing calls.
- No secrets in Git. No host mutation.

## Acceptance Criteria

1. A unit test refuses a call to a server that is not allow-listed.
2. A unit test rejects an oversized parameter and a schema-invalid tool result.
3. The C10 register rows match the code, and the two not-applicable rows stay not applicable.
4. `./scripts/validate-repo.sh` passes.

## Validation Plan

- Automated: unit tests and `./scripts/validate-repo.sh`
- Manual: confirm no digest was invented
- Evidence to include: test names

## AI Lab gates (required)

- **Creates runtime job on mac-mini?** No
- **Host deploy / mutate authorized by this IWO alone?** **No**
- **Privileged tools expected?** none
- **May run on Air?** Yes — unit tests only. Do not change the live Cursor MCP entry from this IWO.

## Execution

- **Branch:** `iwo/092-aisvs-mcp-checks`
- **Risk tier:** P2
- **Pre-PR / pre-merge gate:** `./scripts/validate-repo.sh`
- **Depends on:** IWO-085, IWO-067, IWO-079
- **Human verification required:** Yes
- **Reviewer / approver:** human operator
- **Project status record:** `docs/features/index.md`
- **Other status surfaces:** `docs/security/aisvs-level-1.md`

## Closeout

- Verification evidence:
- Follow-ons filed:
- Residual risks:
- Docs/status updated:
- Status surfaces reconciled:
- Summary metadata reviewed:
- Planning-only change? No, once accepted and implemented
- Host deploy performed? No
