# IWO-126 — Steward Nexus Study Deep Grounding

**Status:** Complete  
**Priority:** P2  
**Effort:** S  
**Owner:** operator  
**Feature:** FEAT-022, FEAT-010  
**Services / Areas:** platform, docs

## Problem

Steward's standing goals and personal agent loop have access to `nexus_search` as an authorized **See** tool. However, `_nexus_search` in `tool_runtime.py` currently only calls `books_for_query`, which returns library catalog titles or short summaries. When a book is found without pre-cached summaries, it returns `"Passage: The title matches what you asked."`, leaving Steward without actual chapter text or technical excerpts.

Conversely, `nexus_study.py` possesses a deep extraction engine (`extract_book_context`, `_search_epub`, `_search_pdf`, and `_extract_table_of_contents`) capable of pulling precise paragraphs, chapter text, and Table of Contents outlines from the 149+ technical books in `~/.ai-lab/nexus/`. This engine is currently only invoked by the browser-based Study Copilot in `control_app.py`, leaving background wakes and conversational Steward interactions unable to deeply read the shelf.

## Decision Context

- **Chosen approach:**
  - Wire `extract_book_context` from `nexus_study.py` directly into `_nexus_search` in `tool_runtime.py`.
  - Support enhanced arguments on `nexus_search`: `query` (required), optional `book` (filter to a specific book title or relative path), optional `chapter` (specific chapter number or topic), and optional `toc` (boolean to extract the Table of Contents / parts outline).
  - When a query matches candidate books via `suggest_books`, automatically extract and append deep chapter excerpts for the top hit(s), grounding Steward in real book content.
  - Add a "Nexus Technical Study Sentinel" template to Steward Desk in `steward.js` for 1-click standing reading watches.
- **Access and Invariants Preserved:**
  - The tool name remains `nexus_search` under the **See** ceiling (`FEAT-022`).
  - Read-only execution with zero writes and zero network egress.
  - Fails gracefully if books are missing or unreadable.

## What To Build / Fix

1. **`platform/src/ai_lab_platform/tool_runtime.py`**:
   - Enhance `_nexus_search` to support `book`, `chapter`, and `toc` arguments.
   - For general queries, resolve top matching books and append deep excerpts from `extract_book_context`.
   - For book-specific or TOC queries, invoke `extract_book_context` directly.
2. **`platform/src/ai_lab_platform/web/static/steward.js`**:
   - Add a `study` preset to `TEMPLATES` on the Steward Desk ("Nexus Technical Study Sentinel").
3. **Tests**:
   - Add unit tests in `tests/test_nexus_study_grounding.py` verifying:
     - General topic queries returning deep excerpts.
     - Book-specific queries with chapter targeting.
     - Table of Contents extraction via `nexus_search`.
     - Short query rejection (`len(query) < 3`).
     - Preservation of `See` classification in `steward.py`.

## Expected Change Surface

- Expected: `platform/src/ai_lab_platform/tool_runtime.py`, `platform/src/ai_lab_platform/web/static/steward.js`, `tests/test_nexus_study_grounding.py`.
- Tests: `python3 -m unittest tests.test_nexus_study_grounding -v`, `python3 -m unittest tests.test_steward -v`.
- Docs/status: `docs/features/index.md`, `docs/work-orders/README.md`.

## Out Of Scope

- Modifying model weights or running GPU inference.
- Adding write or mutative tools to the See class.
- Live deployment to `mac-mini` (requires explicit operator deploy authorization).

## Do NOT Change

- Do not alter the See / Draft / Approval classification in `steward.py`.
- Do not remove the query length validation (`len(query) < 3` raises `ToolError`).
- Do not expose file paths outside `~/.ai-lab/nexus/`.

## Acceptance Criteria

1. `nexus_search` returns direct chapter excerpts from matching EPUB/PDF volumes.
2. `nexus_search` with `book` or `toc=True` extracts the book's parts/chapters breakdown.
3. Steward access manifest preserves `nexus_search` in the **See** class.
4. All unit tests pass cleanly and `./scripts/validate-repo.sh` reports `RESULT: OK`.

## Validation Plan

- Automated: `python3 -m unittest discover -s tests -v` and `./scripts/validate-repo.sh`.
- Evidence: Unit test output proving deep context extraction.

## AI Lab gates (required)

- **Creates runtime job on mac-mini?** No
- **Host deploy / mutate authorized by this IWO alone?** **No**
- **Privileged tools expected?** none
- **May run on Air?** Yes for unit tests.
