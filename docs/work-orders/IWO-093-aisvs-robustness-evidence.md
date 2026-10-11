# IWO-093 — AISVS robustness evidence for catalogued models

**Status:** Draft  
**Priority:** P2  
**Effort:** M  
**Owner:** human (operator)  
**Feature:** [FEAT-018](../features/FEAT-018-ai-security-platform.md)  
**Services / Areas:** docs, platform

## Problem

The lab serves published instruction-tuned tags and has not recorded alignment evidence, an adversarial check, a block on inferred sensitive attributes, an inference rate limit, or an extraction-pattern detector. AISVS Level 1 rows 11.1.1, 11.1.2, 11.1.3, 11.2.1, 11.2.2, and 11.3.1 in [the gap register](../security/aisvs-level-1.md). Antares and Vise do not satisfy these rows.

## Decision Context

- Chosen approach: A versioned evidence note per catalogued tag, plus lab-side controls that do not retrain the model: a fixed output filter fixture, a per-caller request cap in the API, and a counter for repeated identical prompts. The evidence note quotes the lab’s observation. It does not paste vendor model cards.
- Alternatives rejected: Fine-tuning on the Studio. Treating the IWO-057 accuracy fixture as an alignment suite. Running extraction attacks as the test.
- Assumptions: Tags stay those already named in `docs/models/serving.md`.
- Open decisions: The numeric rate limit. The shape of the repeated-prompt counter.

## What To Build / Fix

- An evidence file that lists each catalogued tag and what the lab has actually checked. Unknown checks stay unknown.
- A unit test for a response filter fixture aimed at a sensitive-attribute pattern the test defines.
- A per-caller cap on chat requests in the API, tested without a live model.
- A repeated-prompt counter that records a threshold crossing. It does not need to identify a real attacker.
- Update the six C11 rows. Do not mark a row met because a vendor’s training is assumed.

## Expected Change Surface

- Expected: `docs/models/`, API rate-limit helper, tests, gap register
- Tests: unit tests. No Studio call and no attack corpus.
- Docs/status: gap register and this Closeout

## Out Of Scope

- Training, quantization re-eval, watermarking, and differential privacy.
- Hostile samples. Those stay on the Security Compute Plane and are not run here.
- Host deploy and model pulls.

## Do NOT Change

- Do not copy AISVS prose or a vendor model card into Git.
- Do not add exploit prompts, payloads, or attack procedures to the repo.
- No secrets in Git. No host mutation.

## Acceptance Criteria

1. The evidence file exists for each catalogued tag and does not claim an unchecked property.
2. Unit tests cover the output fixture, the request cap, and the repeated-prompt counter.
3. The six register rows match those tests and say when a property is still unknown.
4. `./scripts/validate-repo.sh` passes.

## Validation Plan

- Automated: unit tests and `./scripts/validate-repo.sh`
- Manual: read the evidence file for overclaim
- Evidence to include: the file path and test names

## AI Lab gates (required)

- **Creates runtime job on mac-mini?** No
- **Host deploy / mutate authorized by this IWO alone?** **No**
- **Privileged tools expected?** none
- **May run on Air?** Yes — docs and unit tests only

## Execution

- **Branch:** `iwo/093-aisvs-robustness-evidence`
- **Risk tier:** P2
- **Pre-PR / pre-merge gate:** `./scripts/validate-repo.sh`
- **Depends on:** IWO-085, IWO-055
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
