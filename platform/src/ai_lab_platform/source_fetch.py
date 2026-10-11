"""HTTPS fetch for chat sources.

User-pasted links stay on an exact host allowlist. A factual question is
looked up on Wikipedia and DuckDuckGo, then those result pages are fetched
when the address is public. Each redirect is checked again.
"""

from __future__ import annotations

import ipaddress
import json
import re
import socket
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote_plus, unquote, urljoin, urlsplit, urlunsplit
from urllib.request import OpenerDirector, Request, HTTPSHandler, HTTPHandler

_DATA = Path(__file__).resolve().parent / "data" / "fetch_allowlist.json"
_CATALOG = Path(__file__).resolve().parent / "data" / "source_catalog.json"
USER_AGENT = "ai-lab-harness/0.2 (local documentation fetch)"
MAX_BYTES = 500_000
TEXT_CAP = 200_000
TIMEOUT_S = 8
MAX_REDIRECTS = 3
CACHE_TTL_S = 3600
_REDIRECTS = {301, 302, 303, 307, 308}
_SENSITIVE_QUERY = {"token", "key", "api_key", "apikey", "password", "secret", "access_token"}
_HTML_TYPES = ("text/html", "application/xhtml", "application/xml", "text/xml")
_TEXT_TYPES = ("text/plain", "text/html", "application/xhtml", "application/xml", "text/xml")
_UPDATED_RE = re.compile(
    r"(?:updated|published|revised)\s*:\s*"
    r"([A-Z][a-z]+ \d{1,2}, \d{4}|\d{4}-\d{2}-\d{2})",
    re.I,
)
_DATE_PREF = (
    "article:modified_time",
    "og:updated_time",
    "last-modified",
    "date",
    "dc.date",
    "article:published_time",
)
_URL_RE = re.compile(r"https://[^\s<>\"']+", re.I)
_cache_lock = threading.Lock()
_cache: dict[str, tuple[float, "FetchedPage"]] = {}


class FetchDenied(Exception):
    """The URL is not safe to request."""


@dataclass
class FetchedPage:
    url: str
    title: str = ""
    text: str = ""
    document_date: str = ""
    date_kind: str = ""
    fetched_at: str = ""
    error: str = ""
    truncated: bool = False

    @property
    def ok(self) -> bool:
        return bool(self.text) and not self.error


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_allowlist(path: Path | None = None) -> set[str]:
    raw = json.loads((path or _DATA).read_text(encoding="utf-8"))
    hosts = raw.get("hosts") if isinstance(raw, dict) else None
    if not isinstance(hosts, list):
        return set()
    return {str(host).strip().lower().rstrip(".") for host in hosts if str(host).strip()}


def load_catalog(path: Path | None = None) -> list[dict[str, Any]]:
    raw = json.loads((path or _CATALOG).read_text(encoding="utf-8"))
    rows = raw.get("entries") if isinstance(raw, dict) else None
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict) and row.get("url")]


def urls_in_text(text: str) -> list[str]:
    found: list[str] = []
    for match in _URL_RE.finditer(text or ""):
        url = match.group(0).rstrip(").,;]>\"'")
        if url not in found:
            found.append(url)
    return found


def _has_word(text: str, word: str) -> bool:
    return re.search(rf"\b{re.escape(word)}\b", text or "", re.I) is not None


def catalog_urls(query: str, *, catalog: list[dict[str, Any]] | None = None) -> list[dict[str, str]]:
    """Pinned pages whose required words appear in the question."""
    hits: list[dict[str, str]] = []
    for row in catalog if catalog is not None else load_catalog():
        require = [str(w) for w in (row.get("require_any") or []) if str(w).strip()]
        also = [str(w) for w in (row.get("also_any") or []) if str(w).strip()]
        if require and not any(_has_word(query, word) for word in require):
            continue
        if also and not any(_has_word(query, word) for word in also):
            continue
        if not require and not also:
            continue
        url = str(row.get("url") or "").strip()
        if not url:
            continue
        hits.append({"url": url, "title": str(row.get("title") or "").strip()})
    return hits


