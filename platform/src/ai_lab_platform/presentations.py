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
    raw = (name or "").strip()
    lower = raw.lower()
    for ext in (".html", ".md"):
        if lower.endswith(ext):
            raw = raw[: -len(ext)].strip()
            break
    if ".." in raw or "/" in raw or "\\" in raw:
        raise PresentationError("name cannot contain path separators or parent directory references")
    cleaned = _SLUG_RE.sub("-", raw.lower()).strip("-")
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


def _clean_slide_title(title: str) -> str:
    """Strip redundant 'Slide 1:', 'Slide 2 -', 'Slide #3:' prefixes from titles."""
    t = (title or "").strip()
    t = re.sub(r"^#+\s*", "", t)
    cleaned = re.sub(r"^Slide\s*#?\d+\s*[:\-–—.]*\s*", "", t, flags=re.IGNORECASE).strip()
    return cleaned or t or "Key Insights"


def _parse_slides(content: str) -> list[dict[str, str]]:
    """Parse slide sections from markdown separated by '---' or slide headers ('## Slide' / '## ')."""
    text = (content or "").strip()
    if not text:
        return [{"index": "1", "title": "Overview", "body": "No content provided."}]

    raw_blocks: list[str] = []

    # 1. Try splitting on horizontal rule lines (---, ***, ===)
    hr_pattern = r"(?m)^\s*(?:---|[*]{3,}|={3,})\s*$"
    if re.search(hr_pattern, text):
        raw_blocks = [b.strip() for b in re.split(hr_pattern, text) if b.strip()]

    # 2. If no horizontal rules, check for '## Slide \d+' or 'Slide \d+:' boundaries
    if len(raw_blocks) <= 1:
        slide_marker_pattern = r"(?m)(?=^(?:#{1,3}\s*)?Slide\s*#?\d+\s*[:\-–—.]*)"
        candidate_blocks = [b.strip() for b in re.split(slide_marker_pattern, text) if b.strip()]
        if len(candidate_blocks) > 1:
            raw_blocks = candidate_blocks

    # 3. If still only 1 block, try splitting on any level-2 markdown headers (## )
    if len(raw_blocks) <= 1:
        h2_pattern = r"(?m)(?=^##\s+)"
        h2_blocks = [b.strip() for b in re.split(h2_pattern, text) if b.strip()]
        if len(h2_blocks) > 1:
            raw_blocks = h2_blocks

    # 4. If still only 1 block, try splitting on level-1 markdown headers (# ) if multiple exist
    if len(raw_blocks) <= 1:
        h1_pattern = r"(?m)(?=^#\s+)"
        h1_blocks = [b.strip() for b in re.split(h1_pattern, text) if b.strip()]
        if len(h1_blocks) > 1:
            raw_blocks = h1_blocks

    if not raw_blocks:
        raw_blocks = [text]

    # Clean up introductory / title-only blocks (e.g. initial `# Deck Title`)
    if len(raw_blocks) > 1:
        first_lines = [l.strip() for l in raw_blocks[0].splitlines() if l.strip()]
        if len(first_lines) <= 2 and all(l.startswith("#") and not re.search(r"Slide\s*#?\d+", l, re.IGNORECASE) for l in first_lines):
            raw_blocks.pop(0)

    slides: list[dict[str, str]] = []
    for idx, block in enumerate(raw_blocks[:_MAX_SLIDES]):
        lines = block.splitlines()
        raw_title = ""
        body_lines: list[str] = []
        for line in lines:
            trimmed = line.strip()
            if not raw_title and (trimmed.startswith("#") or re.match(r"^Slide\s*#?\d+", trimmed, re.IGNORECASE)):
                raw_title = re.sub(r"^#+\s*", "", trimmed).strip()
            else:
                body_lines.append(line)
        clean_title = _clean_slide_title(raw_title)
        body = "\n".join(body_lines).strip()
        slides.append(
            {
                "index": str(idx + 1),
                "title": clean_title or f"Slide {idx + 1}",
                "body": body,
            }
        )

    return slides or [{"index": "1", "title": "Overview", "body": text}]


