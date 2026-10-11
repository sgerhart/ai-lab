# IWO-083 — Shared fetched pages, PDF text, and complete chat answers

**Status:** Complete (unit; control plane restarted)
**Priority:** P2
**Effort:** M
**Owner:** human (operator)
**Feature:** [FEAT-008](../features/FEAT-008-research-retrieval-memory.md)
**Services / Areas:** platform (chat, retrieval, attachments)
**Risk tier:** P2

## Problem

A page fetched in one chat is kept only when that chat belongs to a project,
so the next chat starts over. Attached PDFs and images are stubs. Ordinary
chat cannot read lab port status or list project files unless the operator
starts an agent run. General Local is still told to reply briefly, which cuts
off a sourced answer.

## Decision Context

- Chosen approach: store every successful fetch under a reserved library id
  (`lab-sources`) that any later chat can match by shared words. A user
  project's own files stay on that project. PDF text is taken from page
  streams, including deflated streams, with a size cap and no new package.
  A lab-status question reads the existing port check and does not search
  the web. A "what files" question lists that project's filenames only.
  Sourced answers, and models other than Fast Local, are told to answer
  completely.
- Alternatives rejected: searching every project document from every chat;
  enabling `http_get_allowlist` so the model picks URLs; claiming the local
  model can see images.
- Assumptions: Fast Local remains `llama3.2:3b`. Image files stay unread.
- Open decisions: a real embedding model, and vision for images, stay later.

## What To Build / Fix

- Fetched pages are stored in the shared library and also on the chat's
  project when it has one.
- A later factual question includes matching library pages in the source text.
- PDF attachments and project PDFs contribute extracted text.
- Lab health and a project file list are added as sources when the question
  asks for them.
- The chat system line drops "reply briefly" when the turn has sources or
  the selected model is not Fast Local.

## Expected Change Surface

- Expected: later chats, PDF attachments, lab-status questions, General Local replies.
- Tests: `tests/test_grounded_chat.py`, `tests/test_project_documents.py`
- Docs/status: this file, `docs/features/index.md`, FEAT-008, work-order index.

## Out Of Scope

Image understanding. A new embedding model. Model-chosen URLs. Deploy of
compose on the Air.

## Do NOT Change

No secrets in Git. Project search stays inside that project. Empty retrieval
still returns no invented citations. Greetings are not searched.

## Acceptance Criteria

1. A page fetched with no project is available to a later question, and a
   private project file is not included.
2. A guessed figure that is not in that saved page is removed.
3. A lab-health question includes the port read and does not call web search.
4. A project file question lists that project's names only.
5. PDF text is extracted from a plain stream and a deflated stream. An image
   still says vision is not enabled.
6. General Local, and any sourced reply, is not instructed to be brief.
7. `python3 -m unittest tests.test_grounded_chat tests.test_project_documents -v` passes.

## Validation Plan

- Automated: the command in criterion 7.
- Manual: on Studio, ask a fact, then ask it again in a new chat; attach a
  text PDF; ask whether the lab is up on General Local.
- Evidence to include: unit output.

## AI Lab gates (required)

- **Creates runtime job on mac-mini?** No
- **Host deploy / mutate authorized by this IWO alone?** **No**
- **Privileged tools expected?** none
- **May run on Air?** Yes for unit tests. No lab compose on the Air.

## Execution

- **Branch:** current working tree
- **Risk tier:** P2
- **Pre-PR / pre-merge gate:** `python3 -m unittest tests.test_grounded_chat tests.test_project_documents -v`
- **Depends on:** IWO-082, IWO-060
- **Human verification required:** Yes before calling the live chat done
- **Reviewer / approver:** operator
- **Project status record:** `docs/features/index.md` and this file

## Closeout

- Verification evidence: `python3 -m unittest tests.test_grounded_chat tests.test_project_documents -v` — 25 tests, ok.
- Follow-ons filed: [IWO-084](IWO-084-embeddings-and-images.md).
- Residual risks: the shared library matches on shared words, so a weak overlap can attach an old page. Qdrant lists at most 100 library pages. PDF text is the strings in the file, not a full layout parse. Images stay unread.
- Docs/status updated: this file, feature index, FEAT-008, work-order index.
- Status surfaces reconciled: feature index row added.
- Summary metadata reviewed: yes.
- Planning-only change? No
- Host deploy performed? Yes — the four chat modules were copied to the mini and the existing control-plane agent was restarted. No data wipe. Health returned ok.