_FACT_RE = re.compile(
    r"\b(what|which|who|when|where|why|how|list|define|compare|supported|support|"
    r"number of|how many|how long|how much|explain|describe)\b|\?",
    re.I,
)
_GREETING_RE = re.compile(
    r"^(hi|hello|hey|thanks|thank you|ok|okay|yes|no|good morning|good night)[.!]?$",
    re.I,
)
_SEARCH_HOSTS = {"en.wikipedia.org", "html.duckduckgo.com", "duckduckgo.com"}
_UDDG_RE = re.compile(r"[?&]uddg=([^&\"']+)", re.I)


def factual_query(text: str) -> bool:
    """A question the local model would have to recall or guess."""
    query = " ".join((text or "").split())
    if len(query) < 12 or _GREETING_RE.match(query):
        return False
    return bool(_FACT_RE.search(query))


def needs_source_fetch(query: str) -> bool:
    return bool(urls_in_text(query) or catalog_urls(query) or factual_query(query))


def validate_https_url(
    url: str,
    *,
    allowlist: set[str] | None = None,
    public: bool = False,
) -> str:
    """Return a canonical https URL or raise FetchDenied."""
    text = (url or "").strip()
    if not text or any(ch in text for ch in "\r\n\t "):
        raise FetchDenied("URL is empty or contains spaces")
    parts = urlsplit(text)
    if parts.scheme.lower() != "https":
        raise FetchDenied("only https URLs can be fetched")
    if parts.username or parts.password:
        raise FetchDenied("URLs with a username or password are refused")
    host = (parts.hostname or "").lower().rstrip(".")
    if not host:
        raise FetchDenied("URL has no host")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise FetchDenied("IP addresses are not allowlisted")
    if parts.port not in (None, 443):
        raise FetchDenied("only port 443 is allowed")
    if not public:
        hosts = allowlist if allowlist is not None else load_allowlist()
        if host not in hosts:
            raise FetchDenied(f"{host} is not on the fetch allowlist")
    for key in parse_qs(parts.query, keep_blank_values=True):
        if key.lower() in _SENSITIVE_QUERY:
            raise FetchDenied("URL query looks like a credential")
    netloc = host if parts.port in (None, 443) else f"{host}:443"
    return urlunsplit(("https", netloc, parts.path or "/", parts.query, ""))


def _public_addresses(host: str, resolve: Callable[[str], list[str]] | None) -> None:
    if resolve is not None:
        addresses = list(resolve(host))
    else:
        prev = socket.getdefaulttimeout()
        socket.setdefaulttimeout(5)
        try:
            infos = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
        except socket.gaierror as exc:
            raise FetchDenied("host did not resolve") from exc
        finally:
            socket.setdefaulttimeout(prev)
        addresses = [item[4][0] for item in infos]
    if not addresses:
        raise FetchDenied("host did not resolve")
    for raw in addresses:
        try:
            ip = ipaddress.ip_address(raw)
        except ValueError as exc:
            raise FetchDenied("host resolved to an unreadable address") from exc
        if not ip.is_global:
            raise FetchDenied("host resolved to an address that is not public")


