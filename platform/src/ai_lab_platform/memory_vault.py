"""Personal memory vault: markdown files the agent can list, grep, and read.

The vault lives under the operator home (``~/.ai-lab/memory``), outside Git.
The answering model only reads. ``record_day`` files a digest and does not
rewrite people, preferences, or decisions.
"""

from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from pathlib import Path

_DAY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_FRONT_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
_MAX_FILE_BYTES = 256_000
_BRIEF_CAP = 4_000
_READ_CAP = 8_000

LAYOUT = (
    "entities/people",
    "entities/projects",
    "knowledge/facts",
    "knowledge/preferences",
    "knowledge/decisions",
    "comms",
    "timeline/daily",
    "timeline/weekly",
    "workstreams/active",
    "workstreams/completed",
)

_IDENTITY = """---
id: operator
type: identity
aliases: [me, operator]
---

Name, timezone, and how autonomous this assistant should be go in this file.
The assistant reads this file. A later filing job does not rewrite it.
"""

_README = """# Personal memory

Markdown files for the personal agent. Each file may start with `id`, `type`,
and `aliases`. Search is a word match over the file text and those aliases.
`timeline/daily/` holds filed notes. Entity and preference files are current
state and are not rewritten by the daily filer.
"""


class VaultError(ValueError):
    """A vault path or argument the agent must not follow."""


def default_vault_root() -> Path:
    override = os.environ.get("AI_LAB_MEMORY_VAULT", "").strip()
    if override:
        return Path(override).expanduser()
    return Path.home() / ".ai-lab" / "memory"


def utc_day(when: datetime | None = None) -> str:
    moment = when or datetime.now(timezone.utc)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc).date().isoformat()


