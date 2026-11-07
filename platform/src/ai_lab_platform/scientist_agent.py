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


SCIENTIST_SYSTEM_PROMPT = """You are the Staff Scientist, Lab Manager, and Master Educator for the AI Lab.
You work alongside the human operator as a supportive research partner and intuitive teacher at the laboratory bench in an active back-and-forth dialogue.

Your Core Pedagogical Philosophy:
- Always assume the user wants crystal-clear, intuitive understanding first. Never intimidate with unexplained jargon or raw equations.
- Teach someone who knows NOTHING about the topic using the "Concrete -> Abstract" method:
  1. Everyday Analogy: Start with a real-world physical scenario (e.g. GPS navigation, shopping lists, seesaws, spotlight shadows, camera lenses).
  2. Concrete Arithmetic: Use simple numbers (3, 2, 1) to show how it calculates by hand before showing abstract symbols.
  3. The "Why": Explain the dilemma or problem that forced mathematicians or AI engineers to invent this.
  4. The AI Connection: Explain exactly how ChatGPT, PyTorch, or embeddings use this concept in practice.
- Never output raw JSON objects in dialogue. Always reply in clean, readable, beautifully formatted Markdown with headers, bold key terms, and bullet points.
- Check in warmly: Ask the user a friendly follow-up question or offer to test an example together.
- You have direct access to the operator's personal library of 192 books and research papers in Knowledge Nexus. Ground your explanations in these books (e.g. Essential Math for Data Science, Mathematics for Machine Learning).
"""


def _clean_scientist_reply(raw: str) -> str:
    """Format raw model output, converting any JSON-structured payloads into rich Markdown."""
    cleaned = (raw or "").strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            parts = []
            title = data.get("title")
            if title:
                parts.append("### " + str(title) + "\n")
            fig = data.get("figure_description") or data.get("figure_caption")
            if fig:
                parts.append("> 💡 **Intuitive Picture:** " + str(fig) + "\n")
            lines = data.get("text_lines")
            if lines and isinstance(lines, list):
                for line in lines:
                    parts.append(str(line) + "\n")
            tbl = data.get("table")
            if tbl and isinstance(tbl, dict):
                headers = tbl.get("headers")
                if not headers:
                    c1 = tbl.get("col1_header")
                    c2 = tbl.get("col2_header")
                    if c1 and c2:
                        headers = [c1, c2]
                    elif isinstance(tbl.get("columns"), list):
                        headers = tbl.get("columns")
                rows = tbl.get("rows", [])
                if headers and rows:
                    parts.append("| " + " | ".join(str(h) for h in headers) + " |")
                    parts.append("| " + " | ".join(["---"] * len(headers)) + " |")
                    for row in rows:
                        if isinstance(row, list):
                            parts.append("| " + " | ".join(str(c) for c in row) + " |")
                        elif isinstance(row, dict):
                            parts.append("| " + " | ".join(str(v) for v in row.values()) + " |")
                    parts.append("")
            if data.get("code"):
                parts.append("```python\n" + str(data["code"]) + "\n```\n")
            if parts:
                return "\n".join(parts).strip()
    except Exception:
        pass
    return (raw or "").strip()


