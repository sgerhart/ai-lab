# IWO-087 — AISVS model inventory, admission, and AI BOM

**Status:** Draft  
**Priority:** P2  
**Effort:** M  
**Owner:** human (operator)  
**Feature:** [FEAT-018](../features/FEAT-018-ai-security-platform.md)  
**Services / Areas:** platform, docs, models

## Problem

The lab can name Ollama tags and refuse an unattended pull. It cannot show, for each tag in use, an origin record, a passed safety check, a scan-before-import result, or a machine-readable AI bill of materials. Those are AISVS 1.0 Level 1 identifiers 3.1.1, 3.2.1, 6.1.1, 6.1.2, and 6.2.1 in [the gap register](../security/aisvs-level-1.md).

Requirement 3.4.1 stays partial on purpose. This lab has one environment on three hosts. This IWO does not create a second environment.

## Decision Context

- Chosen approach: An admission record in Git for each catalogued tag: origin, digest if the operator has one, scan result, and a short AI BOM written by the lab. Pulls stay operator-authorized. WO-006 still refuses unattended pulls.
- Alternatives rejected: Scanning weights inside this IWO. Pulling models. Claiming upstream alignment as a lab test.
- Assumptions: Digests and scan output are supplied by the operator or by a later authorized command. This draft does not run that command.
- Open decisions: Which scanner is allowed to look at a model file. Where the BOM file lives under `docs/models/` or `platform/`.

## What To Build / Fix

- A versioned admission file per catalogued tag with origin and the checks this IWO actually ran.
- A machine-readable BOM that lists the tag, the base artifact, and the lab config that selects it. Datasets are omitted when the lab did not train the model, and the file says so.
- Tests that refuse a tag with no admission row when the router is asked to select it.
- Register updates for 3.1.1, 3.2.1, 6.1.1, 6.1.2, and 6.2.1.

## Expected Change Surface

- Expected: `docs/models/`, model router or catalog loader, tests, gap register
- Tests: unit tests with a fake catalog. No `ollama pull`.
- Docs/status: gap register, FEAT-018, this Closeout

## Out Of Scope

- Cryptographic signature verification at load (AISVS 3.1.2 and 3.1.3 are Level 2).
- Host deploy, model pulls, or a malware scan of a live Studio blob.
- Splitting development and production (3.4.1).

## Do NOT Change

- Do not copy AISVS prose into Git.
- Do not mark `catalogued-not-pulled` tags as pulled.
- No secrets, weights, or scan dumps with file contents in Git.
- No host mutation.

## Acceptance Criteria

1. Every tag the router can select has an admission row, or the router refuses it in a unit test.
2. The BOM is machine-readable and states that the lab did not train the model.
3. The five register rows match the files.
4. `./scripts/validate-repo.sh` passes. No model pull was run.

## Validation Plan

- Automated: unit tests and `./scripts/validate-repo.sh`
- Manual: confirm the BOM lists only tags already named in `docs/models/serving.md`
- Evidence to include: the test output and the BOM path

## AI Lab gates (required)

- **Creates runtime job on mac-mini?** No
- **Host deploy / mutate authorized by this IWO alone?** **No**
- **Privileged tools expected?** none
- **May run on Air?** Yes — docs and unit tests only

## Execution

- **Branch:** `iwo/087-aisvs-model-admission`
- **Risk tier:** P2
- **Pre-PR / pre-merge gate:** `./scripts/validate-repo.sh`
- **Depends on:** IWO-085, IWO-055, ADR 0044
- **Human verification required:** Yes
- **Reviewer / approver:** human operator
- **Project status record:** `docs/features/index.md`
- **Other status surfaces:** `docs/security/aisvs-level-1.md`, `docs/models/serving.md`

## Closeout

- Verification evidence:
- Follow-ons filed:
- Residual risks:
- Docs/status updated:
- Status surfaces reconciled:
- Summary metadata reviewed:
- Planning-only change? No, once accepted and implemented
- Host deploy performed? No
