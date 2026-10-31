# IWO-118 — Coding Training Dataset and Task Contracts

**Status:** Complete (WO-02 Delivered)  
**Priority:** P2  
**Effort:** M  
**Owner:** Steven Gerhart  
**Feature:** FEAT-024  
**Services / Areas:** `coding-training/packages/datasets/`, `coding-training/datasets/`, tests

## Problem

Training coding models with execution-verified reinforcement learning requires high-quality, strictly partitioned, and content-addressed task definitions. Using ambiguous, contaminated, or leaking benchmarks causes models to memorize specific unit tests rather than learning generalizable programming semantics. WO-02 requires curating 100+ reviewed Python tasks, content-addressed immutable test bundles, family-disjoint train/val/test splits, 100% verified reference solutions, and automated prompt leakage detection.

## Decision Context

- Curated task taxonomy spanning 10 algorithmic families.
- Immutable test bundles referenced exclusively by SHA-256 digest (`datasets/test_bundles/{sha256}.json`).
- Strict stratification by `family_id` to prevent cross-split leakage between train, val, and test.
- Every task includes 20 comprehensive test cases (boundary, empty, single-element, and scale).
- Zero prompt leakage: hidden test expectations must never appear in task prompts.

## What To Build / Fix

1. Implement `packages/datasets/task_generator.py`: Define raw task blueprints across 10 algorithmic families with 20 test cases each.
2. Implement `packages/datasets/catalog_builder.py`: Assemble 105 curated tasks with function signatures, docstrings, and verified reference implementations.
3. Implement `packages/datasets/packager.py`: Package tasks, write content-addressed test bundles, standalone reference solutions, and cryptographically signed dataset manifests.
4. Implement `packages/datasets/validator.py`: Automated validation engine verifying family disjointness, bundle SHA-256 integrity, reference solution pass rate, and prompt leakage.
5. Implement `packages/datasets/task_loader.py`: Efficient disk loader for dataset manifests, test bundles, and reference solutions.
6. Implement `scripts/compile_datasets.py`: Deterministic dataset compilation CLI.
7. Implement unit test suite `tests/unit/test_datasets.py` covering loader, disjointness, bundle integrity, corruption resistance, and validation reporting.
8. Document Gate WO-02 closeout record in `coding-training/docs/gates/WO-02.md`.

## Expected Change Surface

- Expected: `coding-training/packages/datasets/`, `coding-training/datasets/`, `coding-training/scripts/`, `coding-training/tests/unit/test_datasets.py`, `coding-training/docs/gates/WO-02.md`, `docs/work-orders/IWO-118-coding-training-datasets-and-tasks.md`.
- Tests: `cd coding-training && make check`, `python3 scripts/compile_datasets.py`.
- Docs/status: `docs/features/index.md`, `docs/features/FEAT-024-execution-verified-coding-model-training.md`.

## Out Of Scope

- Live model fine-tuning (deferred to WO-04/05).
- Linux sandbox container provisioning (deferred to WO-03).
- Remote repository web scraping or external dataset imports without provenance review.

## Do NOT Change

- Do not modify existing AI Lab core services (`platform/`, `infrastructure/`).
- Do not run untrusted code on macOS.
- Do not add unverified task definitions without 100% passing reference solutions.

## Closeout & Evidence

- Files created:
  - `coding-training/packages/datasets/task_generator.py`
  - `coding-training/packages/datasets/catalog_builder.py`
  - `coding-training/packages/datasets/packager.py`
  - `coding-training/packages/datasets/validator.py`
  - `coding-training/packages/datasets/task_loader.py`
  - `coding-training/scripts/compile_datasets.py`
  - `coding-training/tests/unit/test_datasets.py`
  - `coding-training/datasets/manifests/dataset_v1.json` (105 tasks)
  - `coding-training/datasets/test_bundles/` (105 SHA-256 test bundles, 2,100 test cases)
  - `coding-training/datasets/reference_solutions/` (105 verified reference solutions)
  - `coding-training/docs/gates/WO-02.md`
- Verification commands run:
  - `cd coding-training && python3 scripts/compile_datasets.py` (PASS, 0 leaks, 0 errors)
  - `cd coding-training && make check` (24 passing unit tests, 0 lint errors)
