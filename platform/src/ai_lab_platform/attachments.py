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
                text = data.decode("utf-8", errors="replace")[:12000]
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


def default_attachment_store() -> AttachmentStore:
    return AttachmentStore()