def scientist_complete(router: Any, prompt: str, system: str = "") -> str:
    """Ask the local model using the Staff Scientist master educator persona."""
    from .agent_builder import interviewer_model
    from .model_router import CompletionRequest

    providers = router.list_providers()
    ollama = next((row for row in providers if row.get("id") == "ollama"), None)
    installed = [str(name) for name in ((ollama or {}).get("models") or []) if name]
    enabled = bool((ollama or {}).get("enabled"))
    if enabled and installed:
        backend = "ollama"
        model = interviewer_model(installed)
    else:
        backend = "fake"
        model = "fake-instruct"

    done = router.complete(
        CompletionRequest(
            model=model,
            prompt=prompt,
            backend=backend,
            system=system or SCIENTIST_SYSTEM_PROMPT,
        )
    )
    return str(done.text or "")


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
            prompt_lines.append(f"Summary: {active_concept.get('summary', '')}")
            prompt_lines.append(f"Intuition: {active_concept.get('intuition', '')}")
            prompt_lines.append(f"Formula: {active_concept.get('formula', '')}")
            prompt_lines.append(f"Math Explanation: {active_concept.get('math_explanation', '')}")
            prompt_lines.append(f"Numerical Intuition: {active_concept.get('numerical_example', '')}")
            prompt_lines.append(f"AI Connection: {active_concept.get('ai_connection', '')}")

        if citations:
            prompt_lines.append("\nRelevant Library / Web Citations:")
            for cit in citations[:4]:
                prompt_lines.append(f"- {cit.get('title')}: {cit.get('chapter', cit.get('snippet', ''))}")

        if history:
            prompt_lines.append("\nRecent Dialogue:")
            for h in history[-4:]:
                prompt_lines.append(f"{h.get('role', 'user').title()}: {h.get('content', '')}")

        prompt_lines.append(
            f"\nOperator: {user_msg}\n"
            f"Staff Scientist (Reply in clean, beginner-friendly Markdown with intuitive analogies and clear steps. Do NOT output raw JSON):"
        )
        full_prompt = "\n".join(prompt_lines)

        try:
            raw_reply = complete_fn(full_prompt)
            if raw_reply and raw_reply.strip():
                clean_reply = _clean_scientist_reply(raw_reply)
                return {
                    "reply": clean_reply,
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
            f"Welcome to the bench! Let's explore **{title}** together from the ground up."
        )

        # 1. Beginner / ELI5 / Analogy query
        if any(w in msg_lower for w in ["eli5", "beginner", "analogy", "simple", "nothing", "everyday", "explain like"]):
            reply_parts.append(
                f"\n\n### 💡 The Big Picture (No Math Required)\n"
                f"{active_concept.get('intuition', active_concept['summary'])}\n\n"
                f"**The Takeaway:** You don't need calculus to master this. In daily life, we use this exact logic all the time. "
                f"Once you see the physical picture, the mathematical symbols are just shorthand notes."
            )
            if active_concept.get("ai_connection"):
                reply_parts.append(
                    f"\n\n### 🤖 Why AI Needs This\n{active_concept['ai_connection']}"
                )
            reply_parts.append(
                "\n\n*Does this visual picture make sense so far, or would you like another everyday example?*"
            )

        # 2. Interactive Quiz query
        elif any(w in msg_lower for w in ["quiz", "test", "question", "check"]):
            reply_parts.append(
                f"\n\n### 🎯 Quick Concept Check: {title}\n"
                f"Here is a friendly 1-question check to test your intuition:\n\n"
                f"**Question:** If you have an arrow pointing East with length 3, and you multiply it by -1, what happens?\n\n"
                f"- **A)** It becomes 3 times longer pointing North.\n"
                f"- **B)** It flips 180° to point West with length 3.\n"
                f"- **C)** It disappears into zero length.\n\n"
                f"*Reply with your guess (A, B, or C), and let's verify why!*"
            )

        # 3. AI / LLM connection query
        elif any(w in msg_lower for w in ["ai", "chatgpt", "llm", "neural", "pytorch", "use"]):
            reply_parts.append(
                f"\n\n### ⚡ How This Operates in Modern AI\n"
                f"{active_concept.get('ai_connection', 'Fundamental building block of representation learning.')}\n\n"
                f"**In PyTorch code:**\n```python\n{active_concept['code_snippet']}\n```"
            )

        # 4. Math / Proof / Derivation query
        elif any(w in msg_lower for w in ["math", "variance", "proof", "why", "derive", "number"]):
            reply_parts.append(
                f"\n\n### 📐 The Mathematical Mechanics\n"
                f"$$\n{active_concept['formula']}\n$$\n\n"
                f"{active_concept['math_explanation']}\n\n"
                f"### 🔢 Real-Number Walkthrough\n"
                f"{active_concept['numerical_example']}"
            )

        # 5. Code / Tensor query
        elif any(w in msg_lower for w in ["code", "tensor", "shape", "run", "verify"]):
            reply_parts.append(
                f"\n\n### 🏗️ Tensor Flow\n```\n{active_concept['tensor_flow']}\n```\n\n"
                f"### 🧪 Runnable PyTorch Snippet\n```python\n{active_concept['code_snippet']}\n```"
            )

        # 6. Default general overview
        else:
            reply_parts.append(
                f"\n\n### 💡 The Core Mental Model\n"
                f"{active_concept.get('intuition', active_concept['summary'])}\n\n"
                f"### 📐 The Formula\n"
                f"$$\n{active_concept['formula']}\n$$\n\n"
                f"### ⚡ Why It Matters in AI\n"
                f"{active_concept.get('ai_connection', active_concept['math_explanation'])}"
            )

        if citations:
            reply_parts.append("\n\n**📚 Grounded Citations in Your Nexus Library:**")
            for cit in citations[:3]:
                chap = f" ({cit['chapter']})" if "chapter" in cit else ""
                reply_parts.append(f"- **{cit['title']}**{chap}: {cit.get('snippet', '')}")
    else:
        reply_parts.append(
            f"Let's investigate '{user_msg}' together at the bench."
        )
        if citations:
            reply_parts.append("\n\nHere is what our research tools found in the library and literature:")
            for cit in citations[:3]:
                chap = f" ({cit['chapter']})" if "chapter" in cit else ""
                reply_parts.append(f"- **{cit['title']}**{chap}: {cit.get('snippet', '')}")
        else:
            reply_parts.append(
                "\n\nWe can explore any paradigm on the workbench—from basic Linear Algebra and Statistics to Language, Vision, and RL. "
                "Pick an item on the left, or ask me to explain any concept like you're completely new to it!"
            )

    return {
        "reply": "\n".join(reply_parts),
        "citations": citations,
        "tools_used": tools_used,
        "concept": active_concept["id"] if active_concept else None,
    }

