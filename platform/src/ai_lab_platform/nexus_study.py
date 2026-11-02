"""Nexus Study Book Search & Grounding Engine.

Extracts real chapter text and excerpts from books stored in Nexus (~/.ai-lab/nexus).
Supports both EPUB (clean chapter HTML) and PDF formats.
"""

from __future__ import annotations

import os
import re
import zipfile
from pathlib import Path
from typing import Any

from .attachments import pdf_text

# Words a run-on filename may be split into. Short fragments are omitted on
# purpose so "networks" does not become "net" + "works".
_TITLE_WORDS = frozenset(
    """
    a an the and but or nor for on at to from by of in with vs as me my
    blue team handbook incident response building cyber risk management program
    cybersecurity manager managers guide ops bash defensive security edition
    developer developers playbook large language model models identity software
    development inside warfare intelligent continuous privacy code supply chain
    web application zero trust networks network cloud native cookbook kubernetes
    observability learning serverless practical architecture hybrid buzzing across
    space illustrated children childrens guide everything learn maths math linear
    algebra formula cheat cheatsheet sheet whitepaper new introduction agents
    agent tools quality context engineering prototype production day rewrite
    foundational generation prompt operationalizing generative vertex solving
    domain specific problems using embeddings vector stores text pretraining
    inference optimization matters illusion thinking nikita prasad feature
    basics memory forensics comprehensive technical offensive windows commands
    chief information officer exam study mind economics emerging markets journey
    plan global engagement standards red teaming vision mission strategic goals
    claude certified architect foundations foundation top interview questions
    answers common agentic workflow patterns sessions google what prompting views
    good key industry use cases partners trends artificial visualizing
    understanding convolutional different techniques leiden long select right
    chapter mastery essentials quick start coupon save percent arch diagram notes
    solution firewall segmentation cisco data science algorithms cleaning
    advanced programming concepts mastering multiprocessing tutorial based
    visualization comparison coding deep python effective conversational human
    loop machine interpretable alignment evaluation everyday build drug discovery
    pipelines financial practice reliable systems succeeding swarm intelligence
    james kennedy pocket art product transformers platform full book search
    powered action governance looks testing skills interoperability vibe course
    intro week how case papers paper gen its your our their into over per via about
    without within through also more most other such than then when where who why
    which been being have has had was were you we they do does did if so no yes
    up out off down own same each few many much some any only very too both
    these those one two three four five six seven eight nine ten first second
    third fourth beginner beginners operations operation guides systems system
    engineers engineer platforms
    smart home automation solutions assistant robotics robot drones drone
    arduino contracts governance definitive management scale quality scratch
    command line aws google cloud platform deciphering purpose built ardupilot
    pixhawk concept flight essential visualization apis industrial mastering
    associate guide portal beginners projects raspberry pico example modeling
    mindstorms inventor recipes solving most common multimodal analysis
    handbook 3d statistics scientists ready blueprints patterns hard parts
    architectures designing fundamentals analyst development lego
    siemens software engineering semantic microsoft power assisted design
    """.split()
)
_TITLE_ACRONYMS = {
    "ai": "AI",
    "llm": "LLM",
    "llms": "LLMs",
    "pdf": "PDF",
    "epub": "EPUB",
    "mcp": "MCP",
    "owasp": "OWASP",
    "cissp": "CISSP",
    "ciso": "CISO",
    "rag": "RAG",
    "sql": "SQL",
    "oop": "OOP",
    "nlp": "NLP",
    "it": "IT",
    "api": "API",
    "ml": "ML",
    "dl": "DL",
    "gpu": "GPU",
    "cpu": "CPU",
    "eda": "EDA",
    "sdlc": "SDLC",
    "mlops": "MLOps",
    "nvidia": "NVIDIA",
    "ubs": "UBS",
    "cio": "CIO",
    "js": "JS",
    "hipaa": "HIPAA",
    "nisp": "NISP",
    "nltk": "NLTK",
    "meap": "MEAP",
    "html": "HTML",
    "css": "CSS",
    "json": "JSON",
    "rlcd": "RLCD",
    "bg": "BG",
    "esp": "ESP",
    "plc": "PLC",
    "plcs": "PLCs",
    "ros": "ROS",
    "ros2": "ROS2",
    "hmi": "HMI",
    "tia": "TIA",
    "bi": "BI",
    "aws": "AWS",
    "gcp": "GCP",
    "3d": "3D",
}
_TITLE_SPECIAL = {
    "3d": "3D",
    "ebpf": "eBPF",
    "numpy": "NumPy",
    "pytorch": "PyTorch",
    "tensorflow": "TensorFlow",
    "pandas": "Pandas",
    "swiftui": "SwiftUI",
    "xcode": "Xcode",
    "react": "ReAct",
    "openai": "OpenAI",
    "github": "GitHub",
    "hdbscan": "HDBScan",
    "genai": "GenAI",
    "javascript": "JavaScript",
    "raspberrypi": "Raspberry Pi",
    "homeassistant": "Home Assistant",
    "ardupilot": "ArduPilot",
    "pixhawk": "Pixhawk",
    "mindstorms": "MINDSTORMS",
    "powerbi": "Power BI",
    "cplusplus": "C++",
    "lego": "LEGO",
    "siemens": "Siemens",
}
_TITLE_SMALL = frozenset(
    {"a", "an", "the", "and", "but", "or", "nor", "for", "on", "at", "to", "from", "by", "of", "in", "with", "vs", "as"}
)
_TITLE_EXTENSIONS = (".epub", ".pdf", ".png", ".pptx", ".docx", ".zip", ".html", ".ppt")
_ORDINAL = re.compile(r"^\d+(?:st|nd|rd|th)$", re.I)
_ARXIV = re.compile(r"^\d{4}\.\d{4,5}(?:v\d+)?$", re.I)
_VERSION = re.compile(r"^v\d+$", re.I)
_COURSE = re.compile(r"^[CW]\d+$", re.I)