def _normalize_date(raw: str) -> str:
    text = " ".join((raw or "").split())
    match = re.match(r"(\d{4}-\d{2}-\d{2})", text)
    if match:
        return match.group(1)
    for fmt in ("%B %d, %Y", "%b %d, %Y", "%d %B %Y", "%d %b %Y"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    return ""


class _PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.meta: list[tuple[str, str]] = []
        self.times: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        ad = {key.lower(): (value or "") for key, value in attrs}
        if tag in {"script", "style", "noscript", "svg"}:
            self._skip += 1
        if tag == "meta":
            prop = (ad.get("property") or ad.get("name") or ad.get("itemprop") or "").lower()
            content = ad.get("content") or ""
            if prop and content:
                self.meta.append((prop, content))
        if tag == "time" and ad.get("datetime"):
            self.times.append(ad["datetime"])
        if tag in {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "section"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg"} and self._skip:
            self._skip -= 1

    def handle_data(self, data: str) -> None:
        if self._skip:
            return
        self.parts.append(data)


def _document_date(parser: _PageParser, text: str) -> tuple[str, str]:
    by_prop = {prop: value for prop, value in parser.meta}
    for prop in _DATE_PREF:
        found = _normalize_date(by_prop.get(prop, ""))
        if found:
            return found, "document"
    for raw in parser.times:
        found = _normalize_date(raw)
        if found:
            return found, "document"
    match = _UPDATED_RE.search(text)
    if match:
        found = _normalize_date(match.group(1))
        if found:
            return found, "document"
    return "", ""


def html_to_text(raw: str) -> tuple[str, str, str]:
    parser = _PageParser()
    parser.feed(raw)
    parser.close()
    text = re.sub(r"\n{3,}", "\n\n", "".join(parser.parts))
    text = "\n".join(line.rstrip() for line in text.splitlines()).strip()
    if len(text) > TEXT_CAP:
        text = text[:TEXT_CAP]
    date, kind = _document_date(parser, text)
    return text, date, kind


def _header_date(headers: Any) -> str:
    raw = ""
    if headers is not None:
        getter = getattr(headers, "get", None)
        raw = getter("Last-Modified") if callable(getter) else ""
    if not raw:
        return ""
    try:
        parsed = parsedate_to_datetime(str(raw))
    except (TypeError, ValueError, IndexError):
        return ""
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).date().isoformat()


def _default_opener() -> OpenerDirector:
    opener = OpenerDirector()
    opener.add_handler(HTTPHandler())
    opener.add_handler(HTTPSHandler())
    return opener


def _headers_of(resp: Any) -> Any:
    headers = getattr(resp, "headers", None)
    if headers is None:
        info = getattr(resp, "info", None)
        headers = info() if callable(info) else {}
    return headers


def _status_of(resp: Any) -> int:
    for name in ("status", "code"):
        value = getattr(resp, name, None)
        if isinstance(value, int):
            return value
    getter = getattr(resp, "getcode", None)
    if callable(getter):
        try:
            value = getter()
        except (TypeError, ValueError):
            return 0
        if isinstance(value, int):
            return value
    return 0


def _close(resp: Any) -> None:
    close = getattr(resp, "close", None)
    if callable(close):
        close()


def _next_url(
    current: str,
    location: str,
    allowlist: set[str] | None,
    *,
    public: bool = False,
) -> tuple[str, str]:
    if not location:
        return current, "redirect had no location"
    try:
        return validate_https_url(urljoin(current, location), allowlist=allowlist, public=public), ""
    except FetchDenied as exc:
        return current, str(exc)


def fetch_page(
    url: str,
    *,
    title: str = "",
    opener: Any = None,
    resolve: Callable[[str], list[str]] | None = None,
    allowlist: set[str] | None = None,
    use_cache: bool = True,
    now: str = "",
    public: bool = False,
) -> FetchedPage:
    """Fetch one page. User links stay on the host allowlist. Search results may be any public https host."""
    fetched_at = now or utc_now()
    try:
        current = validate_https_url(url, allowlist=allowlist, public=public)
    except FetchDenied as exc:
        return FetchedPage(url=url, title=title, fetched_at=fetched_at, error=str(exc))

    if use_cache:
        with _cache_lock:
            hit = _cache.get(current)
        if hit is not None and (datetime.now(timezone.utc).timestamp() - hit[0]) < CACHE_TTL_S:
            cached = hit[1]
            return FetchedPage(
                url=cached.url,
                title=title or cached.title,
                text=cached.text,
                document_date=cached.document_date,
                date_kind=cached.date_kind,
                fetched_at=cached.fetched_at,
                truncated=cached.truncated,
            )

    client = opener or _default_opener()
    hops = 0
    while True:
        parts = urlsplit(current)
        try:
            _public_addresses(parts.hostname or "", resolve)
        except FetchDenied as exc:
            return FetchedPage(url=current, title=title, fetched_at=fetched_at, error=str(exc))
        req = Request(
            current,
            headers={"User-Agent": USER_AGENT, "Accept": "text/html,text/plain;q=0.9"},
            method="GET",
        )
        try:
            resp = client.open(req, timeout=TIMEOUT_S)
        except HTTPError as exc:
            if exc.code in _REDIRECTS and hops < MAX_REDIRECTS:
                location = exc.headers.get("Location") if exc.headers else ""
                nxt, err = _next_url(current, location, allowlist, public=public)
                if err:
                    return FetchedPage(url=current, title=title, fetched_at=fetched_at, error=err)
                current = nxt
                hops += 1
                continue
            return FetchedPage(
                url=current,
                title=title,
                fetched_at=fetched_at,
                error=f"fetch failed ({exc.code})",
            )
        except (URLError, TimeoutError, OSError):
            return FetchedPage(url=current, title=title, fetched_at=fetched_at, error="fetch failed")
        headers = _headers_of(resp)
        code = _status_of(resp)
        if code in _REDIRECTS and hops < MAX_REDIRECTS:
            location = headers.get("Location") if hasattr(headers, "get") else ""
            _close(resp)
            nxt, err = _next_url(current, location, allowlist, public=public)
            if err:
                return FetchedPage(url=current, title=title, fetched_at=fetched_at, error=err)
            current = nxt
            hops += 1
            continue
        if code and not 200 <= code < 300:
            _close(resp)
            return FetchedPage(url=current, title=title, fetched_at=fetched_at, error=f"fetch failed ({code})")
        try:
            body = resp.read(MAX_BYTES + 1)
            final = resp.geturl() if hasattr(resp, "geturl") else ""
        finally:
            _close(resp)
        if final:
            try:
                current = validate_https_url(final, allowlist=allowlist, public=public)
            except FetchDenied as exc:
                return FetchedPage(url=final, title=title, fetched_at=fetched_at, error=str(exc))
        break

    truncated = len(body) > MAX_BYTES
    raw = body[:MAX_BYTES]
    if b"\x00" in raw[:512]:
        return FetchedPage(url=current, title=title, fetched_at=fetched_at, error="response was not text")
    ctype = ""
    if headers is not None and hasattr(headers, "get"):
        ctype = str(headers.get("Content-Type") or "").split(";")[0].strip().lower()
    if ctype and not ctype.startswith(_TEXT_TYPES):
        return FetchedPage(url=current, title=title, fetched_at=fetched_at, error="unsupported content type")
    decoded = raw.decode("utf-8", errors="replace")
    if not ctype or ctype.startswith(_HTML_TYPES):
        text, doc_date, kind = html_to_text(decoded)
    else:
        text, doc_date, kind = decoded.strip()[:TEXT_CAP], "", ""
    if not doc_date:
        header_date = _header_date(headers)
        if header_date:
            doc_date, kind = header_date, "http-last-modified"
    if not text:
        return FetchedPage(url=current, title=title, fetched_at=fetched_at, error="page had no text")
    page = FetchedPage(
        url=current,
        title=title,
        text=text,
        document_date=doc_date,
        date_kind=kind,
        fetched_at=fetched_at,
        truncated=truncated,
    )
    if use_cache:
        with _cache_lock:
            _cache[current] = (datetime.now(timezone.utc).timestamp(), page)
    return page


def clear_fetch_cache() -> None:
    with _cache_lock:
        _cache.clear()


def _fetch_raw(
    url: str,
    *,
    hosts: set[str],
    opener: Any = None,
    resolve: Callable[[str], list[str]] | None = None,
) -> str:
    """GET one search endpoint. The host must be one of ``hosts``."""
    try:
        current = validate_https_url(url, allowlist=hosts)
    except FetchDenied:
        return ""
    try:
        _public_addresses(urlsplit(current).hostname or "", resolve)
    except FetchDenied:
        return ""
    client = opener or _default_opener()
    req = Request(
        current,
        headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/json;q=0.9"},
        method="GET",
    )
    try:
        resp = client.open(req, timeout=TIMEOUT_S)
    except (HTTPError, URLError, TimeoutError, OSError):
        return ""
    try:
        code = _status_of(resp)
        if code and not 200 <= code < 300:
            return ""
        body = resp.read(MAX_BYTES + 1)[:MAX_BYTES]
    finally:
        _close(resp)
    if b"\x00" in body[:512]:
        return ""
    return body.decode("utf-8", errors="replace")


def _wikipedia_hits(
    query: str,
    *,
    opener: Any,
    resolve: Callable[[str], list[str]] | None,
    limit: int = 1,
) -> list[dict[str, str]]:
    capped = max(1, min(int(limit), 5))
    url = (
        "https://en.wikipedia.org/w/api.php?action=opensearch&limit="
        + str(capped)
        + "&namespace=0&format=json&search="
        + quote_plus(query[:240])
    )
    raw = _fetch_raw(url, hosts=_SEARCH_HOSTS, opener=opener, resolve=resolve)
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list) or len(parsed) < 4:
        return []
    titles = parsed[1] if isinstance(parsed[1], list) else []
    links = parsed[3] if isinstance(parsed[3], list) else []
    hits: list[dict[str, str]] = []
    for title, link in zip(titles, links, strict=False):
        if isinstance(link, str) and link.startswith("https://"):
            hits.append({"url": link, "title": str(title or "")})
    return hits


