"""Presentation and slide deck generator for AI Lab agents (IWO-104).

Produces standalone, beautiful HTML presentations and Markdown slides stored under
``~/.ai-lab/presentations``, outside Git.
"""

from __future__ import annotations

import html
import os
import re
from pathlib import Path
from typing import Any

_SLUG_RE = re.compile(r"[^a-z0-9_-]+")
_MAX_SLIDES = 50


class PresentationError(ValueError):
    """Path escape or presentation formatting error."""


def default_presentations_root() -> Path:
    override = os.environ.get("AI_LAB_PRESENTATIONS_ROOT", "").strip()
    if override:
        return Path(override).expanduser()
    return Path.home() / ".ai-lab" / "presentations"


def _safe_slug(name: str) -> str:
    if ".." in name or "/" in name or "\\" in name:
        raise PresentationError("name cannot contain path separators or parent directory references")
    cleaned = _SLUG_RE.sub("-", name.strip().lower()).strip("-")
    return cleaned[:60] or "presentation"


def _confine(root: Path, rel: str) -> Path:
    raw = rel.strip().replace("\\", "/")
    if not raw or raw.startswith("/") or ".." in Path(raw).parts:
        raise PresentationError("path escapes presentations root")
    candidate = (root.resolve() / raw).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise PresentationError("path escapes presentations root") from exc
    return candidate


def _parse_slides(content: str) -> list[dict[str, str]]:
    """Parse slide sections from markdown separated by '---'."""
    raw_blocks = [b.strip() for b in re.split(r"\n---\n", content) if b.strip()]
    if not raw_blocks:
        raw_blocks = [content.strip() or "Empty Presentation"]
    slides: list[dict[str, str]] = []
    for idx, block in enumerate(raw_blocks[:_MAX_SLIDES]):
        lines = block.splitlines()
        title = ""
        body_lines: list[str] = []
        for line in lines:
            if not title and line.startswith("#"):
                title = line.lstrip("#").strip()
            else:
                body_lines.append(line)
        slides.append(
            {
                "index": str(idx + 1),
                "title": title or f"Slide {idx + 1}",
                "body": "\n".join(body_lines).strip(),
            }
        )
    return slides