def _segment_title_token(token: str) -> list[str]:
    """Split a concatenated lowercase token into known words, or leave it whole."""
    text = token.lower()
    if (
        text in _TITLE_WORDS
        or text in _TITLE_ACRONYMS
        or text in _TITLE_SPECIAL
        or _ORDINAL.match(text)
        or text.isdigit()
    ):
        return [text]
    length = len(text)
    if length < 8:
        return [token]
    best = [10**9] * (length + 1)
    prev = [-1] * (length + 1)
    best[0] = 0
    for start in range(length):
        if best[start] >= 10**9:
            continue
        for end in range(start + 1, min(length, start + 28) + 1):
            piece = text[start:end]
            known = (
                piece in _TITLE_WORDS
                or piece in _TITLE_ACRONYMS
                or piece in _TITLE_SPECIAL
                or _ORDINAL.match(piece)
                or (piece.isdigit() and len(piece) <= 4)
            )
            if not known:
                continue
            cost = 1.0 / (len(piece) ** 2)
            if best[start] + cost < best[end]:
                best[end] = best[start] + cost
                prev[end] = start
    if prev[length] < 0:
        return [token]
    parts: list[str] = []
    cursor = length
    while cursor > 0:
        cut = prev[cursor]
        parts.append(text[cut:cursor])
        cursor = cut
    parts.reverse()
    return parts if len(parts) > 1 else [token]


def _split_camel(token: str) -> list[str]:
    if token.lower() in _TITLE_SPECIAL or token.lower() in _TITLE_ACRONYMS:
        return [token]
    if _VERSION.match(token) or _COURSE.match(token) or _ORDINAL.match(token):
        return [token]
    parts = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", token).split()
    out: list[str] = []
    for part in parts:
        match = re.match(r"^([A-Z]{2,})([A-Z][a-z].+)$", part)
        if match and (match.group(1).lower() in _TITLE_ACRONYMS or match.group(2).lower() in _TITLE_WORDS):
            out.extend([match.group(1), match.group(2)])
        else:
            out.append(part)
    return out or [token]


_HYPHEN_TAILS = frozenset({"powered", "native", "driven", "based", "enabled", "assisted"})


