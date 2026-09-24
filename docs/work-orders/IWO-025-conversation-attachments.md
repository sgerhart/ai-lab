# IWO-025 — Conversation attachments (docs / images)

**Status:** Complete  
**Priority:** P1  
**Effort:** S  
**Feature:** [FEAT-013](../features/FEAT-013-personal-agent-studio.md)  
**Risk tier:** P2

## Problem

Chat cannot include operator documents or images for context.

## What shipped

- `AttachmentStore` under `~/.ai-lab/uploads/{conversation_id}/`
- `POST /v1/conversations/{id}/attachments` (PDF/MD/TXT/PNG/JPEG/WebP, 8 MiB)
- Chat/stream prompts include extracted text (MD/TXT) or honest image/PDF stubs
- UI Attach button on Personal Agent Studio

## Out Of Scope

Vision models; full PDF text extraction library

## Closeout

- Evidence: `tests.test_personal_agent_studio.AttachmentStoreTests`
- Host deploy: with IWO-024 batch
