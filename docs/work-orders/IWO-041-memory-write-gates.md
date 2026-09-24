# IWO-041 — Agent memory_write gates (FEAT-008)

**Status:** Complete  
**Priority:** P2  
**Effort:** S  
**Owner:** human (operator)  
**Feature:** [FEAT-008](../features/FEAT-008-research-retrieval-memory.md)  
**Risk tier:** P2  
**GitHub:** [#9](https://github.com/sgerhart/ai-lab/issues/9)

## Problem

IWO-040 lets operators upsert memory via HTTP and agents *search* it.
Agents cannot write memory yet; writes must stay audited and source-cited.

## What To Build / Fix

- Tool `memory_write` (privileged — needs approval in the agent loop)
- Requires `text` + `source`; calls RetrievalService.upsert
- Allow on `research` privileged_tools; keep lab-operations read-only
- Unit tests: deny without approval; approve then upsert

## Out Of Scope

- Automatic ingestion pipelines
- Changing Qdrant compose

## Acceptance Criteria

1. Unapproved `memory_write` awaits approval / denied.
2. Approved write appears in subsequent `memory_search`.
3. Missing `source` fails closed.

## Closeout

- Verification evidence: `python3 -m unittest tests.test_retrieval -v`
- Host deploy performed? No
