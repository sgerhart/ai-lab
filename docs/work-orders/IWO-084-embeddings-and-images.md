# IWO-084 — Page embeddings and image chat

**Status:** Complete (unit; control plane restarted)
**Priority:** P2
**Effort:** M
**Owner:** human (operator)
**Feature:** [FEAT-008](../features/FEAT-008-research-retrieval-memory.md)
**Services / Areas:** platform (chat, retrieval, attachments)
**Risk tier:** P2

## Problem

A saved page is found only when the next question shares two words with it.
An attached image is stored and described as unread, even though Qwen 3.6 and
Qwen 3.8 on the Studio list vision.

## Decision Context

- Chosen approach: rank saved pages with a small local English embedding
  (`BAAI/bge-small-en-v1.5` via fastembed) when that package is installed.
  The Qdrant collection stays on the 64-dimension hash so existing points
  are left in place. Word overlap remains the fallback. An image on the
  latest user message is sent to Ollama when that tag's capabilities include
  vision. A model without vision keeps the unread note. An image turn does
  not search the web and does not strip names the picture supplied.
- Alternatives rejected: a second Ollama model for embeddings, because the
  Studio keeps one chat model loaded; changing the Qdrant vector size.
- Assumptions: Qwen 3.6 and Qwen 3.8 are the vision tags already installed.
  Fast Local (`llama3.2:3b`) is not.
- Open decisions: none in this slice.

## What To Build / Fix

- `embeddings.py` and retrieval ranking for the shared library and for a
  project's own files.
- Ollama generate and stream accept up to four images.
- Chat sends images only after `/api/show` reports vision.

## Expected Change Surface

- Expected: a later question with different words, and an attached image.
- Tests: `tests/test_grounded_chat.py`, `tests/test_repo_finish.py`
- Docs/status: this file, feature index, FEAT-008, work-order index.

## Out Of Scope

A new Qdrant collection. Pulling another Ollama tag. Image generation.

## Do NOT Change

No secrets in Git. No weights in Git. Project files stay inside that project.
Empty retrieval still invents no citations.

## Acceptance Criteria

1. A saved coastline page is returned for a shoreline question, and a private
   project file is not.
2. A switch question does not return that coastline page.
3. An image turn does not call web search, and a model number in the reply
   stays in the answer.
4. Ollama is sent the image bytes only when the request includes them.
5. `python3 -m unittest tests.test_grounded_chat tests.test_repo_finish tests.test_project_documents tests.test_retrieval -q` passes.

## Validation Plan

- Automated: the command in criterion 5.
- Manual: ask a fetched fact again in new words, and attach a PNG on Qwen 3.6
  or Qwen 3.8.
- Evidence to include: unit output, and a live cosine check of the shoreline
  paraphrase against the coastline sentence.

## AI Lab gates (required)

- **Creates runtime job on mac-mini?** No
- **Host deploy / mutate authorized by this IWO alone?** **No**
- **Privileged tools expected?** none
- **May run on Air?** Yes for unit tests. No lab compose on the Air.

## Execution

- **Branch:** current working tree
- **Risk tier:** P2
- **Pre-PR / pre-merge gate:** the unittest command above
- **Depends on:** IWO-083, IWO-040
- **Human verification required:** Yes before calling image chat done
- **Reviewer / approver:** operator
- **Project status record:** `docs/features/index.md` and this file

## Closeout

- Verification evidence: 41 tests, ok. Live embedder name `bge-small-en-v1.5`. Shoreline versus coastline score 0.599; shoreline versus a switch sentence 0.337. Threshold is 0.45.
- Follow-ons filed: none.
- Residual risks: the embedding is English and small, so a vague question can still miss. Pages are embedded from their saved text at question time until a vector is stored. Fast Local does not see images.
- Docs/status updated: this file, feature index, FEAT-008, work-order index, IWO-083 follow-on.
- Status surfaces reconciled: feature index row added.
- Summary metadata reviewed: yes.
- Planning-only change? No
- Host deploy performed? Yes — chat modules copied to the mini, fastembed installed in the control-plane venv, embedding weights cached on first use, control plane restarted. No data wipe. Health returned ok.
