# IWO-088 — AISVS model load isolation contract

**Status:** Draft  
**Priority:** P2  
**Effort:** S  
**Owner:** human (operator)  
**Feature:** [FEAT-018](../features/FEAT-018-ai-security-platform.md)  
**Services / Areas:** docs

## Problem

AISVS 4.1.1 is partial: agents have isolation tiers, and Studio Ollama is a host process. AISVS 4.1.2 is a gap: nothing in Git allow-lists the serialization formats Ollama may load. Both are recorded in [the gap register](../security/aisvs-level-1.md). Requirement 4.3.1 stays not applicable. There is no edge inference device.

## Decision Context

- Chosen approach: Write the contract the loader must meet, and a test double that rejects a format outside the allow-list. Do not change the Studio host, Ollama’s bind, or install a sandbox in this IWO.
- Alternatives rejected: Moving Ollama into a new container or VM as part of this draft. Treating ADR 0017 agent tiers as a per-model sandbox.
- Assumptions: Ollama remains the inference server (ADR 0019) until a later accepted ADR says otherwise.
- Open decisions: Whether a later IWO is allowed to change how Ollama is supervised. That later IWO is P1 and needs its own deploy authorization.

## What To Build / Fix

- Document the formats the lab is willing to load, in lab words, with GGUF called out if that is the operator’s choice.
- A pure function that accepts only those format names, with unit tests.
- Point 4.1.1 at ADR 0017 and state plainly that the host Ollama process is still the runtime.
- Update register rows 4.1.1 and 4.1.2. Leave 4.3.1 not applicable.

## Expected Change Surface

- Expected: `docs/models/` or `docs/security/`, a small platform helper, tests, the gap register
- Tests: unit tests for the format allow-list. No live load.
- Docs/status: gap register and this Closeout

## Out Of Scope

- Installing a sandbox, changing launchd, or changing Ollama’s listen address.
- GPU attestation and the rest of C4 Level 2 and Level 3.
- Hostile-workload isolation. That stays FEAT-019.

## Do NOT Change

- Do not copy AISVS prose into Git.
- Do not bind a new listener.
- No host mutation and no model pull.

## Acceptance Criteria

1. The allow-list rejects an unknown format name in a unit test.
2. The register says whether 4.1.2 is met by that function, and still says 4.1.1 is partial while Ollama is a host process.
3. `./scripts/validate-repo.sh` passes.

## Validation Plan

- Automated: unit test and `./scripts/validate-repo.sh`
- Manual: read the contract and confirm it does not instruct a host change
- Evidence to include: test name and the two register rows

## AI Lab gates (required)

- **Creates runtime job on mac-mini?** No
- **Host deploy / mutate authorized by this IWO alone?** **No**
- **Privileged tools expected?** none
- **May run on Air?** Yes — docs and unit tests only

## Execution

- **Branch:** `iwo/088-aisvs-model-load-isolation`
- **Risk tier:** P2
- **Pre-PR / pre-merge gate:** `./scripts/validate-repo.sh`
- **Depends on:** IWO-085, ADR 0017, ADR 0019
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
- Planning-only change? The host runtime stays unchanged. The allow-list function is code once this IWO is accepted.
- Host deploy performed? No
