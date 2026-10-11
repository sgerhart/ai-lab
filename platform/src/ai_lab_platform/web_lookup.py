"""Read-only web lookup for the personal agent.

The model supplies a question. The lab searches Wikipedia and DuckDuckGo and
fetches one public page. The model does not choose the URL.
"""

from __future__ import annotations

from typing import Any, Callable

from .source_fetch import factual_query, fetch_page, search_pages, urls_in_text

_EXCERPT = 1_200


class WebLookupError(ValueError):
    """The question cannot be searched."""


def web_search(
    query: str,
    *,
    opener: Any = None,
    resolve: Callable[[str], list[str]] | None = None,
) -> str:
    text = " ".join((query or "").split())
    if not text:
        raise WebLookupError("query is empty")
    if len(text) > 240:
        raise WebLookupError("query is too long")
    if urls_in_text(text):
        return "web_search does not open a URL from the question. Ask in words."
    if not factual_query(text):
        return "web_search hits=0\nAsk a factual question."
    hits = search_pages(text, opener=opener, resolve=resolve, limit=1)
    if not hits:
        return f"web_search hits=0 query={text[:80]}"
    hit = hits[0]
    page = fetch_page(
        hit["url"],
        title=hit.get("title") or "",
        opener=opener,
        resolve=resolve,
        public=True,
        use_cache=opener is None,
    )
    lines = [f"web_search hits=1 query={text[:80]}", f"url: {page.url or hit['url']}"]
    if page.title or hit.get("title"):
        lines.append(f"title: {page.title or hit.get('title')}")
    if page.document_date:
        lines.append(f"document_date: {page.document_date}")
    if page.error:
        lines.append(f"error: {page.error}")
    else:
        excerpt = " ".join(page.text.split())[:_EXCERPT]
        lines.append(excerpt or "page had no text")
    return "\n".join(lines)


def research_pages(
    query: str,
    *,
    opener: Any = None,
    resolve: Callable[[str], list[str]] | None = None,
    limit: int = 5,
) -> tuple[str, list[dict[str, str]]]:
    """Several public pages for one question. The lab chooses the URLs."""
    text = " ".join((query or "").split())
    if not text:
        raise WebLookupError("query is empty")
    if len(text) > 240:
        raise WebLookupError("query is too long")
    if urls_in_text(text):
        return "research does not open a URL from the question. Ask in words.", []
    if not factual_query(text):
        return "research hits=0\nAsk a factual question.", []
    capped = max(1, min(int(limit), 5))
    hits = search_pages(text, opener=opener, resolve=resolve, limit=capped, wiki_limit=capped)
    sources: list[dict[str, str]] = []
    for hit in hits:
        page = fetch_page(
            hit["url"],
            title=hit.get("title") or "",
            opener=opener,
            resolve=resolve,
            public=True,
            use_cache=opener is None,
        )
        body = " ".join(page.text.split())[:6_000]
        sources.append(
            {
                "url": page.url or hit["url"],
                "title": page.title or hit.get("title") or "",
                "document_date": page.document_date or "",
                "excerpt": body[:700],
                "body": body,
                "error": page.error or "",
            }
        )
    if not sources:
        return f"research hits=0 query={text[:80]}", []
    lines = [f"research hits={len(sources)} query={text[:80]}"]
    for index, source in enumerate(sources, start=1):
        lines.append(f"{index}. {source['title'] or 'untitled'}")
        lines.append(f"url: {source['url']}")
        if source["document_date"]:
            lines.append(f"document_date: {source['document_date']}")
        if source["error"]:
            lines.append(f"error: {source['error']}")
        elif source["excerpt"]:
            lines.append(source["excerpt"])
        else:
            lines.append("page had no text")
    return "\n".join(lines), sources
