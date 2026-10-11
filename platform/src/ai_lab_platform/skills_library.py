"""Procedural Skill Library for AI Lab agents (IWO-104).

Enables agents to construct, persist, browse, and execute specialized skills stored under
``~/.ai-lab/skills/``, outside Git.
"""

from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SLUG_RE = re.compile(r"[^a-z0-9_-]+")


class SkillError(ValueError):
    """Path escape or skill format error."""


def default_skills_root() -> Path:
    override = os.environ.get("AI_LAB_SKILLS_ROOT", "").strip()
    if override:
        return Path(override).expanduser()
    return Path.home() / ".ai-lab" / "skills"


def _safe_slug(name: str) -> str:
    if ".." in name or "/" in name or "\\" in name:
        raise SkillError("name cannot contain path separators or parent directory references")
    cleaned = _SLUG_RE.sub("-", name.strip().lower()).strip("-")
    return cleaned[:60] or "custom-skill"


def _confine(root: Path, rel: str) -> Path:
    raw = rel.strip().replace("\\", "/")
    if not raw or raw.startswith("/") or ".." in Path(raw).parts:
        raise SkillError("path escapes skills root")
    candidate = (root.resolve() / raw).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise SkillError("path escapes skills root") from exc
    return candidate


class SkillLibrary:
    def __init__(self, root: Path | None = None) -> None:
        self.root = (root or default_skills_root()).expanduser()

    def create(self, name: str, description: str, steps: str) -> str:
        """Persist a new procedural skill with standard YAML frontmatter."""
        clean_name = name.strip() or "Custom Skill"
        slug = _safe_slug(clean_name)
        clean_desc = (description or clean_name).strip()
        clean_steps = (steps or "").strip()
        if not clean_steps:
            raise SkillError("steps or procedure is required to create a skill")

        self.root.mkdir(parents=True, exist_ok=True)
        skill_dir = _confine(self.root.resolve(), slug)
        skill_dir.mkdir(parents=True, exist_ok=True)

        skill_file = skill_dir / "SKILL.md"
        now_iso = datetime.now(timezone.utc).date().isoformat()

        content = (
            f"---\n"
            f"name: {clean_name}\n"
            f"slug: {slug}\n"
            f"description: {clean_desc}\n"
            f"created_at: {now_iso}\n"
            f"---\n\n"
            f"# {clean_name}\n\n"
            f"## Purpose\n"
            f"{clean_desc}\n\n"
            f"## Procedural Execution Steps\n"
            f"{clean_steps}\n"
        )

        skill_file.write_text(content, encoding="utf-8")
        return (
            f"skill_create success: Created skill '{clean_name}' at skills/{slug}/SKILL.md. "
            f"Agents can now read and execute this procedural skill."
        )

    def list_skills(self, *, limit: int = 50) -> str:
        if not self.root.is_dir():
            return "skill_list: No custom skills installed yet."
        entries: list[str] = []
        for d in sorted(self.root.iterdir()):
            if not d.is_dir():
                continue
            skill_md = d / "SKILL.md"
            if skill_md.is_file():
                # Extract first title or description
                first_lines = skill_md.read_text(encoding="utf-8").splitlines()[:10]
                desc = d.name
                for line in first_lines:
                    if line.startswith("description:"):
                        desc = line.split(":", 1)[1].strip()
                        break
                entries.append(f"- '{d.name}': {desc}")
            if len(entries) >= limit:
                break
        if not entries:
            return "skill_list: No custom skills installed yet."
        return f"skill_list hits={len(entries)}:\n" + "\n".join(entries)

    def read(self, name: str) -> str:
        slug = _safe_slug(name)
        skill_dir = _confine(self.root.resolve(), slug)
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.is_file():
            raise SkillError(f"skill '{name}' (slug: {slug}) not found")
        return skill_file.read_text(encoding="utf-8")