def _detect_theme(deck_title: str, all_text: str) -> dict[str, Any]:
    """Detect presentation topic and return matching color theme, atmospheric glow, and curated photography."""
    combined = f"{deck_title} {all_text}".lower()
    
    if any(k in combined for k in ["stock", "financial", "market", "revenue", "dividend", "invest", "share", "csco", "cisco stock", "eps", "trading", "crypto"]):
        return {
            "name": "finance",
            "accent": "#00d296",
            "accent_glow": "rgba(0, 210, 150, 0.28)",
            "gradient": "radial-gradient(circle at 85% 15%, rgba(0, 210, 150, 0.18) 0%, transparent 55%), radial-gradient(circle at 15% 85%, rgba(12, 90, 140, 0.22) 0%, transparent 65%)",
            "badge": "📈 Market & Financial Intelligence",
            "images": [
                ("https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=1200&q=80", "Financial Market & Stock Analytics"),
                ("https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?auto=format&fit=crop&w=1200&q=80", "Global Financial Exchange & Trends"),
                ("https://images.unsplash.com/photo-1559526324-4b87b5e36e44?auto=format&fit=crop&w=1200&q=80", "Enterprise Growth & Revenue Metrics"),
                ("https://images.unsplash.com/photo-1544197150-b99a580bb7a8?auto=format&fit=crop&w=1200&q=80", "Infrastructure & Enterprise Backbone"),
                ("https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=1200&q=80", "Executive Headquarters & Strategy"),
            ],
        }
    if any(k in combined for k in ["network", "switch", "router", "cisco", "hardware", "datacenter", "fiber", "infrastructure", "telecom"]):
        return {
            "name": "network",
            "accent": "#00bceb",
            "accent_glow": "rgba(0, 188, 235, 0.28)",
            "gradient": "radial-gradient(circle at 85% 15%, rgba(0, 188, 235, 0.2) 0%, transparent 55%), radial-gradient(circle at 15% 85%, rgba(20, 60, 160, 0.25) 0%, transparent 65%)",
            "badge": "🌐 Network & Cloud Infrastructure",
            "images": [
                ("https://images.unsplash.com/photo-1544197150-b99a580bb7a8?auto=format&fit=crop&w=1200&q=80", "Next-Gen Datacenter Connectivity"),
                ("https://images.unsplash.com/photo-1558494949-ef010cbdcc31?auto=format&fit=crop&w=1200&q=80", "High-Density Server Architecture"),
                ("https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1200&q=80", "Global Interconnected Fabric"),
                ("https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=1200&q=80", "High-Speed Optical Telemetry"),
            ],
        }
    if any(k in combined for k in ["security", "cyber", "threat", "antares", "defense", "posture", "vulnerability", "malware", "auth"]):
        return {
            "name": "security",
            "accent": "#ff5c77",
            "accent_glow": "rgba(255, 92, 119, 0.28)",
            "gradient": "radial-gradient(circle at 85% 15%, rgba(255, 92, 119, 0.2) 0%, transparent 55%), radial-gradient(circle at 15% 85%, rgba(120, 30, 60, 0.25) 0%, transparent 65%)",
            "badge": "🛡️ Security Architecture & Defense",
            "images": [
                ("https://images.unsplash.com/photo-1563986768609-322da13575f3?auto=format&fit=crop&w=1200&q=80", "Cybersecurity Shield & Data Integrity"),
                ("https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&w=1200&q=80", "Zero-Trust Threat Telemetry"),
                ("https://images.unsplash.com/photo-1510511459019-5dda7724fd87?auto=format&fit=crop&w=1200&q=80", "Cryptographic Defense Plane"),
            ],
        }
    if any(k in combined for k in ["ai", "llm", "neural", "model", "intelligence", "agent", "deep learning"]):
        return {
            "name": "ai",
            "accent": "#a87ffb",
            "accent_glow": "rgba(168, 127, 251, 0.28)",
            "gradient": "radial-gradient(circle at 85% 15%, rgba(168, 127, 251, 0.22) 0%, transparent 55%), radial-gradient(circle at 15% 85%, rgba(50, 40, 130, 0.25) 0%, transparent 65%)",
            "badge": "⚡ Artificial Intelligence Systems",
            "images": [
                ("https://images.unsplash.com/photo-1677442136019-21780efad99a?auto=format&fit=crop&w=1200&q=80", "Neural Computing & Cognitive Mesh"),
                ("https://images.unsplash.com/photo-1620712943543-bcc4688e7485?auto=format&fit=crop&w=1200&q=80", "Autonomous Agent Architecture"),
                ("https://images.unsplash.com/photo-1531403009284-440f080d1e12?auto=format&fit=crop&w=1200&q=80", "High-Performance Workstation Cluster"),
            ],
        }
    return {
        "name": "executive",
        "accent": "#7cb8ff",
        "accent_glow": "rgba(124, 184, 255, 0.28)",
        "gradient": "radial-gradient(circle at 85% 15%, rgba(124, 184, 255, 0.18) 0%, transparent 55%), radial-gradient(circle at 15% 85%, rgba(40, 60, 120, 0.22) 0%, transparent 65%)",
        "badge": "📊 Executive Briefing & Strategy",
        "images": [
            ("https://images.unsplash.com/photo-1542744094-3a31f272c490?auto=format&fit=crop&w=1200&q=80", "Executive Strategy & Roadmap"),
            ("https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=1200&q=80", "Enterprise Scale & Governance"),
            ("https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1200&q=80", "Modern Enterprise Horizon"),
        ],
    }