def _render_html(deck_title: str, slides: list[dict[str, str]]) -> str:
    """Generate a self-contained, beautiful HTML slide deck with keyboard navigation."""
    safe_title = html.escape(deck_title)
    slides_html: list[str] = []

    for s in slides:
        idx = s["index"]
        stitle = html.escape(s["title"])
        # Format body lines into HTML paragraphs/lists/code blocks
        body_parts: list[str] = []
        in_list = False
        in_code = False
        code_lines: list[str] = []

        for line in s["body"].splitlines():
            sline = line.strip()
            if sline.startswith("```"):
                if in_code:
                    body_parts.append(
                        f"<pre><code>{html.escape(chr(10).join(code_lines))}</code></pre>"
                    )
                    code_lines = []
                    in_code = False
                else:
                    in_code = True
                continue
            if in_code:
                code_lines.append(line)
                continue
            if sline.startswith("- ") or sline.startswith("* "):
                if not in_list:
                    body_parts.append("<ul>")
                    in_list = True
                body_parts.append(f"<li>{html.escape(sline[2:].strip())}</li>")
                continue
            if in_list:
                body_parts.append("</ul>")
                in_list = False
            if sline:
                body_parts.append(f"<p>{html.escape(sline)}</p>")

        if in_code and code_lines:
            body_parts.append(f"<pre><code>{html.escape(chr(10).join(code_lines))}</code></pre>")
        if in_list:
            body_parts.append("</ul>")

        content_html = "\n".join(body_parts)
        active_cls = " active" if idx == "1" else ""
        slides_html.append(
            f"""
      <div class="slide{active_cls}" data-slide="{idx}">
        <div class="slide-header">
          <span class="slide-badge">AI Lab Presentation</span>
          <span class="slide-num">{idx} / {len(slides)}</span>
        </div>
        <h2 class="slide-title">{stitle}</h2>
        <div class="slide-body">
          {content_html}
        </div>
      </div>"""
        )

    slides_rendered = "\n".join(slides_html)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{safe_title} · AI Lab Presentation</title>
  <style>
    :root {{
      --bg: #121212;
      --card-bg: #1e1e1e;
      --ink: #ececec;
      --muted: #a0a0a0;
      --accent: #7cb8ff;
      --line: #2e2e2e;
      --font: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0; height: 100vh; overflow: hidden;
      background: var(--bg); color: var(--ink);
      font-family: var(--font); display: flex; flex-direction: column;
    }}
    .deck-container {{
      flex: 1; display: flex; align-items: center; justify-content: center;
      padding: 32px; position: relative;
    }}
    .slide {{
      display: none; width: min(960px, 92vw); min-height: 540px;
      background: var(--card-bg); border: 1px solid var(--line);
      border-radius: 20px; padding: 48px 56px; box-shadow: 0 24px 64px rgba(0,0,0,0.45);
      flex-direction: column; animation: fadeIn .2s ease-out;
    }}
    .slide.active {{ display: flex; }}
    @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(8px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    .slide-header {{
      display: flex; justify-content: space-between; align-items: center;
      margin-bottom: 24px; font-size: 13px; text-transform: uppercase; letter-spacing: .08em;
      color: var(--muted);
    }}
    .slide-badge {{ color: var(--accent); font-weight: 600; }}
    .slide-title {{
      margin: 0 0 28px; font-size: 32px; font-weight: 700;
      color: #ffffff; letter-spacing: -.02em; line-height: 1.25;
    }}
    .slide-body {{ flex: 1; font-size: 18px; line-height: 1.6; color: #d0d0d0; }}
    .slide-body p {{ margin: 0 0 16px; }}
    .slide-body ul {{ margin: 0 0 20px; padding-left: 24px; }}
    .slide-body li {{ margin-bottom: 10px; }}
    .slide-body pre {{
      background: #111; padding: 16px; border-radius: 10px;
      overflow-x: auto; font-family: ui-monospace, Menlo, monospace; font-size: 14px;
      border: 1px solid var(--line); color: var(--accent);
    }}
    .controls {{
      display: flex; justify-content: space-between; align-items: center;
      padding: 16px 36px; border-top: 1px solid var(--line); background: #161616;
      font-size: 14px; color: var(--muted);
    }}
    .btn-nav {{
      background: #252525; border: 1px solid var(--line); color: var(--ink);
      padding: 8px 16px; border-radius: 8px; font: inherit; cursor: pointer;
    }}
    .btn-nav:hover {{ background: #333; }}
  </style>
</head>
<body>
  <div class="deck-container">
    {slides_rendered}
  </div>
  <div class="controls">
    <div><strong>{safe_title}</strong> (Use &larr; / &rarr; or Space)</div>
    <div style="display:flex;gap:8px;">
      <button type="button" class="btn-nav" id="prev-btn">&larr; Prev</button>
      <button type="button" class="btn-nav" id="next-btn">Next &rarr;</button>
    </div>
  </div>
  <script>
    let cur = 1;
    const total = {len(slides)};
    function show(idx) {{
      if (idx < 1 || idx > total) return;
      cur = idx;
      document.querySelectorAll('.slide').forEach(s => {{
        s.classList.toggle('active', parseInt(s.getAttribute('data-slide')) === cur);
      }});
    }}
    document.getElementById('prev-btn').onclick = () => show(cur - 1);
    document.getElementById('next-btn').onclick = () => show(cur + 1);
    window.addEventListener('keydown', (e) => {{
      if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'PageDown') show(cur + 1);
      else if (e.key === 'ArrowLeft' || e.key === 'PageUp') show(cur - 1);
      else if (e.key === 'Home') show(1);
      else if (e.key === 'End') show(total);
    }});
  </script>
</body>
</html>"""


class PresentationLibrary:
    def __init__(self, root: Path | None = None) -> None:
        self.root = (root or default_presentations_root()).expanduser()

    def write(self, name: str, title: str, content: str) -> str:
        """Write slide deck as both clean Markdown and standalone interactive HTML."""
        slug = _safe_slug(name or title)
        cleaned_title = (title or name or "AI Lab Presentation").strip()
        body = (content or "").strip()
        if not body:
            raise PresentationError("presentation content cannot be empty")

        slides = _parse_slides(body)
        self.root.mkdir(parents=True, exist_ok=True)

        md_path = _confine(self.root.resolve(), f"{slug}.md")
        html_path = _confine(self.root.resolve(), f"{slug}.html")

        # Save markdown
        md_text = f"# {cleaned_title}\n\n{body}\n"
        md_path.write_text(md_text, encoding="utf-8")

        # Save HTML presentation
        html_rendered = _render_html(cleaned_title, slides)
        html_path.write_text(html_rendered, encoding="utf-8")

        return (
            f"presentation_write filed={slug}.html (title: '{cleaned_title}', "
            f"slides: {len(slides)}). View in browser or share."
        )

    def list_presentations(self, *, limit: int = 50) -> str:
        if not self.root.is_dir():
            return "presentation_list: No presentations yet."
        files = sorted(self.root.glob("*.html"))
        if not files:
            return "presentation_list: No presentations yet."
        lines = [f"presentation_list hits={len(files)}:"]
        for p in files[:limit]:
            lines.append(f"- {p.name}")
        return "\n".join(lines)

    def read(self, name: str) -> str:
        slug = _safe_slug(name)
        path = _confine(self.root.resolve(), f"{slug}.md")
        if not path.is_file():
            raise PresentationError(f"presentation '{slug}.md' not found")
        return path.read_text(encoding="utf-8")
