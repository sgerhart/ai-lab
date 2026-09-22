# IWO-002 — Agent-run and conversation contract on the mini

**Status:** Ready  
**Priority:** P1  
**Effort:** M  
**Owner:** operator  
**Feature:** [FEAT-010](../features/FEAT-010-mini-personal-agent-loop.md)  
**Services / Areas:** platform, docs  
**Risk tier:** P2 (code + schema; FakeBackend only; no host mutate)

## Problem

The mini has runtime work orders and deterministic `agent_plans.py`, but no
first-class **conversation** and **agent-run** contract for personal-agent
chat/loops. Without it, FEAT-004 UI and FEAT-010 model loops have nowhere
durable to land. Fixed plans must not be mistaken for a model-driven loop.

## Decision Context

- **Chosen approach:** Add Postgres-backed conversation + agent-run records on
  the mini, linked optionally to a runtime work order UUID; drive unit tests
  with FakeBackend only.
- **Alternatives rejected:** Force every chat turn into today’s work-order row
  shape; wait for Studio before any schema.
- **Assumptions:** Existing `WorkOrder` / `Status` enum stays; extend rather than
  replace (lifecycle mapping ADR 0036).
- **Open decisions:** Exact table names—implementer chooses consistent with
  `schema.sql`.

## What To Build / Fix

- Schema + store methods for conversations, messages, agent runs (status,
  budgets, model class, traces placeholder)
- FastAPI endpoints: create conversation, post message (persisted), get run
- Clear API docs: chat turn vs durable background run
- Unit tests with FakeBackend; no live cloud; no Studio

## Expected Change Surface

- Expected: `platform/src/ai_lab_platform/` schema, store, control_app, tests
- Tests: unittest for create/list/get; denial when unauthenticated if auth
  stub exists (auth may be IWO-003—if so, test store layer in isolation)
- Docs/status: FEAT-010 status note; PLAN-mini-first

## Out Of Scope

- HTML UI (IWO-003); real model loop (IWO-005); cloud providers; host deploy;
  privileged new tools

## Do NOT Change

- Bind policy; secrets in Git; runtime `Status` rename; Clarion paths;
  historical `WO-000`–`007`

## Acceptance Criteria

1. Conversation + agent-run round-trip in Postgres (or SQLite test store).
2. Documented distinction: ordinary message vs durable run.
3. `./scripts/validate-repo.sh` + focused platform tests pass.
4. No `--apply`, compose up, model pull, or paid API calls.

## Validation Plan

- Automated: platform unit tests; validate-repo
- Manual: none required beyond reading OpenAPI/docstring
- Evidence: test output in Closeout

## AI Lab gates (required)

- **Creates runtime job on mac-mini?** No (schema/API only in this IWO; live
  migrate needs separate deploy auth if applied to mini)
- **Host deploy / mutate authorized by this IWO alone?** No
- **Privileged tools expected?** none
- **May run on Air?** Yes (dev/test)

## Execution

- **Branch:** `iwo/002-agent-run-conversation`
- **Risk tier:** P2
- **Pre-merge gate:** `./scripts/validate-repo.sh` + platform tests
- **Depends on:** IWO-001 (protocol), FEAT-010 spec
- **Human verification required:** Yes (review)
- **Reviewer / approver:** operator
- **Project status record:** this file + FEAT-010
- **Other status surfaces:** GitHub FEAT-010 issue

## Closeout

- Verification evidence: (pending implementation)
- Follow-ons filed: IWO-003
- Residual risks: live mini schema migrate needs deploy auth
- Host deploy performed? No