class MemoryVault:
    def __init__(self, root: Path | None = None) -> None:
        self.root = (root or default_vault_root()).expanduser()

    def ensure_layout(self) -> None:
        """Create the folder set and starter files. Existing files stay."""
        root = self.root
        root.mkdir(parents=True, exist_ok=True)
        for rel in LAYOUT:
            (root / rel).mkdir(parents=True, exist_ok=True)
        readme = root / "README.md"
        if not readme.is_file():
            readme.write_text(_README, encoding="utf-8")
        identity = root / "identity.md"
        if not identity.is_file():
            identity.write_text(_IDENTITY, encoding="utf-8")

    def render_brief(self, *, day: str | None = None) -> str:
        """Dated preamble. Creates the layout when the vault is new."""
        self.ensure_layout()
        today = day or utc_day()
        identity = self._read_text(self.root / "identity.md")
        open_work = self._titles("workstreams/active")
        daily = self.root / "timeline" / "daily" / f"{today}.md"
        if daily.is_file():
            day_line = f"Today's note exists: timeline/daily/{today}.md"
        else:
            day_line = f"No timeline note for {today} yet."
        work_lines = "\n".join(f"- {item}" for item in open_work[:15]) or "- (none)"
        text = (
            f"Personal brief as of {today} UTC. "
            "This brief can be stale. Search the vault before treating a line as current.\n\n"
            f"## Identity\n{identity[:1500].strip()}\n\n"
            f"## Open work\n{work_lines}\n\n"
            f"## Day\n{day_line}\n"
        )
        return text[:_BRIEF_CAP]

    def list_files(self, prefix: str = "", *, limit: int = 200) -> str:
        root = self._existing_root()
        if root is None:
            return "vault_list hits=0\nvault has no files yet"
        rel_prefix = _safe_prefix(prefix)
        rows: list[str] = []
        for path in _markdown_files(root):
            rel = path.relative_to(root).as_posix()
            if rel_prefix and rel != rel_prefix and not rel.startswith(rel_prefix + "/"):
                continue
            rows.append(rel)
            if len(rows) >= limit:
                break
        if not rows:
            return f"vault_list hits=0 prefix={rel_prefix or '/'}"
        head = f"vault_list hits={len(rows)} prefix={rel_prefix or '/'}"
        return head + "\n" + "\n".join(rows)

    def grep(self, query: str, *, limit: int = 8) -> str:
        needle = _query(query)
        root = self._existing_root()
        if root is None:
            return f"vault_grep query={needle} hits=0\nvault has no files yet"
        ranked: list[tuple[int, str, list[str]]] = []
        for path in _markdown_files(root):
            text = _read_capped(path)
            if text is None:
                continue
            meta, body = _frontmatter(text)
            aliases = [str(item) for item in meta.get("aliases") or []]
            alias_hit = _alias_hit(needle, aliases)
            body_hit = needle.casefold() in text.casefold()
            if not alias_hit and not body_hit:
                continue
            rel = path.relative_to(root).as_posix()
            lines = _matching_lines(body, needle)[:3]
            label = f"{rel} id={meta.get('id') or path.stem}"
            if aliases:
                label += " aliases=" + ", ".join(aliases[:12])
            ranked.append((0 if alias_hit else 1, label, lines))
        ranked.sort(key=lambda item: (item[0], item[1]))
        chosen = ranked[:limit]
        if not chosen:
            return f"vault_grep query={needle} hits=0"
        blocks = [f"vault_grep query={needle} hits={len(chosen)}"]
        for _rank, label, lines in chosen:
            blocks.append(label)
            blocks.extend(lines)
        return "\n".join(blocks)[:_READ_CAP]

    def read(self, rel: str) -> str:
        root = self._existing_root()
        if root is None:
            raise VaultError("vault has no files yet")
        path = _confine(root, rel)
        if not path.is_file():
            raise VaultError(f"no such vault file: {rel}")
        if path.suffix.lower() != ".md":
            raise VaultError("vault reads markdown files only")
        text = _read_capped(path)
        if text is None:
            raise VaultError("vault file is too large to read")
        header = path.relative_to(root).as_posix()
        return f"{header}\n{text[:_READ_CAP]}"

    def record_day(self, day: str, lines: list[str]) -> str:
        """Append a digest under timeline/daily. Does not edit other files."""
        if not _DAY_RE.match(day or ""):
            raise VaultError("day must be YYYY-MM-DD")
        notes = []
        for line in lines:
            cleaned = " ".join(str(line).split())
            if not cleaned:
                continue
            notes.append(cleaned[:500])
            if len(notes) >= 40:
                break
        if not notes:
            raise VaultError("nothing to file")
        self.ensure_layout()
        path = self.root / "timeline" / "daily" / f"{day}.md"
        path = _confine(self.root.resolve(), f"timeline/daily/{day}.md")
        block = "\n".join(f"- {note}" for note in notes)
        if path.is_file():
            existing = path.read_text(encoding="utf-8")
            path.write_text(existing.rstrip() + "\n\n## Filed\n" + block + "\n", encoding="utf-8")
        else:
            path.write_text(
                (
                    f"---\nid: {day}\ntype: timeline\naliases: [{day}]\n---\n\n"
                    f"# {day}\n\n## Filed\n{block}\n"
                ),
                encoding="utf-8",
            )
        return f"timeline/daily/{day}.md"

    def write_entry(
        self,
        category: str,
        title: str,
        content: str,
        *,
        entry_type: str = "",
    ) -> str:
        """Record a structured memory file in the vault with frontmatter."""
        self.ensure_layout()
        cat = (category or "facts").strip().lower()
        valid_dirs = {
            "preferences": "knowledge/preferences",
            "preference": "knowledge/preferences",
            "facts": "knowledge/facts",
            "fact": "knowledge/facts",
            "decisions": "knowledge/decisions",
            "decision": "knowledge/decisions",
            "projects": "entities/projects",
            "project": "entities/projects",
            "people": "entities/people",
            "person": "entities/people",
        }
        rel_dir = valid_dirs.get(cat, "knowledge/facts")
        cleaned_title = title.strip() or "untitled"
        slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", cleaned_title.lower()).strip("-")[:60] or "entry"
        rel_path = f"{rel_dir}/{slug}.md"
        path = _confine(self.root.resolve(), rel_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        today = utc_day()
        meta_type = entry_type.strip() or cat
        frontmatter = (
            f"---\nid: {slug}\ntype: {meta_type}\naliases: [{cleaned_title}]\nupdated_at: {today}\n---\n\n"
        )
        body = f"# {cleaned_title}\n\n{content.strip()}\n"
        path.write_text(frontmatter + body, encoding="utf-8")
        return f"vault_write filed={rel_path} title={cleaned_title}"

    def _existing_root(self) -> Path | None:
        root = self.root
        if not root.is_dir():
            return None
        return root.resolve()

    def _read_text(self, path: Path) -> str:
        if not path.is_file():
            return "(identity file is missing)"
        return path.read_text(encoding="utf-8")

    def _titles(self, rel: str) -> list[str]:
        folder = self.root / rel
        if not folder.is_dir():
            return []
        found: list[str] = []
        for path in sorted(folder.glob("*.md")):
            if path.is_symlink():
                continue
            text = _read_capped(path) or ""
            meta, body = _frontmatter(text)
            title = str(meta.get("id") or path.stem)
            first = next((line.strip("# ").strip() for line in body.splitlines() if line.strip()), "")
            if first:
                title = first[:120]
            found.append(f"{rel}/{path.name} — {title}")
        return found


def _safe_prefix(prefix: str) -> str:
    raw = (prefix or "").strip().replace("\\", "/").lstrip("/")
    if not raw:
        return ""
    parts = Path(raw).parts
    if ".." in parts:
        raise VaultError("prefix escapes the memory vault")
    return raw.rstrip("/")


def _query(query: str) -> str:
    needle = " ".join((query or "").split())
    if not needle:
        raise VaultError("query is empty")
    if len(needle) > 200:
        raise VaultError("query is too long")
    return needle


def _confine(root: Path, rel: str) -> Path:
    raw = (rel or "").strip().replace("\\", "/")
    if not raw or raw.startswith("/") or raw.startswith("~"):
        raise VaultError("path escapes the memory vault")
    parts = Path(raw).parts
    if ".." in parts or any(part.startswith("/") for part in parts):
        raise VaultError("path escapes the memory vault")
    root_r = root.resolve()
    candidate = (root_r / raw).resolve()
    try:
        candidate.relative_to(root_r)
    except ValueError as exc:
        raise VaultError("path escapes the memory vault") from exc
    return candidate


def _frontmatter(text: str) -> tuple[dict[str, object], str]:
    match = _FRONT_RE.match(text or "")
    if not match:
        return {}, text or ""
    meta: dict[str, object] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        name = key.strip()
        raw = value.strip()
        if raw.startswith("[") and raw.endswith("]"):
            inner = raw[1:-1].strip()
            items = []
            if inner:
                for part in inner.split(","):
                    item = part.strip().strip("'\"")
                    if item:
                        items.append(item)
            meta[name] = items
        else:
            meta[name] = raw.strip("'\"")
    return meta, text[match.end() :]


def _alias_hit(needle: str, aliases: list[str]) -> bool:
    folded = needle.casefold()
    for alias in aliases:
        item = alias.casefold()
        if not item:
            continue
        if folded == item or folded in item:
            return True
        if len(item) >= 3 and item in folded:
            return True
    return False


def _matching_lines(body: str, needle: str) -> list[str]:
    folded = needle.casefold()
    found: list[str] = []
    for line in body.splitlines():
        if folded in line.casefold() and line.strip():
            found.append(line.strip()[:240])
    return found


def _read_capped(path: Path) -> str | None:
    try:
        if path.stat().st_size > _MAX_FILE_BYTES:
            return None
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None


def _markdown_files(root: Path) -> list[Path]:
    found: list[Path] = []
    root_r = root.resolve()
    for dirpath, dirnames, filenames in os.walk(root_r, followlinks=False):
        dirnames[:] = sorted(name for name in dirnames if not name.startswith("."))
        for name in sorted(filenames):
            if not name.endswith(".md"):
                continue
            path = Path(dirpath) / name
            if path.is_symlink():
                continue
            try:
                resolved = path.resolve()
                resolved.relative_to(root_r)
            except (OSError, ValueError):
                continue
            found.append(resolved)
    return found