def _keep_title_hyphen(left: str, right: str) -> bool:
    if left.isdigit() and right.isdigit():
        return True
    small = {"a", "an", "the", "of", "in", "on", "to", "for", "and", "with", "by"}
    if (left.lower() in small or right.lower() in small) and (left[:1].isupper() or right[:1].isupper()):
        return True
    right_key = right.lower()
    if left.lower() in _TITLE_ACRONYMS and (right_key in _TITLE_ACRONYMS or right_key in _TITLE_SPECIAL or right_key in _HYPHEN_TAILS):
        return True
    if re.fullmatch(r"[A-Z][a-z]{2,}", left) and re.fullmatch(r"[A-Z][a-z]{2,}", right):
        return True
    return False


def _split_title_hyphens(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        left, right = match.group(1), match.group(2)
        if _keep_title_hyphen(left, right):
            return f"{left}-{right}"
        return f"{left} {right}"

    previous = None
    while previous != text:
        previous = text
        text = re.sub(r"([A-Za-z0-9]+)-([A-Za-z0-9]+)", repl, text)
    return text


def _known_title_word(word: str) -> bool:
    key = word.strip("()").lower().replace("'s", "").replace("'", "")
    return (
        key in _TITLE_WORDS
        or key in _TITLE_ACRONYMS
        or key in _TITLE_SPECIAL
        or bool(_ORDINAL.match(key) or _VERSION.match(key) or _COURSE.match(key) or key.isdigit())
    )


def _polish_title_word(word: str, *, first: bool, last: bool, next_known: bool) -> str:
    if word == ":":
        return word
    bare = word.strip("()")
    key = bare.lower()
    starts_paren = word.startswith("(")
    if key in _TITLE_SPECIAL:
        cased = _TITLE_SPECIAL[key]
    elif key in _TITLE_ACRONYMS:
        cased = _TITLE_ACRONYMS[key]
    elif _ORDINAL.match(key) or key.isdigit():
        cased = key.lower() if _VERSION.match(key) else key
    elif _VERSION.match(key):
        cased = key.lower()
    elif _COURSE.match(bare):
        cased = bare[0].upper() + bare[1:]
    elif any(ch.isupper() for ch in bare[1:]) and not bare.isupper():
        cased = bare
    elif key in _TITLE_SMALL and not first and not last and not starts_paren and next_known:
        cased = key
    elif key.replace("'", "").isalpha():
        cased = key[:1].upper() + key[1:]
    else:
        cased = bare
    if starts_paren:
        cased = "(" + cased
    if word.endswith(")") and not cased.endswith(")"):
        cased += ")"
    return cased


def format_book_title(name: str) -> str:
    """Turn a book filename or rough stem into a readable title.

    Underscores and kebab-case become words. Concatenated lowercase slugs
    are split on a fixed word list. Acronyms, brands, and compounds such as
    ``AI-Powered`` and ``Human-in-the-Loop`` keep their usual spelling.
    """
    raw = name.strip()
    raw = re.sub(r"\\u([0-9a-fA-F]{4})", lambda match: chr(int(match.group(1), 16)), raw)
    raw = re.sub(r"\\(?!u)", "/", raw)
    text = raw.split("/")[-1]
    lowered = text.lower()
    for ext in _TITLE_EXTENSIONS:
        if lowered.endswith(ext):
            text = text[: -len(ext)]
            break
    if _ARXIV.match(text):
        return text

    text = re.sub(r"\s+copy$", "", text, flags=re.I).strip()
    if not _ARXIV.match(text):
        text = text.replace(".", " ")
    text = re.sub(r"(?:^|[_\s])1[6-9]\d{8}(?=$|[_\s])", " ", text)
    text = re.sub(r"[_\s]+v\d+[_\s]+MEAP\b", " (MEAP)", text, flags=re.I)
    text = re.sub(r"\s+full book$", "", text, flags=re.I).strip()
    text = text.replace("\u2013", " - ").replace("\u2014", " - ")
    text = text.replace("+", " ")
    text = text.replace("_", " ")
    text = re.sub(r"(\d+)(st|nd|rd|th)", r" \1\2 ", text, flags=re.I)
    text = re.sub(r"\(From Scrat\b\)?", "(From Scratch)", text, flags=re.I)
    text = re.sub(
        r"recipesforsolvingthemostcommondataen\b",
        "Recipes for Solving Common Data Engineering Problems",
        text,
        flags=re.I,
    )
    text = re.sub(r"\b3ddatasciencewithpython\b", "3d data science with python", text, flags=re.I)
    text = re.sub(r"\s+-\s+", " : ", text)
    text = re.sub(r"\s+", " ", text).strip()

    parts = [part for part in re.split(r"\s+", text) if part]
    # A slug like blueteamhandbook_incidentresponse is a title and a subtitle.
    if (
        len(parts) == 2
        and all(re.fullmatch(r"[a-z0-9]{10,}", part) for part in parts)
    ):
        text = f"{parts[0]} : {parts[1]}"

    text = _split_title_hyphens(text)
    text = re.sub(r"\s+", " ", text).strip(" -")

    tokens: list[str] = []
    for tok in text.split():
        if tok == ":":
            tokens.append(":")
            continue
        if _ARXIV.match(tok):
            tokens.append(tok)
            continue
        bits = [tok]
        if (
            re.search(r"[A-Za-z]{3,}\d|\d[A-Za-z]{2,}", tok)
            and not _VERSION.match(tok)
            and not _COURSE.match(tok)
            and not _ORDINAL.match(tok)
        ):
            bits = re.findall(r"\b3[dD]|[A-Za-z]+|\d+(?:st|nd|rd|th)|\d+|[()]", tok, flags=re.I) or [tok]
        for bit in bits:
            if bit in {"(", ")"}:
                if bit == ")" and tokens:
                    tokens[-1] = tokens[-1] + ")"
                elif bit == "(":
                    tokens.append("(")
                continue
            sides = bit.split("-") if "-" in bit else [bit]
            keep_hyphen = "-" in bit
            pieces: list[str] = []
            for side in sides:
                for camel in _split_camel(side):
                    if camel.islower() or (len(camel) > 10 and camel[1:].islower()):
                        pieces.extend(_segment_title_token(camel.lower()))
                    else:
                        pieces.append(camel)
            if keep_hyphen and len(pieces) == len(sides):
                tokens.append("-".join(pieces))
            else:
                tokens.extend(pieces)

    cleaned: list[str] = []
    for tok in tokens:
        if cleaned and cleaned[-1] == "(":
            cleaned[-1] = "(" + tok
        else:
            cleaned.append(tok)
    tokens = cleaned

    rewritten: list[str] = []
    index = 0
    while index < len(tokens):
        tok = tokens[index]
        nxt = tokens[index + 1].lower() if index + 1 < len(tokens) else ""
        if tok.lower() == "maths" and index + 2 < len(tokens) and tokens[index + 1] == "4" and tokens[index + 2].lower() == "ml":
            rewritten.extend(["Maths", "for", "ML"])
            index += 3
            continue
        if tok.lower() in {"developers", "managers"} and nxt in {"guide", "playbook", "handbook"}:
            stem = "developer" if tok.lower().startswith("developer") else "manager"
            rewritten.append(stem + "'s")
        elif tok.lower() == "childrens" and nxt in {"guide", "book"}:
            rewritten.append("children's")
        else:
            rewritten.append(tok)
        index += 1

    joined: list[str] = []
    index = 0
    while index < len(rewritten):
        piece = rewritten[index]
        if (
            re.fullmatch(r"[A-Za-z]", piece)
            and piece.lower() not in {"a", "i"}
            and index + 1 < len(rewritten)
            and re.fullmatch(r"[A-Za-z]", rewritten[index + 1])
            and rewritten[index + 1].lower() not in {"a", "i"}
        ):
            letters = [piece, rewritten[index + 1]]
            index += 2
            while (
                index < len(rewritten)
                and re.fullmatch(r"[A-Za-z]", rewritten[index])
                and rewritten[index].lower() not in {"a", "i"}
            ):
                letters.append(rewritten[index])
                index += 1
            joined.append(".".join(ch.upper() for ch in letters) + ".")
            continue
        joined.append(piece)
        index += 1

    polished: list[str] = []
    for index, tok in enumerate(joined):
        following = joined[index + 1] if index + 1 < len(joined) else ""
        if "-" in tok and tok != "-":
            bits = tok.split("-")
            polished.append(
                "-".join(
                    _polish_title_word(
                        bit,
                        first=(index == 0 and bit_index == 0),
                        last=(index == len(joined) - 1 and bit_index == len(bits) - 1),
                        next_known=_known_title_word(bits[bit_index + 1]) if bit_index + 1 < len(bits) else _known_title_word(following),
                    )
                    for bit_index, bit in enumerate(bits)
                )
            )
        else:
            polished.append(
                _polish_title_word(
                    tok,
                    first=index == 0 or tok.startswith("("),
                    last=index == len(joined) - 1,
                    next_known=_known_title_word(following),
                )
            )
    title = " ".join(polished)
    title = re.sub(r"\s+:\s+", ": ", title)
    title = re.sub(r"\s+([,.;)])", r"\1", title)
    title = re.sub(r"(\()\s+", r"\1", title)
    title = re.sub(r"\s+", " ", title).strip()
    title = re.sub(r"\s+(\d+(?:st|nd|rd|th) Edition)$", r", \1", title, flags=re.I)
    title = re.sub(r"^(New Whitepaper|Whitepaper)\s+(?!:)", r"\1: ", title)
    return title


def find_nexus_root() -> Path | None:
    """Find the local Nexus storage directory."""
    candidates = [
        Path.home() / ".ai-lab" / "nexus",
        Path.home() / "Documents" / "Information",
        Path.home() / "Information",
    ]
    for c in candidates:
        try:
            if c.is_dir() and any(
                (c / name).is_dir()
                for name in ("01_AI_and_GenAI", "04_Books_Library", "02_Python_and_Data_Science")
            ):
                return c
        except (PermissionError, OSError):
            continue
    for c in candidates:
        try:
            if c.is_dir():
                return c
        except (PermissionError, OSError):
            continue
    return None


def resolve_book_file(rel_path: str) -> Path | None:
    """Locate the actual book file on disk from a relative path."""
    try:
        p_abs = Path(rel_path)
        if p_abs.is_file():
            return p_abs
        if p_abs.with_suffix(".epub").is_file():
            return p_abs.with_suffix(".epub")
        if p_abs.with_suffix(".pdf").is_file():
            return p_abs.with_suffix(".pdf")
    except (TypeError, ValueError, OSError):
        pass

    root = find_nexus_root()
    if not root:
        return None
    # Sanitize and resolve
    clean_rel = rel_path.strip('"\'').lstrip("/\\")
    full = root / clean_rel
    try:
        if full.is_file():
            return full
    except (PermissionError, OSError):
        pass


    # Try sibling with .epub or .pdf extension
    p_epub = full.with_suffix(".epub")
    try:
        if p_epub.is_file():
            return p_epub
    except (PermissionError, OSError):
        pass

    p_pdf = full.with_suffix(".pdf")
    try:
        if p_pdf.is_file():
            return p_pdf
    except (PermissionError, OSError):
        pass

    clean_name = Path(clean_rel).name
    for pattern in (clean_name, f"{clean_name}.epub", f"{clean_name}.pdf"):
        try:
            found = next(root.rglob(pattern), None)
            if found and found.is_file():
                return found
        except (PermissionError, OSError):
            continue

    return None


def _extract_table_of_contents(book_file: Path, max_chars: int = 5000) -> str:
    """Extract Table of Contents, Parts, and Chapter breakdown."""
    epub_file = book_file.with_suffix(".epub")
    if epub_file.is_file():
        try:
            with zipfile.ZipFile(epub_file, "r") as z:
                html_files = z.namelist()
                match_f = next(
                    (f for f in html_files if "contents.html" in f.lower() or "toc.html" in f.lower()),
                    None,
                )
                if match_f:
                    raw = z.read(match_f).decode("utf-8", errors="ignore")
                    txt = re.sub(r"<[^>]+>", "\n", raw)
                    lines = [l.strip() for l in txt.splitlines() if l.strip()]
                    toc_items: list[str] = []
                    for l in lines:
                        if re.match(r"^(?:Part\s+\d+|\d+\s+[A-Z]|appendix\s+[a-z]|brief contents)", l, re.I):
                            toc_items.append(l)
                    if toc_items:
                        book_name = format_book_title(epub_file.name)
                        return f'[Table of Contents / Parts Overview for "{book_name}"]:\n' + "\n".join(toc_items)[:max_chars]
        except Exception:
            pass

    if book_file.suffix.lower() == ".pdf" and book_file.is_file():
        try:
            with open(book_file, "rb") as f:
                data = f.read(2_000_000)
            text = pdf_text(data)
            if text:
                m = re.search(r"(?:brief contents|table of contents|contents)[\s\S]{100,3000}", text, re.I)
                if m:
                    book_name = format_book_title(book_file.name)
                    return f'[Table of Contents / Parts Overview for "{book_name}"]:\n' + m.group(0)[:max_chars]
        except Exception:
            pass

    return ""


def extract_book_context(rel_path: str, query: str, max_chars: int = 5000) -> str:
    """Extract relevant chapter or paragraph excerpts for a user query from the book."""
    book_file = resolve_book_file(rel_path)
    if not book_file:
        return ""

    q_lower = query.lower()
    # Check for structural / TOC / parts / outline queries
    is_toc_query = bool(
        re.search(
            r"\b(?:parts?|parts of the book|part titles?|table of contents|contents|brief contents|chapters?|outline|structure|how is the book organized|how is the book structured)\b",
            q_lower,
        )
    )
    if is_toc_query and not re.search(r"\bchapter\s+\d+\b", q_lower):
        toc_text = _extract_table_of_contents(book_file, max_chars=max_chars)
        if toc_text:
            return toc_text

    # 1. Try Qdrant vector search first
    try:
        from .nexus_rag import NexusRagStore

        store = NexusRagStore()
        chunks = store.search(query, rel_path=rel_path, limit=4)
        if chunks:
            valid_chunks = [c for c in chunks if c.score > 0.05 or len(chunks) == 1]
            if valid_chunks:
                out: list[str] = []
                cur_len = 0
                for c in valid_chunks:
                    snippet = f'[Excerpt from "{c.title}" ({c.chapter})]:\n"{c.text}"'
                    if cur_len + len(snippet) > max_chars:
                        break
                    out.append(snippet)
                    cur_len += len(snippet)
                if out:
                    return "\n\n".join(out)
    except Exception:
        pass

    # 2. Check for preferred EPUB sibling for structured chapter HTML
    epub_file = book_file.with_suffix(".epub")
    if epub_file.is_file():
        excerpts = _search_epub(epub_file, query, max_chars=max_chars)
        if excerpts:
            return excerpts

    # 3. Fall back to PDF extraction if only PDF is available
    if book_file.suffix.lower() == ".pdf" and book_file.is_file():
        return _search_pdf(book_file, query, max_chars=max_chars)

    return ""


def _search_epub(epub_path: Path, query: str, max_chars: int = 5000) -> str:
    """Search an EPUB file for chapter summaries or relevant topic paragraphs."""
    q_lower = query.lower()
    ch_match = re.search(r"\bchapter\s+(\d+)\b", q_lower)

    try:
        with zipfile.ZipFile(epub_path, "r") as z:
            html_files = [f for f in z.namelist() if f.lower().endswith((".html", ".xhtml"))]

            # 1. User asked specifically for a chapter number (e.g. Chapter 1, Chapter 2)
            if ch_match:
                ch_num = ch_match.group(1)
                target = f"chapter-{ch_num}."
                match_file = next((f for f in html_files if target in f.lower()), None)
                if match_file:
                    raw = z.read(match_file).decode("utf-8", errors="ignore")
                    txt = re.sub(r"<[^>]+>", " ", raw)
                    txt = re.sub(r"\s+", " ", txt).strip()
                    book_name = format_book_title(epub_path.name)
                    return (
                        f"[Direct Excerpt from {book_name}, Chapter {ch_num}]:\n"
                        f'"{txt[:max_chars]}"'
                    )

            # 2. General topic or factual question: distinct-term paragraph search
            stop_words = {
                "what", "when", "where", "which", "their", "this", "that", "with",
                "from", "have", "does", "about", "how", "many", "the", "and", "for",
                "are", "use", "using", "been", "can", "you", "tell", "explain",
            }
            q_words = set(
                w.lower()
                for w in re.findall(r"\b[a-zA-Z]{3,}\b", query)
                if w.lower() not in stop_words
            )
            if not q_words:
                return ""

            matches: list[tuple[int, int, str, str]] = []
            for name in html_files:
                try:
                    raw = z.read(name).decode("utf-8", errors="ignore")
                except Exception:
                    continue
                # Split by HTML block tags into coherent paragraphs
                blocks = re.split(r"<(?:p|div|h[1-6]|section)[^>]*>", raw)
                for b in blocks:
                    txt = re.sub(r"<[^>]+>", " ", b).strip()
                    txt = re.sub(r"\s+", " ", txt)
                    if len(txt) < 45:
                        continue
                    lower = txt.lower()
                    distinct_hits = sum(1 for w in q_words if w in lower)
                    if distinct_hits >= 2 or (len(q_words) == 1 and distinct_hits == 1):
                        # Window around match if block is very large
                        if len(txt) > 1500:
                            first_idx = min(lower.find(w) for w in q_words if w in lower)
                            start_pos = max(0, first_idx - 200)
                            end_pos = min(len(txt), start_pos + 1200)
                            txt = ("..." if start_pos > 0 else "") + txt[start_pos:end_pos].strip() + ("..." if end_pos < len(txt) else "")

                        is_ch = "chapter-" in name.lower()
                        is_aux = any(k in name.lower() for k in ("appendix", "index", "dedication", "copyright", "about-"))
                        total_freq = sum(lower.count(w) for w in q_words)
                        score = distinct_hits * 100 + total_freq + (150 if is_ch else (-100 if is_aux else 0))
                        matches.append((score, distinct_hits, name, txt))

            matches.sort(key=lambda x: x[0], reverse=True)
            if matches:
                book_name = format_book_title(epub_path.name)
                out: list[str] = []
                cur_len = 0
                for _score, _hits, name, txt in matches[:5]:
                    ch_label = Path(name).stem.replace("-", " ").title()
                    snippet = f'[Excerpt from "{book_name}" ({ch_label})]:\n"{txt}"'
                    if cur_len + len(snippet) > max_chars:
                        if not out and len(txt) > (max_chars - 200):
                            txt = txt[: max_chars - 200] + "..."
                            snippet = f'[Excerpt from "{book_name}" ({ch_label})]:\n"{txt}"'
                            out.append(snippet)
                        break
                    out.append(snippet)
                    cur_len += len(snippet)
                return "\n\n".join(out)
    except Exception:
        return ""

    return ""


def _search_pdf(pdf_path: Path, query: str, max_chars: int = 5000) -> str:
    """Search readable text in a PDF for relevant paragraphs."""
    try:
        with open(pdf_path, "rb") as f:
            data = f.read(5_000_000)  # Read up to first 5MB
        full_text = pdf_text(data)
        if not full_text:
            return ""

        stop_words = {"what", "when", "where", "which", "their", "this", "that", "with", "from", "the", "and"}
        q_words = set(w.lower() for w in re.findall(r"\b[a-zA-Z]{3,}\b", query) if w.lower() not in stop_words)
        if not q_words:
            return f'[Excerpt from {pdf_path.stem}]:\n"{full_text[:max_chars]}"'

        # Split into sentence/paragraph blocks
        paragraphs = re.split(r"\n{2,}|\.\s+", full_text)
        scored = []
        for p in paragraphs:
            clean_p = p.strip()
            if len(clean_p) < 40:
                continue
            lower = clean_p.lower()
            hits = sum(1 for w in q_words if w in lower)
            if hits > 0:
                score = hits * 100 + sum(lower.count(w) for w in q_words)
                scored.append((score, clean_p))
        scored.sort(key=lambda x: x[0], reverse=True)
        if scored:
            out = [f'[Excerpt from "{pdf_path.stem}"]:\n"{p}"' for _s, p in scored[:3]]
            return "\n\n".join(out)[:max_chars]
        return f'[Excerpt from "{pdf_path.stem}"]:\n"{full_text[:max_chars]}"'
    except Exception:
        return ""
