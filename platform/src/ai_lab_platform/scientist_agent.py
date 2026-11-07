"""Staff Scientist (Lab Manager / Research Partner) peer agent (IWO-129).

Engages with the human operator in back-and-forth scientific dialogue,
equipped with tools to search the operator's 192 local books in Knowledge Nexus
or conduct live web research for external literature and benchmarks.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from .lab_workbench import get_concept
from .nexus_study import find_nexus_root


def search_nexus_books(query: str, limit: int = 3) -> list[dict[str, str]]:
    """Search the operator's 192 local books and papers in Knowledge Nexus.

    Queries disk-books.json and Qdrant/fastembed embeddings when available.
    """
    q = (query or "").strip().lower()
    if not q:
        return []

    hits: list[dict[str, str]] = []
    nexus_root = find_nexus_root()

    # 1. Search disk-books metadata
    catalog_path = nexus_root / "disk-books.json" if nexus_root else None
    if catalog_path and catalog_path.exists():
        try:
            data = json.loads(catalog_path.read_text(encoding="utf-8"))
            for book in data.get("books", []):
                title = book.get("title", "")
                cat = book.get("category", "")
                rel_path = book.get("relative_path", "")
                blob = f"{title} {cat} {rel_path}".lower()
                if any(word in blob for word in q.split() if len(word) > 2):
                    hits.append(
                        {
                            "source": "nexus_library",
                            "title": title,
                            "category": cat,
                            "reference": rel_path,
                            "snippet": f"Book in local library: '{title}' ({cat}). Direct study path: {rel_path}",
                        }
                    )
                    if len(hits) >= limit:
                        return hits
        except Exception:
            pass

    # 2. Try Qdrant semantic search if available
    try:
        from .nexus_rag import search_books_qdrant

        qdrant_results = search_books_qdrant(query, limit=limit)
        for r in qdrant_results:
            hits.append(
                {
                    "source": "nexus_rag",
                    "title": r.get("title", "Unknown Book"),
                    "category": r.get("category", "ai-books"),
                    "reference": r.get("reference", ""),
                    "snippet": r.get("text", "")[:300],
                }
            )
            if len(hits) >= limit:
                return hits
    except Exception:
        pass

    return hits[:limit]


def search_web_literature(query: str) -> list[dict[str, str]]:
    """Search public literature via the bounded web lookup tool."""
    q = (query or "").strip()
    if not q:
        return []

    try:
        from .web_lookup import web_search

        result = web_search(q)
        return [
            {
                "source": "web_literature",
                "title": f"Web Research: {q[:60]}",
                "snippet": result[:500],
            }
        ]
    except Exception as exc:
        return [
            {
                "source": "web_literature",
                "title": f"Web Lookup ({q[:40]})",
                "snippet": f"Web search note: {exc}",
            }
        ]


SCIENTIST_SYSTEM_PROMPT = """You are the Staff Scientist and Lab Manager for the AI Lab.
You work alongside the human operator as a fellow scientist and research partner at the laboratory bench.

