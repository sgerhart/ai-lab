"""Conversation attachments (FEAT-013 / IWO-025). Files under ~/.ai-lab/uploads/."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any
from uuid import uuid4

_SAFE_NAME = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
ALLOWED_EXTENSIONS = {
    ".pdf": "application/pdf",
    ".md": "text/markdown",
    ".txt": "text/plain",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}
MAX_BYTES = 8 * 1024 * 1024  # 8 MiB
# llama3.2:3b on Studio Ollama 0.34 allocates llama.context_length (131072).
# The lab does not override num_ctx. Leave room for the reply; older turns fall off.
DEFAULT_CONTEXT_TOKENS = 131072
REPLY_RESERVE_TOKENS = 2048
CHARS_PER_TOKEN = 4
MAX_ATTACHMENT_TEXT_CHARS = 200_000


class AttachmentError(ValueError):
    pass


def default_uploads_root() -> Path:
    return Path.home() / ".ai-lab" / "uploads"


class AttachmentStore:
    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root) if root else default_uploads_root()

    def ensure(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.root, 0o700)

    def _conv_dir(self, conversation_id: str) -> Path:
        if not re.match(r"^[0-9a-fA-F-]{8,64}$", conversation_id):
            raise AttachmentError("invalid conversation id")
        path = self.root / conversation_id
        path.mkdir(parents=True, exist_ok=True, mode=0o700)
        return path

    def save(
        self,
        *,
        conversation_id: str,
        filename: str,
        data: bytes,
        content_type: str = "",
    ) -> dict[str, Any]:
        if len(data) > MAX_BYTES:
            raise AttachmentError(f"file too large (max {MAX_BYTES} bytes)")
        if len(data) == 0:
            raise AttachmentError("empty file")
        base = Path(filename).name
        if not _SAFE_NAME.match(base):
            # sanitize
            base = re.sub(r"[^A-Za-z0-9._-]+", "_", base)[:128] or "upload.bin"
        ext = Path(base).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise AttachmentError(
                f"unsupported type {ext!r}; allowed: {sorted(ALLOWED_EXTENSIONS)}"
            )
        expected = ALLOWED_EXTENSIONS[ext]
        ctype = content_type.strip() or expected
        self.ensure()
        att_id = str(uuid4())
        dest = self._conv_dir(conversation_id) / f"{att_id}{ext}"
        dest.write_bytes(data)
        os.chmod(dest, 0o600)
        meta = {
            "id": att_id,
            "conversation_id": conversation_id,
            "filename": base,
            "content_type": ctype,
            "bytes": len(data),
            "path": str(dest),
            "ext": ext,
        }
        (self._conv_dir(conversation_id) / f"{att_id}.json").write_text(
            __import__("json").dumps(meta), encoding="utf-8"
        )
        return {k: v for k, v in meta.items() if k != "path"}

    def get_meta(self, conversation_id: str, attachment_id: str) -> dict[str, Any] | None:
        meta_path = self._conv_dir(conversation_id) / f"{attachment_id}.json"
        if not meta_path.is_file():
            return None
        import json

        data = json.loads(meta_path.read_text(encoding="utf-8"))
        return {k: v for k, v in data.items() if k != "path"}

    def read_bytes(self, conversation_id: str, attachment_id: str) -> tuple[bytes, dict[str, Any]]:
        import json

        meta_path = self._conv_dir(conversation_id) / f"{attachment_id}.json"
        if not meta_path.is_file():
            raise AttachmentError("attachment not found")
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        path = Path(meta["path"])
        if not path.is_file():
            raise AttachmentError("attachment file missing")
        return path.read_bytes(), meta

    def extract_text_for_prompt(self, conversation_id: str, attachment_ids: list[str]) -> str:
        """Best-effort text for model context. Images get a placeholder caption."""
        parts: list[str] = []
        for att_id in attachment_ids[:8]:
            try:
                data, meta = self.read_bytes(conversation_id, att_id)
            except AttachmentError:
                continue
            name = meta.get("filename") or att_id
            ext = str(meta.get("ext") or "").lower()
            if ext in {".md", ".txt"}:
                text = data.decode("utf-8", errors="replace")[:MAX_ATTACHMENT_TEXT_CHARS]
                parts.append(f"[attachment {name}]\n{text}")
            elif ext == ".pdf":
                # No PDF parser dependency yet — honest stub.
                parts.append(
                    f"[attachment {name}: PDF {meta.get('bytes')} bytes; "
                    "text extraction not installed — summarize from filename only]"
                )
            elif ext in {".png", ".jpg", ".jpeg", ".webp"}:
                parts.append(
                    f"[attachment {name}: image {meta.get('content_type')}, "
                    f"{meta.get('bytes')} bytes; vision not enabled on this Studio model yet]"
                )
            else:
                parts.append(f"[attachment {name}: unsupported for context]")
        return "\n\n".join(parts)


def document_text(filename: str, data: bytes) -> tuple[str, str]:
    """Return (citation source, text) for a project document. Images and PDFs stay honest stubs."""
    if len(data) > MAX_BYTES:
        raise AttachmentError(f"file too large (max {MAX_BYTES} bytes)")
    if not data:
        raise AttachmentError("empty file")
    base = Path(filename).name
    if not _SAFE_NAME.match(base):
        base = re.sub(r"[^A-Za-z0-9._-]+", "_", base)[:128] or "upload.bin"
    ext = Path(base).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise AttachmentError(f"unsupported type {ext!r}; allowed: {sorted(ALLOWED_EXTENSIONS)}")
    if ext in {".md", ".txt"}:
        return base, data.decode("utf-8", errors="replace")[:MAX_ATTACHMENT_TEXT_CHARS]
    if ext == ".pdf":
        return base, f"[PDF {base}: {len(data)} bytes; text extraction not installed]"
    if ext in {".png", ".jpg", ".jpeg", ".webp"}:
        return base, f"[image {base}: {len(data)} bytes; vision not enabled]"
    raise AttachmentError(f"unsupported type {ext!r}")


def prompt_char_budget(
    context_tokens: int = DEFAULT_CONTEXT_TOKENS,
    reply_reserve: int = REPLY_RESERVE_TOKENS,
) -> int:
    """Characters of chat history that stay inside the model window."""
    usable = max(256, int(context_tokens) - int(reply_reserve))
    return usable * CHARS_PER_TOKEN


def build_chat_prompt(
    turns: list[tuple[str, str, list[str]]],
    attachment_text,
    *,
    max_chars: int | None = None,
) -> str:
    """Newest turns first into the budget. Each turn is (role, content, attachment ids).

    ``attachment_text(ids)`` returns the cited file text for those ids.
    A turn that does not fit is shortened from its attachment, then older turns drop.
    """
    budget = prompt_char_budget() if max_chars is None else max(1, int(max_chars))
    chosen: list[str] = []
    used = 0
    for role, content, ids in reversed(turns):
        block = ""
        if ids:
            block = attachment_text(list(ids)) or ""
        gap = 2 if chosen else 0
        remaining = budget - used - gap
        if remaining <= 0:
            break
        segment = _fit_turn(role, content or "", block, remaining)
        if not segment:
            break
        chosen.append(segment)
        used += len(segment) + gap
    return "\n".join(reversed(chosen))


def _fit_turn(role: str, content: str, block: str, budget: int) -> str:
    head = f"{role}: {content}"
    if not block:
        return head[:budget]
    prefix = head + "\n\nAttached materials:\n"
    if len(prefix) >= budget:
        return head[:budget]
    return prefix + block[: budget - len(prefix)]


def default_attachment_store() -> AttachmentStore:
    return AttachmentStore()