def _unwrap_ddg(href: str) -> str:
    text = (href or "").replace("&amp;", "&")
    if text.startswith("//"):
        text = "https:" + text
    match = _UDDG_RE.search(text)
    if match:
        return unquote(match.group(1))
    if "duckduckgo.com" in text:
        return ""
    return text


def _ddg_hits(query: str, *, opener: Any, resolve: Callable[[str], list[str]] | None) -> list[dict[str, str]]:
    url = "https://html.duckduckgo.com/html/?q=" + quote_plus(query[:240])
    raw = _fetch_raw(url, hosts=_SEARCH_HOSTS, opener=opener, resolve=resolve)
    hits: list[dict[str, str]] = []
    for match in re.finditer(r'class="result__a"[^>]*href="([^"]+)"', raw or "", re.I):
        link = _unwrap_ddg(match.group(1))
        if link.startswith("https://"):
            hits.append({"url": link, "title": ""})
    return hits


def search_pages(
    query: str,
    *,
    opener: Any = None,
    resolve: Callable[[str], list[str]] | None = None,
    limit: int = 2,
    wiki_limit: int = 1,
) -> list[dict[str, str]]:
    """Public pages for a factual question. The model does not choose the URLs."""
    text = " ".join((query or "").split())
    if not factual_query(text):
        return []
    found: list[dict[str, str]] = []
    seen: set[str] = set()
    hits = _wikipedia_hits(text, opener=opener, resolve=resolve, limit=wiki_limit)
    hits.extend(_ddg_hits(text, opener=opener, resolve=resolve))
    for row in hits:
        try:
            url = validate_https_url(row["url"], public=True)
        except FetchDenied:
            continue
        host = (urlsplit(url).hostname or "").lower()
        if host == "duckduckgo.com" or host.endswith(".duckduckgo.com"):
            continue
        if url in seen:
            continue
        seen.add(url)
        found.append({"url": url, "title": row.get("title") or ""})
        if len(found) >= limit:
            break
    return found