def _format_inline_markdown(text: str) -> str:
    """Format inline markdown bold, quotes, and metrics with rich styling."""
    escaped = html.escape(text)
    # Highlight bold text
    formatted = re.sub(r"\*\*(.+?)\*\*", r'<strong class="hl">\1</strong>', escaped)
    # Highlight italic text
    formatted = re.sub(r"\*(.+?)\*", r"<em>\1</em>", formatted)
    # Highlight numbers/metrics
    formatted = re.sub(
        r"(\b\+?\d+(?:\.\d+)?%|\$\d+(?:\.\d+)?(?:[BMK]| billion| million)?|\bCAGR\b|\bEPS\b)",
        r'<span class="metric-chip">\1</span>',
        formatted,
    )
    return formatted


def _render_html(deck_title: str, slides: list[dict[str, str]]) -> str:
    """Generate a self-contained, beautiful HTML slide deck with topic imagery, rich backgrounds, and keyboard navigation."""
    safe_title = html.escape(deck_title)
    all_body_text = " ".join(s.get("body", "") for s in slides)
    theme = _detect_theme(deck_title, all_body_text)
    curated_images = theme["images"]
    
    slides_html: list[str] = []

    for i, s in enumerate(slides):
        idx = s["index"]
        raw_title = s["title"]
        stitle = _format_inline_markdown(raw_title)
        
        # Check for user-defined image in body markdown: ![alt](url)
        img_match = re.search(r"!\[(.*?)\]\((.*?)\)", s["body"])
        slide_img = ""
        slide_img_caption = ""
        if img_match:
            slide_img_caption = html.escape(img_match.group(1))
            slide_img = img_match.group(2).strip()
        elif curated_images and (i == 0 or i % 2 == 1 or i == len(slides) - 1):
            # Assign contextual curated image
            img_choice = curated_images[i % len(curated_images)]
            slide_img, slide_img_caption = img_choice

        # Parse body lines into HTML elements
        body_parts: list[str] = []
        in_list = False
        in_code = False
        code_lines: list[str] = []

        for line in s["body"].splitlines():
            sline = line.strip()
            # Skip standalone image markdown line since it's presented in the image card
            if sline.startswith("![") and "](" in sline:
                continue
            if sline.startswith("```"):
                if in_code:
                    body_parts.append(
                        f'<pre class="glass-code"><code>{html.escape(chr(10).join(code_lines))}</code></pre>'
                    )
                    code_lines = []
                    in_code = False
                else:
                    in_code = True
                continue
            if in_code:
                code_lines.append(line)
                continue
            if sline.startswith(">"):
                if in_list:
                    body_parts.append("</ul>")
                    in_list = False
                quote_text = _format_inline_markdown(sline.lstrip(">").strip())
                body_parts.append(f'<div class="quote-callout"><span class="quote-icon">💡</span><div>{quote_text}</div></div>')
                continue
            if sline.startswith("- ") or sline.startswith("* "):
                if not in_list:
                    body_parts.append('<ul class="slide-list">')
                    in_list = True
                item_content = _format_inline_markdown(sline[2:].strip())
                body_parts.append(f"<li>{item_content}</li>")
                continue
            if in_list:
                body_parts.append("</ul>")
                in_list = False
            if sline:
                p_content = _format_inline_markdown(sline)
                body_parts.append(f"<p>{p_content}</p>")

        if in_code and code_lines:
            body_parts.append(f'<pre class="glass-code"><code>{html.escape(chr(10).join(code_lines))}</code></pre>')
        if in_list:
            body_parts.append("</ul>")

        content_html = "\n".join(body_parts)
        active_cls = " active" if idx == "1" else ""
        
        # Determine slide layout
        is_title_slide = (idx == "1")
        if is_title_slide:
            # Hero Cover Slide Layout
            cover_style = f"background-image: linear-gradient(180deg, rgba(14,16,22,0.7) 0%, rgba(14,16,22,0.95) 100%), url('{slide_img}');" if slide_img else ""
            slides_html.append(
                f"""
      <div class="slide hero-slide{active_cls}" data-slide="{idx}" style="{cover_style}">
        <div class="hero-overlay"></div>
        <div class="hero-content">
          <div class="hero-badge">{theme['badge']}</div>
          <h1 class="hero-title">{stitle}</h1>
          <div class="hero-body">{content_html}</div>
          <div class="hero-footer">
            <span class="hero-meta">Slide 01 of {len(slides):02d} · AI Lab Executive Briefing</span>
            <span class="hero-nav-hint">Press &rarr; or Space to begin</span>
          </div>
        </div>
      </div>"""
            )
        elif slide_img:
            # 2-Column Split Layout with Featured Topic Image Card
            slides_html.append(
                f"""
      <div class="slide split-slide{active_cls}" data-slide="{idx}">
        <div class="slide-header">
          <span class="slide-badge">{theme['badge']}</span>
          <span class="slide-num">Slide {int(idx):02d} of {len(slides):02d}</span>
        </div>
        <div class="split-grid">
          <div class="split-main">
            <h2 class="slide-title">{stitle}</h2>
            <div class="slide-body">
              {content_html}
            </div>
          </div>
          <div class="split-media">
            <div class="media-card">
              <img src="{slide_img}" alt="{slide_img_caption}" class="media-img" loading="lazy" />
              <div class="media-caption">{slide_img_caption}</div>
            </div>
          </div>
        </div>
      </div>"""
            )
        else:
            # Full-Width Standard Slide
            slides_html.append(
                f"""
      <div class="slide standard-slide{active_cls}" data-slide="{idx}">
        <div class="slide-header">
          <span class="slide-badge">{theme['badge']}</span>
          <span class="slide-num">Slide {int(idx):02d} of {len(slides):02d}</span>
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
      --bg: #0b0d13;
      --card-bg: rgba(22, 26, 36, 0.85);
      --ink: #f0f3f8;
      --muted: #94a3b8;
      --accent: {theme['accent']};
      --accent-glow: {theme['accent_glow']};
      --line: rgba(255, 255, 255, 0.08);
      --font: "Söhne", ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0; height: 100vh; overflow: hidden;
      background: var(--bg);
      background-image: {theme['gradient']};
      color: var(--ink);
      font-family: var(--font);
      display: flex; flex-direction: column;
    }}
    .progress-bar {{
      height: 3px; background: rgba(255, 255, 255, 0.08); width: 100%; position: relative;
    }}
    .progress-fill {{
      height: 100%; width: 10%; background: var(--accent);
      box-shadow: 0 0 12px var(--accent);
      transition: width 0.25s ease;
    }}
    .deck-container {{
      flex: 1; position: relative; min-height: 0;
    }}
    .slide {{
      display: none;
      position: absolute; inset: 16px 28px 12px;
      width: auto; height: auto;
      background: var(--card-bg);
      backdrop-filter: blur(24px);
      -webkit-backdrop-filter: blur(24px);
      border: 1px solid var(--line);
      border-radius: 24px; padding: 40px 48px;
      box-shadow: 0 24px 80px rgba(0, 0, 0, 0.6), 0 0 1px 1px rgba(255, 255, 255, 0.05);
      flex-direction: column; animation: slideFade .22s cubic-bezier(0.16, 1, 0.3, 1);
      overflow: auto;
    }}
    .slide.active {{ display: flex; }}
    .slide:not(.active) {{ display: none !important; }}
    @keyframes slideFade {{
      from {{ opacity: 0; transform: scale(0.985) translateY(6px); }}
      to {{ opacity: 1; transform: scale(1) translateY(0); }}
    }}
    .slide-header {{
      display: flex; justify-content: space-between; align-items: center;
      margin-bottom: 20px; font-size: 12px; text-transform: uppercase; letter-spacing: .08em;
      color: var(--muted); flex-shrink: 0;
    }}
    .slide-badge {{
      display: inline-flex; align-items: center; gap: 6px;
      padding: 4px 12px; border-radius: 999px;
      background: rgba(255, 255, 255, 0.05); border: 1px solid var(--line);
      color: var(--accent); font-weight: 600;
    }}
    .slide-num {{ font-variant-numeric: tabular-nums; color: var(--muted); }}
    .slide-title {{
      margin: 0 0 20px; font-size: 30px; font-weight: 700;
      color: #ffffff; letter-spacing: -.02em; line-height: 1.25;
      flex-shrink: 0;
    }}
    .slide-body {{
      flex: 1 0 auto; font-size: 16.5px; line-height: 1.6; color: #cbd5e1;
      overflow: visible;
    }}
    .slide-body p {{ margin: 0 0 14px; }}
    .slide-list {{ margin: 0 0 16px; padding-left: 20px; }}
    .slide-list li {{ margin-bottom: 10px; line-height: 1.5; }}
    .hl {{
      color: #ffffff; font-weight: 600;
      text-decoration-color: var(--accent);
    }}
    .metric-chip {{
      display: inline-block; padding: 1px 7px; border-radius: 6px;
      background: rgba(255, 255, 255, 0.08); border: 1px solid var(--line);
      color: var(--accent); font-weight: 600; font-family: ui-monospace, Menlo, monospace;
      font-size: 0.95em;
    }}
    .quote-callout {{
      display: flex; gap: 12px; align-items: flex-start;
      margin: 16px 0; padding: 14px 18px; border-radius: 12px;
      background: rgba(255, 255, 255, 0.03); border-left: 3px solid var(--accent);
      color: #e2e8f0; font-size: 15px; font-style: italic;
    }}
    .quote-icon {{ font-size: 18px; line-height: 1; flex-shrink: 0; padding-top: 2px; }}
    .glass-code {{
      background: rgba(0, 0, 0, 0.4); padding: 14px 18px; border-radius: 12px;
      border: 1px solid var(--line); font-family: ui-monospace, Menlo, monospace;
      font-size: 13.5px; color: var(--accent); overflow-x: auto;
    }}

    /* 2-Column Split Layout */
    .split-grid {{
      display: grid; grid-template-columns: minmax(0, 1.35fr) minmax(240px, 1fr); gap: 32px;
      flex: 1 0 auto; align-items: start;
    }}
    .split-main {{ display: flex; flex-direction: column; min-width: 0; }}
    .split-media {{ display: flex; flex-direction: column; justify-content: center; }}
    .media-card {{
      background: rgba(0, 0, 0, 0.35); border: 1px solid var(--line);
      border-radius: 18px; overflow: hidden;
      box-shadow: 0 16px 40px rgba(0, 0, 0, 0.4), 0 0 20px var(--accent-glow);
      display: flex; flex-direction: column;
    }}
    .media-img {{
      width: 100%; height: 260px; object-fit: cover; display: block;
      transition: transform 0.3s ease;
    }}
    .media-card:hover .media-img {{ transform: scale(1.02); }}
    .media-caption {{
      padding: 10px 14px; font-size: 12px; color: var(--muted);
      border-top: 1px solid var(--line); background: rgba(10, 12, 18, 0.7);
      text-align: center;
    }}

    /* Hero Title Slide */
    .hero-slide {{
      background-size: cover; background-position: center;
      flex-direction: column; justify-content: safe center;
      padding: 56px 64px; text-align: left;
    }}
    .hero-overlay {{
      position: absolute; inset: 0;
      background: radial-gradient(circle at 20% 40%, rgba(10, 12, 18, 0.85) 0%, rgba(10, 12, 18, 0.96) 100%);
      pointer-events: none;
    }}
    .hero-content {{ position: relative; z-index: 1; width: 100%; max-width: 860px; }}
    .hero-badge {{
      display: inline-flex; align-items: center; gap: 6px;
      padding: 6px 16px; border-radius: 999px;
      background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.15);
      color: var(--accent); font-size: 13px; font-weight: 600; text-transform: uppercase;
      letter-spacing: .08em; margin-bottom: 20px;
    }}
    .hero-title {{
      font-size: 42px; font-weight: 800; color: #ffffff;
      line-height: 1.18; letter-spacing: -.03em; margin: 0 0 16px;
    }}
    .hero-body {{ font-size: 20px; color: #cbd5e1; margin-bottom: 32px; line-height: 1.5; }}
    .hero-footer {{
      display: flex; justify-content: space-between; align-items: center;
      border-top: 1px solid var(--line); padding-top: 20px;
      font-size: 13px; color: var(--muted);
    }}
    .hero-nav-hint {{ color: var(--accent); font-weight: 600; }}

    /* Deck Controls Bar */
    .controls {{
      display: flex; justify-content: space-between; align-items: center;
      padding: 14px 36px; border-top: 1px solid var(--line);
      background: rgba(14, 17, 24, 0.95); backdrop-filter: blur(12px);
      font-size: 13.5px; color: var(--muted); flex-shrink: 0;
    }}
    .controls-left {{ display: flex; align-items: center; gap: 12px; }}
    .controls-right {{ display: flex; align-items: center; gap: 8px; }}
    .btn-nav {{
      background: rgba(255, 255, 255, 0.06); border: 1px solid var(--line);
      color: var(--ink); padding: 7px 14px; border-radius: 8px;
      font: inherit; font-size: 13px; cursor: pointer; transition: all 0.15s ease;
      display: inline-flex; align-items: center; gap: 6px;
    }}
    .btn-nav:hover {{ background: rgba(255, 255, 255, 0.12); color: #ffffff; }}
    .btn-nav.primary {{ background: var(--accent); color: #0b0d13; font-weight: 600; border-color: transparent; }}
    .btn-nav.primary:hover {{ opacity: 0.9; }}
    @media (max-width: 800px) {{
      .split-grid {{ grid-template-columns: 1fr; }}
      .media-img {{ height: 180px; }}
      .slide, .hero-slide {{ padding: 24px; }}
    }}
    @media print {{
      body {{ height: auto; overflow: visible; background: #fff; }}
      .progress-bar, .controls {{ display: none !important; }}
      .deck-container {{ display: block; height: auto; overflow: visible; }}
      .slide,
      .slide:not(.active) {{
        display: flex !important;
        position: relative; inset: auto;
        width: 100%; height: auto; min-height: 100vh;
        margin: 0; overflow: visible;
        break-after: page; page-break-after: always;
        box-shadow: none;
      }}
    }}
  </style>
</head>
<body>
  <div class="progress-bar"><div class="progress-fill" id="progress-fill"></div></div>
  <div class="deck-container">
    {slides_rendered}
  </div>
  <div class="controls">
    <div class="controls-left">
      <strong>{safe_title}</strong>
      <span>(Use &larr; / &rarr; or Space)</span>
    </div>
    <div class="controls-right">
      <button type="button" class="btn-nav" id="prev-btn">&larr; Prev</button>
      <button type="button" class="btn-nav primary" id="next-btn">Next &rarr;</button>
      <button type="button" class="btn-nav" id="fullscreen-btn" title="Toggle Fullscreen">⛶</button>
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
      const fill = document.getElementById('progress-fill');
      if (fill) fill.style.width = ((cur / total) * 100) + '%';
    }}
    document.getElementById('prev-btn').onclick = () => show(cur - 1);
    document.getElementById('next-btn').onclick = () => show(cur + 1);
    document.getElementById('fullscreen-btn').onclick = () => {{
      if (!document.fullscreenElement) {{
        document.documentElement.requestFullscreen().catch(() => {{}});
      }} else {{
        document.exitFullscreen().catch(() => {{}});
      }}
    }};
    window.addEventListener('keydown', (e) => {{
      if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'PageDown') show(cur + 1);
      else if (e.key === 'ArrowLeft' || e.key === 'PageUp') show(cur - 1);
      else if (e.key === 'Home') show(1);
      else if (e.key === 'End') show(total);
    }});
    function initialSlide() {{
      const fromHash = (location.hash || "").match(/slide=(\\d+)/);
      if (fromHash) return parseInt(fromHash[1], 10) || 1;
      return 1;
    }}
    show(initialSlide());
    window.aiLabDeck = {{ current: function() {{ return cur; }}, show: show }};
  </script>
</body>
</html>"""


_MAX_DECK_CHARS = 80_000
_MAX_INSTRUCTION_CHARS = 4_000
_EDIT_INTENT = re.compile(
    r"\b(edit|change|update|rewrite|revise|shorten|expand|add|remove|delete|drop|rename|fix|replace|insert|move|tighten|cut|trim)\b",
    re.IGNORECASE,
)


def deck_title_from_markdown(markdown: str, fallback: str) -> str:
    for line in (markdown or "").splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip() or fallback
    return fallback or "AI Lab Presentation"


def _looks_like_deck(text: str) -> bool:
    body = (text or "").strip()
    if len(body) < 8 or len(body) > _MAX_DECK_CHARS:
        return False
    return body.startswith("#") or body.startswith("---") or "\n---" in body


def deck_edit_prompt(markdown: str, instruction: str, history: list[dict[str, str]] | None = None) -> str:
    """Ask the model to either revise the whole deck or answer without writing."""
    prior: list[str] = []
    for turn in (history or [])[-6:]:
        role = str(turn.get("role") or "").strip().lower()
        if role not in {"user", "assistant"}:
            continue
        content = " ".join(str(turn.get("content") or "").split())[:400]
        if content:
            prior.append(f"{role}: {content}")
    history_block = "\n".join(prior) if prior else "(none)"
    deck = (markdown or "").strip()[:_MAX_DECK_CHARS]
    request = " ".join((instruction or "").split())[:_MAX_INSTRUCTION_CHARS]
    return (
        "You are editing one slide deck. The slides the person is looking at are the markdown below.\n"
        "If they want any change, reply with exactly this shape and nothing else:\n"
        "EDIT\n"
        "<the full updated markdown for every slide. Separate slides with a line that contains only --->\n"
        "If they only asked a question, reply with exactly:\n"
        "ANSWER\n"
        "<a short answer>\n"
        "Do not wrap the reply in fences. Do not drop slides they did not ask to remove.\n\n"
        f"Earlier turns:\n{history_block}\n\n"
        f"DECK\n{deck}\nEND DECK\n\n"
        f"Request: {request}\n"
    )


def _strip_fence(text: str) -> str:
    match = re.match(r"^```(?:markdown|md)?\s*([\s\S]*?)\s*```$", (text or "").strip(), flags=re.IGNORECASE)
    return match.group(1).strip() if match else (text or "").strip()


def _labeled_section(text: str, label: str) -> str | None:
    """Read the body after a standalone EDIT or ANSWER line near the start of the reply."""
    for index, line in enumerate(text.splitlines()[:12]):
        if line.strip().rstrip(":").upper() == label:
            return "\n".join(text.splitlines()[index + 1 :]).strip()
    return None


def interpret_deck_reply(reply: str, *, instruction: str) -> tuple[str, str | None]:
    """Return the chat message and replacement markdown, or None when the deck stays as it is."""
    text = re.sub(r"<think>.*?</think>", "", reply or "", flags=re.DOTALL | re.IGNORECASE).strip()
    if text.startswith("```"):
        text = _strip_fence(text)

    edit = _labeled_section(text, "EDIT")
    if edit is not None:
        body = _strip_fence(edit)
        if _looks_like_deck(body):
            return ("Updated the slides. The page on the left is current.", body)
        return ("The edit did not include the full deck, so the slides were left unchanged.", None)

    answer = _labeled_section(text, "ANSWER")
    if answer is not None:
        message = _strip_fence(answer) or "No change."
        return (message, None)

    if _looks_like_deck(text) and _EDIT_INTENT.search(instruction or ""):
        return ("Updated the slides. The page on the left is current.", text)
    return (text or "No change.", None)


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

        # Save markdown without duplicate top-level title
        trimmed_body = body.lstrip()
        if trimmed_body.startswith(f"# {cleaned_title}") or (trimmed_body.startswith("# ") and "\n" in trimmed_body and cleaned_title.lower() in trimmed_body.splitlines()[0].lower()):
            md_text = f"{trimmed_body}\n"
        else:
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
