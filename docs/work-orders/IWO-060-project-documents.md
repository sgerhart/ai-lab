# IWO-060 — Project document library

**Status:** In progress (unit tests; live Qdrant pass not recorded)  
**Priority:** P2  
**Feature:** [FEAT-008](../features/FEAT-008-research-retrieval-memory.md)

## What this slice does

A project keeps its own documents. `POST /v1/projects/{id}/documents` accepts the same file types as chat attachments. Markdown and text are indexed. PDF and images are stored as an honest note that their contents are not read yet.

Search with a `project_id` returns only that project's documents. A chat linked to the project receives the matching sources with the question. A chat with no project does not. Studio chat search stays global, with the project menu as a narrower view of chats.

## Not in this slice

A new embedding model, PDF text extraction, vision, or a separate RAG page in the sidebar.

## Acceptance

- [x] Two projects do not share search hits
- [x] Delete is refused for a document that belongs to another project
- [ ] Operator adds a markdown file on the live mini and a chat in that project cites it
