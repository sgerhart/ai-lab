# IWO-082 — Grounded chat: dated fetch and product-ID check

**Status:** Complete (unit; not deployed)
**Priority:** P2
**Effort:** M
**Owner:** human (operator)
**Feature:** [FEAT-008](../features/FEAT-008-research-retrieval-memory.md)
**Services / Areas:** platform (chat, retrieval)
**Risk tier:** P2

## Problem

Ordinary chat answers from the local model. A question such as which Cisco
switches ACI supports comes back with a mix of real, wrong, and invented
product IDs, and with no date. Project documents are used only when a file is
already stored. `http_get_allowlist` stays disabled.

## Decision Context

- Chosen approach: on a chat turn, fetch at most two https URLs. A URL in the
  question is fetched when its host is on `data/fetch_allowlist.json`. A
  pinned catalog page is fetched when the question contains that entry's
  words. Any other factual question is looked up on Wikipedia and DuckDuckGo;
  the result pages are fetched when the address is public. The model does not
  choose those URLs. The page's own date and the fetch time are written on
  the reply. Product IDs, years, and measurements that do not appear in the
  page or in matching project documents are removed. If nothing was retrieved
  and the reply names one of those, the reply is labeled unverified and has
  no document date. A page stored on a project is kept for the next question
  in that project.
- Alternatives rejected: letting the model choose any URL; a prompt that only
  says not to hallucinate; searching greetings and other short chat.
- Assumptions: the pinned ACI page is the Nexus 9000 ACI-Mode release notes
  for 16.2(3). That page lists both supported and no-longer-supported
  hardware. The interactive hardware matrix is a script and is not fetched.
- Open decisions: more catalog rows, and a real embedding model, stay later.

## What To Build / Fix

- `source_fetch.py` — https only, exact host, public addresses, redirect
  re-checked, size and time caps.
- `chat_grounding.py` — excerpt, product-ID check, dated footer.
- Chat `POST` and SSE use that path. The stream replaces the bubble with the
  checked text so a removed name is not what gets stored.
- `data/fetch_allowlist.json`, `data/source_catalog.json`.

## Expected Change Surface

- Expected: chat replies that name product IDs.
- Tests: `tests/test_grounded_chat.py`
- Docs/status: this file, `docs/features/index.md`, FEAT-008, work-order index.

## Out Of Scope

Open web search. Enabling `http_get_allowlist` for model-chosen URLs. A new
embedding model. PDF extraction. Deploy or restart of the mini control plane.

## Do NOT Change

No secrets in Git. No bind-address change. No host mutate. Citation policy
for empty retrieval stays empty. Casual replies that name no product ID stay
as the model wrote them.

## Acceptance Criteria

1. An ACI switch question fetches the pinned Cisco release-notes URL and the
   reply carries that page's document date and the fetch time.
2. A product ID that is not in the fetched text is removed and listed.
3. A product ID with no fetched page and no project document is labeled
   unverified and is not given a document date.
4. http, credentials in the URL, IP hosts, off-allowlist hosts, and
   non-public addresses are not requested.
5. `python3 -m unittest tests.test_grounded_chat -v` passes.

## Validation Plan

- Automated: `python3 -m unittest tests.test_grounded_chat -v`
- Manual: after a separately authorized restart of the mini control plane,
  ask which ACI switches are supported and confirm the footer date and that
  invented model numbers are gone.
- Evidence to include: unit output. Live mini was not restarted.

## AI Lab gates (required)

- **Creates runtime job on mac-mini?** No
- **Host deploy / mutate authorized by this IWO alone?** **No**
- **Privileged tools expected?** none
- **May run on Air?** Yes for unit tests. No lab compose on the Air.

## Execution

- **Branch:** current working tree
- **Risk tier:** P2
- **Pre-PR / pre-merge gate:** `python3 -m unittest tests.test_grounded_chat -v`
- **Depends on:** IWO-040, IWO-060
- **Human verification required:** Yes before calling the live chat done
- **Reviewer / approver:** operator
- **Project status record:** `docs/features/index.md` and this file

## Closeout

- Verification evidence: `python3 -m unittest tests.test_grounded_chat tests.test_conversation_contract tests.test_project_documents -v` — 20 tests, ok. Live Studio was not restarted.
- Follow-ons filed: [IWO-083](IWO-083-chat-library-and-reads.md). Further catalog rows stay out of this slice.
- Residual risks: the pinned page is one ACI release, and it also lists hardware that is no longer supported. Those names stay if the model repeats them; the footer says they appeared in that section. A name can still be mis-labeled if the heading heuristic misses the section. Hash embeddings are unchanged.
- Docs/status updated: this file, feature index, FEAT-008, work-order index.
- Status surfaces reconciled: feature index row added.
- Summary metadata reviewed: yes.
- Planning-only change? No
- Host deploy performed? No