Your Persona:
- You are collegial, sharp, deeply curious, mathematically rigorous, and communicative.
- This is an active back-and-forth dialogue between two peer researchers. You do not talk down to the operator, nor do you act like a subservient voice assistant.
- You treat complex AI concepts (Transformers, Diffusion, ViT, GRPO, RoPE, Attention variance) with complete clarity: plain-English intuition first, then exact mathematical derivations with real numbers, followed by practical Python/PyTorch verification snippets.
- You have direct access to the operator's personal library of 192 books and research papers in Knowledge Nexus, as well as live web search for recent papers.
- When an operator asks a question, cite the relevant books in the library or external papers, explain the mechanics, and offer to run a quick test together.
"""


def scientist_chat(
    message: str,
    *,
    concept_id: str | None = None,
    history: list[dict[str, str]] | None = None,
    complete_fn: Callable[[str], str] | None = None,
) -> dict[str, Any]:
    """Process a dialogue turn with the Staff Scientist.

    Args:
        message: The user's query or hypothesis.
        concept_id: Optional active concept slug from the laboratory workbench.
        history: Prior conversation turns [{'role': 'user'|'scientist', 'content': '...'}].
        complete_fn: Optional LLM completion callable. If None, deterministic scientist synthesis is used.

    Returns:
        dict with 'reply', 'citations', 'concept', and 'tools_used'.
    """
    user_msg = (message or "").strip()
    active_concept = get_concept(concept_id) if concept_id else None
    citations: list[dict[str, str]] = []
    tools_used: list[str] = []

    # 1. Determine tool needs
    msg_lower = user_msg.lower()
    needs_library = any(k in msg_lower for k in ["book", "library", "nexus", "paper", "read", "cite", "literature"])
    needs_web = any(k in msg_lower for k in ["internet", "web", "arxiv", "recent", "latest", "benchmark", "search"])

    # If active concept has citations, include them
    if active_concept and active_concept.get("nexus_citations"):
        for c in active_concept["nexus_citations"]:
            citations.append(
                {
                    "source": "concept_curated",
                    "title": c.get("title", ""),
                    "chapter": c.get("chapter", ""),
                    "category": c.get("category", ""),
                    "snippet": c.get("relevance", ""),
                }
            )

    # Perform library search if requested or if relevant query
    if needs_library or ("how" in msg_lower and len(citations) == 0):
        search_q = user_msg if len(user_msg) < 80 else (active_concept["title"] if active_concept else user_msg[:80])
        lib_hits = search_nexus_books(search_q)
        if lib_hits:
            tools_used.append("search_nexus_books")
            citations.extend(lib_hits)

    # Perform web research if requested
    if needs_web:
        web_hits = search_web_literature(user_msg[:120])
        if web_hits:
            tools_used.append("search_web")
            citations.extend(web_hits)

    # If an LLM completion function is provided, call it with prompt context
    if complete_fn is not None:
        prompt_lines = [
            SCIENTIST_SYSTEM_PROMPT,
            "",
            f"Active Workbench Concept: {active_concept['title'] if active_concept else 'General Lab Workbench'}",
        ]
        if active_concept:
            prompt_lines.append(f"Formula: {active_concept.get('formula', '')}")
            prompt_lines.append(f"Math Explanation: {active_concept.get('math_explanation', '')}")
            prompt_lines.append(f"Numerical Intuition: {active_concept.get('numerical_example', '')}")

        if citations:
            prompt_lines.append("\nRelevant Library / Web Citations:")
            for cit in citations[:4]:
                prompt_lines.append(f"- {cit.get('title')}: {cit.get('chapter', cit.get('snippet', ''))}")

        if history:
            prompt_lines.append("\nRecent Dialogue:")
            for h in history[-4:]:
                prompt_lines.append(f"{h.get('role', 'user').title()}: {h.get('content', '')}")

        prompt_lines.append(f"\nOperator: {user_msg}\nStaff Scientist:")
        full_prompt = "\n".join(prompt_lines)

        try:
            raw_reply = complete_fn(full_prompt)
            if raw_reply and raw_reply.strip():
                return {
                    "reply": raw_reply.strip(),
                    "citations": citations,
                    "tools_used": tools_used,
                    "concept": active_concept["id"] if active_concept else None,
                }
        except Exception:
            pass

    # Deterministic high-quality peer scientist synthesis (fallback / test mode)
    reply_parts = []
    if active_concept:
        title = active_concept["title"]
        reply_parts.append(
            f"Great question. Let's look at **{title}** from first principles at the bench."
        )
        if any(w in msg_lower for w in ["math", "variance", "proof", "why", "derive", "number"]):
            reply_parts.append(
                f"\n\n**The Core Mathematical Rationale:**\n{active_concept['math_explanation']}"
            )
            reply_parts.append(
                f"\n\n**Numerical Intuition:**\n{active_concept['numerical_example']}"
            )
        elif any(w in msg_lower for w in ["code", "tensor", "shape", "test", "run", "verify"]):
            reply_parts.append(
                f"\n\n**Tensor Flow Schematic:**\n```\n{active_concept['tensor_flow']}\n```"
            )
            reply_parts.append(
                f"\n\n**Verification Snippet:**\n```python\n{active_concept['code_snippet']}\n```"
            )
        else:
            reply_parts.append(
                f"\n\n{active_concept['summary']}"
            )
            reply_parts.append(
                f"\n\n$$\n{active_concept['formula']}\n$$\n"
            )
            reply_parts.append(
                f"\n\n**How it works in practice:** {active_concept['math_explanation']}"
            )

        if citations:
            reply_parts.append("\n\n**Grounded Citations From Our Library:**")
            for cit in citations[:3]:
                chap = f" ({cit['chapter']})" if "chapter" in cit else ""
                reply_parts.append(f"- **{cit['title']}**{chap}: {cit.get('snippet', '')}")
    else:
        reply_parts.append(
            f"Let's investigate '{user_msg}' together in the lab."
        )
        if citations:
            reply_parts.append("\n\nHere is what our research tools found in the library and literature:")
            for cit in citations[:3]:
                chap = f" ({cit['chapter']})" if "chapter" in cit else ""
                reply_parts.append(f"- **{cit['title']}**{chap}: {cit.get('snippet', '')}")
        else:
            reply_parts.append(
                "\n\nWe can explore any paradigm on the workbench—Language, Vision, Diffusion, Audio, or RL. "
                "Pick an architecture or ask about any equation, and we can derive the math and test the tensors together."
            )

    return {
        "reply": "\n".join(reply_parts),
        "citations": citations,
        "tools_used": tools_used,
        "concept": active_concept["id"] if active_concept else None,
    }

