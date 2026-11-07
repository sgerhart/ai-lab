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


_PDF_PAGE_CACHE: dict[str, tuple[float, list[str]]] = {}
_BOOK_STRUCTURE_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}


def _parse_pdf_cmap(cmap_bytes: bytes) -> dict[str, str]:
    """Parse a PDF /ToUnicode CMap stream into a src_hex -> unicode_str dictionary."""
    text = cmap_bytes.decode("latin1", errors="ignore")
    mapping: dict[str, str] = {}

    for block in re.findall(r"beginbfchar\s*(.*?)\s*endbfchar", text, re.S):
        for m in re.finditer(r"<([0-9a-fA-F]+)>\s*<([0-9a-fA-F]+)>", block):
            src = m.group(1).upper()
            dst = m.group(2)
            try:
                mapping[src] = bytes.fromhex(dst).decode("utf-16-be", errors="ignore")
            except Exception:
                pass

    for block in re.findall(r"beginbfrange\s*(.*?)\s*endbfrange", text, re.S):
        for line in block.strip().splitlines():
            line = line.strip()
            # Format 1: <start> <end> <destStart>
            m1 = re.match(r"^<([0-9a-fA-F]+)>\s*<([0-9a-fA-F]+)>\s*<([0-9a-fA-F]+)>$", line)
            if m1:
                s = int(m1.group(1), 16)
                e = int(m1.group(2), 16)
                d = int(m1.group(3), 16)
                width = len(m1.group(1))
                fmt = f"%0{width}X"
                d_width = len(m1.group(3))
                for i in range(e - s + 1):
                    try:
                        d_hex = f"%0{d_width}X" % (d + i)
                        mapping[fmt % (s + i)] = bytes.fromhex(d_hex).decode("utf-16-be", errors="ignore")
                    except Exception:
                        pass
                continue

            # Format 2: <start> <end> [ <dest1> <dest2> ... ]
            m2 = re.match(r"^<([0-9a-fA-F]+)>\s*<([0-9a-fA-F]+)>\s*\[(.*?)\]$", line)
            if m2:
                s = int(m2.group(1), 16)
                e = int(m2.group(2), 16)
                dests = re.findall(r"<([0-9a-fA-F]+)>", m2.group(3))
                width = len(m2.group(1))
                fmt = f"%0{width}X"
                for i, dst in enumerate(dests):
                    if s + i <= e:
                        try:
                            mapping[fmt % (s + i)] = bytes.fromhex(dst).decode("utf-16-be", errors="ignore")
                        except Exception:
                            pass

    return mapping


def _unpack_pdf_obj_stms(data: bytes) -> dict[int, bytes]:
    """Unpack object streams (/Type /ObjStm) in PDF 1.5+ files into individual objects using linear search."""
    import zlib

    unpacked: dict[int, bytes] = {}
    for chunk in data.split(b"endstream"):
        if b"/Type/ObjStm" not in chunk and b"/Type /ObjStm" not in chunk:
            continue
        parts = chunk.split(b"stream\r\n", 1)
        if len(parts) < 2:
            parts = chunk.split(b"stream\n", 1)
        if len(parts) < 2:
            continue
        header, stream = parts[0], parts[1].strip(b"\r\n")
        n_m = re.search(rb"/N\s+(\d+)", header)
        f_m = re.search(rb"/First\s+(\d+)", header)
        if not n_m or not f_m:
            continue
        try:
            n = int(n_m.group(1))
            first = int(f_m.group(1))
            try:
                decomp = zlib.decompress(stream)
            except Exception:
                decomp = zlib.decompressobj().decompress(stream)
            tokens = decomp[:first].decode("latin1", errors="ignore").split()
            if len(tokens) < 2 * n:
                continue
            pairs = [(int(tokens[2 * i]), int(tokens[2 * i + 1])) for i in range(n)]
            for i in range(n):
                oid, offset = pairs[i]
                end_offset = pairs[i + 1][1] if i + 1 < n else len(decomp) - first
                unpacked[oid] = decomp[first + offset : first + end_offset]
        except Exception:
            continue
    return unpacked


def _extract_pdf_pages_raw(data: bytes, max_pages: int = 500) -> list[str]:
    """Parse pure PDF decompressed streams, BT/ET blocks, kerning arrays, and CMaps page-by-page."""
    import zlib

    obj_streams: dict[int, bytes] = {}
    font_to_cmap: dict[int, dict[str, str]] = {}
    font_to_tuid: dict[int, int] = {}
    page_chunks: list[bytes] = []

    for m in re.finditer(rb"(\d+)\s+0\s+obj([\s\S]*?)endobj", data):
        oid = int(m.group(1))
        chunk = m.group(0)
        s_m = re.search(rb"stream\r?\n(.*?)endstream", chunk, re.S)
        if s_m:
            raw = s_m.group(1).strip(b"\r\n")
            if b"FlateDecode" in chunk:
                try:
                    obj_streams[oid] = zlib.decompress(raw)
                except Exception:
                    try:
                        obj_streams[oid] = zlib.decompressobj().decompress(raw)
                    except Exception:
                        pass
            else:
                obj_streams[oid] = raw

        if b"/Type /Font" in chunk or b"/Type/Font" in chunk:
            tu = re.search(rb"/ToUnicode\s+(\d+)\s+0\s+R", chunk)
            if tu:
                font_to_tuid[oid] = int(tu.group(1))

        if re.search(rb"/Type\s*/Page\b", chunk):
            page_chunks.append(chunk)

    if not page_chunks:
        unpacked = _unpack_pdf_obj_stms(data)
        for oid, obj in unpacked.items():
            if b"/Type /Font" in obj or b"/Type/Font" in obj:
                tu = re.search(rb"/ToUnicode\s+(\d+)\s+0\s+R", obj)
                if tu:
                    font_to_tuid[oid] = int(tu.group(1))
            if re.search(rb"/Type\s*/Page\b", obj):
                page_chunks.append(obj)

    for f_id, tuid in font_to_tuid.items():
        if tuid in obj_streams:
            font_to_cmap[f_id] = _parse_pdf_cmap(obj_streams[tuid])

    pages: list[str] = []
    for p_chunk in page_chunks[:max_pages]:
        page_fonts: dict[str, dict[str, str]] = {}
        font_dict_m = re.search(rb"/Font\s*<<([^>>]+)>>", p_chunk)
        if font_dict_m:
            for fm in re.finditer(rb"/([A-Za-z0-9_]+)\s+(\d+)\s+0\s+R", font_dict_m.group(1)):
                fname = fm.group(1).decode("ascii", errors="ignore")
                fobj = int(fm.group(2))
                if fobj in font_to_cmap:
                    page_fonts[fname] = font_to_cmap[fobj]

        c_single = re.search(rb"/Contents\s+(\d+)\s+0\s+R", p_chunk)
        c_array = re.search(rb"/Contents\s*\[([^\]]+)\]", p_chunk)
        content_ids: list[int] = []
        if c_single:
            content_ids.append(int(c_single.group(1)))
        elif c_array:
            content_ids.extend([int(x) for x in re.findall(rb"(\d+)\s+0\s+R", c_array.group(1))])

        page_lines: list[str] = []
        cur_cmap = next(iter(page_fonts.values()), {})
        for cid in content_ids:
            stream_data = obj_streams.get(cid, b"")
            if not stream_data or b"BT" not in stream_data:
                continue

            for m in re.finditer(
                rb"(/([A-Za-z0-9_]+)\s+[\d\.]+\s+Tf)|(\[([\s\S]*?)\]\s*TJ)|\(((?:\\.|[^\\)])*)\)\s*Tj|<([0-9a-fA-F\s]+)>\s*Tj",
                stream_data,
            ):
                if m.group(1):
                    fn = m.group(2).decode("ascii", errors="ignore")
                    cur_cmap = page_fonts.get(fn, cur_cmap)
                elif m.group(3):
                    tj = m.group(4)
                    parts: list[str] = []
                    for item in re.finditer(rb"\((?:\\.|[^\\)])*\)|<([0-9a-fA-F\s]+)>|(-?\d+(?:\.\d+)?)", tj):
                        val = item.group(0)
                        if val.startswith(b"(") and val.endswith(b")"):
                            s = val[1:-1].decode("latin1", errors="ignore")
                            s = s.replace("\\n", "\n").replace("\\r", "").replace("\\t", "\t")
                            s = s.replace("\\(", "(").replace("\\)", ")")
                            parts.append(s)
                        elif val.startswith(b"<") and val.endswith(b">"):
                            h = item.group(1).decode("ascii", errors="ignore")
                            clean = re.sub(r"\s+", "", h)
                            for i in range(0, len(clean), 4):
                                g = clean[i : i + 4].upper()
                                parts.append(cur_cmap.get(g, ""))
                        else:
                            try:
                                if float(val) < -120:
                                    parts.append(" ")
                            except ValueError:
                                pass
                    line = "".join(parts).strip()
                    if line:
                        page_lines.append(line)
                elif m.group(5):
                    s = m.group(5).decode("latin1", errors="ignore")
                    s = s.replace("\\n", "\n").replace("\\r", "").replace("\\t", "\t")
                    s = s.replace("\\(", "(").replace("\\)", ")")
                    if s.strip():
                        page_lines.append(s.strip())
                elif m.group(6):
                    clean = re.sub(r"\s+", "", m.group(6).decode("ascii", errors="ignore"))
                    parts = [cur_cmap.get(clean[i : i + 4].upper(), "") for i in range(0, len(clean), 4)]
                    line = "".join(parts).strip()
                    if line:
                        page_lines.append(line)

        pages.append("\n".join(page_lines))
    return pages


def extract_pdf_pages(pdf_path: Path, max_pages: int = 500) -> list[str]:
    """Extract page text list for a PDF file with in-memory mtime caching."""
    str_path = str(pdf_path.resolve())
    try:
        mtime = pdf_path.stat().st_mtime
    except (OSError, FileNotFoundError):
        return []

    cached = _PDF_PAGE_CACHE.get(str_path)
    if cached and cached[0] == mtime:
        return cached[1]

    try:
        with open(pdf_path, "rb") as f:
            data = f.read(35_000_000)
        pages = _extract_pdf_pages_raw(data, max_pages=max_pages)
        _PDF_PAGE_CACHE[str_path] = (mtime, pages)
        return pages
    except Exception:
        return []


def _get_pdf_outline_chapters(data: bytes, total_pages: int) -> list[dict[str, Any]]:
    """Extract chapter bookmarks from PDF /Outlines using fast linear scanning."""
    page_id_to_num: dict[int, int] = {}
    dest_to_page: dict[int, int] = {}
    page_num = 1

    # Linear pass over objects
    for chunk in data.split(b"endobj"):
        if b"/Type" in chunk and b"/Page" in chunk and (b"/Page " in chunk or b"/Page\n" in chunk or b"/Page\r" in chunk or b"/Page/" in chunk or b"/Page>>" in chunk):
            m = re.search(rb"(\d+)\s+0\s+obj", chunk)
            if m:
                oid = int(m.group(1))
                page_id_to_num[oid] = page_num
                page_num += 1

    unpacked: dict[int, bytes] | None = None
    if not page_id_to_num:
        unpacked = _unpack_pdf_obj_stms(data)
        for oid, obj in unpacked.items():
            if re.search(rb"/Type\s*/Page\b", obj):
                page_id_to_num[oid] = page_num
                page_num += 1

    # Map indirect destinations [page_obj 0 R /XYZ ...]
    for chunk in data.split(b"endobj"):
        if b"/XYZ" in chunk or b"/Fit" in chunk:
            dm = re.search(rb"(\d+)\s+0\s+obj\s*\[\s*(\d+)\s+0\s+R", chunk)
            if dm:
                d_id = int(dm.group(1))
                target_p_id = int(dm.group(2))
                if target_p_id in page_id_to_num:
                    dest_to_page[d_id] = page_id_to_num[target_p_id]

    named_to_page: dict[str, int] = {}
    for m in re.finditer(rb"\(([^)]+)\)\s*\[\s*(\d+)\s+0\s+R", data):
        dname = m.group(1).decode("latin1", errors="ignore")
        p_id = int(m.group(2))
        if p_id in page_id_to_num:
            named_to_page[dname] = page_id_to_num[p_id]

    action_to_page: dict[int, int] = {}
    for chunk in data.split(b"endobj"):
        if b"/S" in chunk and b"/GoTo" in chunk:
            m = re.search(rb"(\d+)\s+0\s+obj\s*<<\s*/D\s*(?:\(([^)]+)\)|\[\s*(\d+)\s+0\s+R)", chunk)
            if m:
                a_id = int(m.group(1))
                if m.group(2):
                    dname = m.group(2).decode("latin1", errors="ignore")
                    if dname in named_to_page:
                        action_to_page[a_id] = named_to_page[dname]
                elif m.group(3):
                    p_id = int(m.group(3))
                    if p_id in page_id_to_num:
                        action_to_page[a_id] = page_id_to_num[p_id]

    chapters: list[dict[str, Any]] = []
    seen: set[tuple[str, int]] = set()

    sources = [data]
    if unpacked:
        sources.extend(unpacked.values())

    for src in sources:
        for m in re.finditer(rb"<<[^\>]*?/Title\s*(\([^\)]+\)|<[^>]+>)[^\>]*?>>", src):
            chunk = m.group(0)
            t_raw = m.group(1)
            if t_raw.startswith(b"("):
                t = t_raw[1:-1].decode("latin1", errors="ignore")
            else:
                try:
                    h = t_raw[1:-1].decode("ascii", errors="ignore")
                    t = bytes.fromhex(h).decode("utf-16-be", errors="ignore")
                except Exception:
                    t = ""
            t = t.replace("\ufeff", "").strip()
            if not t or len(t) < 3:
                continue

            p_num = None
            a_m = re.search(rb"/A\s+(\d+)\s+0\s+R", chunk)
            if a_m and int(a_m.group(1)) in action_to_page:
                p_num = action_to_page[int(a_m.group(1))]

            if not p_num:
                dm = re.search(rb"/D\s+(\d+)\s+0\s+R", chunk)
                if dm and int(dm.group(1)) in dest_to_page:
                    p_num = dest_to_page[int(dm.group(1))]

            if not p_num:
                dest_arr = re.search(rb"/Dest\s*\[\s*(\d+)\s+0\s+R", chunk)
                if dest_arr and int(dest_arr.group(1)) in page_id_to_num:
                    p_num = page_id_to_num[int(dest_arr.group(1))]
                else:
                    dest_str = re.search(rb"/Dest\s*\(([^)]+)\)", chunk)
                    if dest_str:
                        dn = dest_str.group(1).decode("latin1", errors="ignore")
                        p_num = named_to_page.get(dn)

            if p_num and 1 <= p_num <= total_pages and (t, p_num) not in seen:
                seen.add((t, p_num))
                chapters.append({"title": t, "page": p_num})

    chapters.sort(key=lambda x: x["page"])
    return chapters


def _get_pdf_heading_chapters(pages: list[str]) -> list[dict[str, Any]]:
    """Infer chapter landmarks from PDF Table of Contents or page heading patterns."""
    # 1. Scan early pages for "Table of contents"
    for page in pages[:10]:
        if re.search(r"table of content|contents\b|brief contents", page, re.I):
            entries: list[dict[str, Any]] = []
            seen: set[str] = set()
            for line in page.splitlines():
                matches = list(re.finditer(r"([A-Za-z0-9\s\.,:\x27\"-]{3,60}?)\s+(\d{1,4})(?=\s+[A-Z]|$)", line))
                for m in matches:
                    t = m.group(1).strip()
                    pg = int(m.group(2))
                    if 1 <= pg <= len(pages) and len(t) > 3 and not any(k in t.lower() for k in ("page", "table of content", "version")):
                        if re.search(r"[a-zA-Z]", t) and t.lower() not in seen:
                            seen.add(t.lower())
                            entries.append({"title": t, "page": pg})
            if len(entries) >= 2:
                entries.sort(key=lambda x: x["page"])
                return entries

    # 2. Scan pages for major chapter headings
    chapters: list[dict[str, Any]] = []
    seen_titles: set[str] = set()
    for idx, p_text in enumerate(pages):
        page_num = idx + 1
        lines = [l.strip() for l in p_text.splitlines() if l.strip()]
        for line in lines[:4]:
            m = re.match(
                r"^(?:Chapter\s+\d+[\s\:\-]+[^\n]{3,60}|(?:\d+\.)+\s+[A-Z][^\n]{3,60}|Executive Summary|Quick Start Guide|Introduction|Conclusion|Appendix|References)",
                line,
                re.I,
            )
            if m:
                t = m.group(0).strip()
                if t.lower() not in seen_titles and len(t) <= 80:
                    seen_titles.add(t.lower())
                    chapters.append({"title": t, "page": page_num})
                    break

    if len(chapters) >= 2:
        return chapters

    # 3. Fallback: Milestone sections if book is multi-page
    total = len(pages)
    if total > 15:
        step = max(5, total // 6)
        milestones = []
        for p in range(1, total + 1, step):
            milestones.append({"title": f"Section (Page {p})", "page": p})
        return milestones

    return [{"title": "Start", "page": 1}]


def _get_epub_chapters(epub_path: Path) -> tuple[int, list[dict[str, Any]]]:
    """Parse EPUB chapters from toc.ncx or HTML files with estimated page mapping."""
    chapters: list[dict[str, Any]] = []
    try:
        with zipfile.ZipFile(epub_path, "r") as z:
            ncx_files = [f for f in z.namelist() if f.lower().endswith(".ncx")]
            if ncx_files:
                raw = z.read(ncx_files[0]).decode("utf-8", errors="ignore")
                navs = re.findall(r"<navPoint[\s\S]*?<navLabel>\s*<text>(.*?)</text>\s*</navLabel>", raw)
                if navs:
                    cur_p = 1
                    for n in navs:
                        title = n.strip()
                        if title and len(title) > 2:
                            chapters.append({"title": title, "page": cur_p})
                            cur_p += 8
                    return max(cur_p, 1), chapters

            html_files = [f for f in z.namelist() if f.lower().endswith((".html", ".xhtml"))]
            cur_p = 1
            for f in html_files:
                stem = Path(f).stem.replace("-", " ").title()
                if not any(k in stem.lower() for k in ("cover", "nav", "toc")):
                    chapters.append({"title": stem, "page": cur_p})
                    cur_p += 10
            return max(cur_p, 1), chapters
    except Exception:
        return 1, [{"title": "Beginning", "page": 1}]


def get_book_structure(rel_path: str) -> dict[str, Any]:
    """Return document structure (title, format, total_pages, and chapter list)."""
    book_file = resolve_book_file(rel_path)
    if not book_file or not book_file.is_file():
        return {}

    str_path = str(book_file.resolve())
    try:
        mtime = book_file.stat().st_mtime
    except (OSError, FileNotFoundError):
        return {}

    cached = _BOOK_STRUCTURE_CACHE.get(str_path)
    if cached and cached[0] == mtime:
        return cached[1]

    title = format_book_title(book_file.name)
    fmt = book_file.suffix.lower().lstrip(".")

    # If sibling EPUB exists, extract rich chapter index in milliseconds
    epub_file = book_file.with_suffix(".epub")
    epub_chapters: list[dict[str, Any]] = []
    epub_total = 1
    if epub_file.is_file():
        epub_total, epub_chapters = _get_epub_chapters(epub_file)

    if fmt == "pdf":
        total_pages = 1
        chapters: list[dict[str, Any]] = []
        try:
            with open(book_file, "rb") as f:
                data = f.read(25_000_000)
            count_m = re.findall(rb"/Count\s+(\d+)", data)
            if count_m:
                total_pages = max(int(c) for c in count_m)
            chapters = _get_pdf_outline_chapters(data, total_pages or 500)
            if chapters:
                total_pages = max(total_pages, max(c["page"] for c in chapters))
        except Exception:
            chapters = []

        # If PDF outline didn't yield chapters, use sibling EPUB chapters if available
        if len(chapters) < 2 and len(epub_chapters) >= 2:
            chapters = epub_chapters
            if total_pages <= 1:
                total_pages = epub_total

        # Fallback to milestone page markers if multi-page but no outline
        if len(chapters) < 2 and total_pages > 15:
            step = max(5, total_pages // 6)
            chapters = [{"title": f"Section (Page {p})", "page": p} for p in range(1, total_pages + 1, step)]

        res = {
            "title": title,
            "rel_path": rel_path,
            "format": "pdf",
            "total_pages": total_pages,
            "chapters": chapters,
        }
        _BOOK_STRUCTURE_CACHE[str_path] = (mtime, res)
        return res

    if fmt == "epub":
        total_pages, chapters = _get_epub_chapters(book_file)
        return {
            "title": title,
            "rel_path": rel_path,
            "format": "epub",
            "total_pages": total_pages,
            "chapters": chapters,
        }

    return {
        "title": title,
        "rel_path": rel_path,
        "format": fmt,
        "total_pages": 1,
        "chapters": [{"title": "Document", "page": 1}],
    }


def _extract_table_of_contents(book_file: Path, max_chars: int = 5000) -> str:
    """Extract Table of Contents, Parts, and Chapter breakdown."""
    struct = get_book_structure(str(book_file))
    if struct and struct.get("chapters") and len(struct["chapters"]) >= 2:
        lines = [f"Page {c['page']}: {c['title']}" for c in struct["chapters"]]
        return f'[Table of Contents for "{struct.get("title", book_file.stem)}"]:\n' + "\n".join(lines)[:max_chars]

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

    return ""


def extract_book_context(
    rel_path: str,
    query: str,
    page: int | None = None,
    chapter: str = "",
    max_chars: int = 6000,
) -> str:
    """Extract targeted chapter or paragraph excerpts for a user query from the book."""
    book_file = resolve_book_file(rel_path)
    if not book_file:
        return ""

    struct = get_book_structure(rel_path)
    title = struct.get("title", format_book_title(book_file.name))
    total_pages = struct.get("total_pages", 1)
    chapters = struct.get("chapters", [])

    is_pdf = book_file.suffix.lower() == ".pdf"
    pages_list: list[str] | None = None

    def _get_pages() -> list[str]:
        nonlocal pages_list
        if pages_list is None:
            pages_list = extract_pdf_pages(book_file) if is_pdf else []
        return pages_list

    q_lower = query.lower()
    ch_num_match = re.search(r"\bchapter\s+(\d+)\b", q_lower)

    # 1. Query explicitly targets a specific chapter number (e.g. "Chapter 18")
    if ch_num_match:
        target_num = ch_num_match.group(1)
        # Check EPUB sibling or self first
        epub_file = book_file if not is_pdf else book_file.with_suffix(".epub")
        if epub_file.is_file():
            ex = _search_epub(epub_file, query, max_chars=max_chars)
            if ex:
                return ex

        # Check PDF pages by chapter landmark
        for idx, ch in enumerate(chapters):
            if re.search(rf"\bchapter\s+{target_num}\b", ch["title"], re.I) or re.search(rf"^{target_num}\b", ch["title"]):
                start_p = ch["page"]
                end_p = chapters[idx + 1]["page"] - 1 if idx + 1 < len(chapters) else start_p + 8
                end_p = max(start_p, min(total_pages, end_p))
                if is_pdf:
                    pages = _get_pages()
                    parts = [
                        f"--- Page {p} ---\n{pages[p-1].strip()}"
                        for p in range(start_p, end_p + 1)
                        if 1 <= p <= len(pages) and pages[p - 1].strip()
                    ]
                    joined = "\n\n".join(parts)
                    if joined:
                        return (
                            f'[Direct Book Excerpt from "{title}" - Chapter {target_num}: "{ch["title"]}" (Pages {start_p}–{end_p})]:\n'
                            f'"{joined[:max_chars]}"'
                        )

    # 2. Check for structural / TOC query
    is_toc_query = bool(
        re.search(
            r"\b(?:parts?|parts of the book|part titles?|table of contents|contents|brief contents|chapters?|outline|structure|how is the book organized|how is the book structured)\b",
            q_lower,
        )
    )
    if is_toc_query and not ch_num_match:
        toc_text = _extract_table_of_contents(book_file, max_chars=max_chars)
        if toc_text:
            return toc_text

    # 3. Target by active chapter from reading position (skip placeholders like "Start", "Beginning", "Document")
    if chapter and chapter.strip().lower() not in ("start", "beginning", "document", "cover", "title"):
        matched_ch: dict[str, Any] | None = None
        matched_idx = -1
        ch_clean = chapter.strip().lower()
        for idx, ch in enumerate(chapters):
            t_low = ch["title"].lower()
            if t_low == ch_clean or t_low in ch_clean or ch_clean in t_low:
                matched_ch = ch
                matched_idx = idx
                break

        if matched_ch and is_pdf:
            pages = _get_pages()
            start_p = matched_ch["page"]
            if matched_idx + 1 < len(chapters):
                end_p = min(total_pages, chapters[matched_idx + 1]["page"] - 1)
            else:
                end_p = min(total_pages, start_p + 8)
            end_p = max(start_p, end_p)

            parts: list[str] = []
            for p_num in range(start_p, end_p + 1):
                if 1 <= p_num <= len(pages):
                    t = pages[p_num - 1].strip()
                    if t:
                        parts.append(f"--- Page {p_num} ---\n{t}")
            joined = "\n\n".join(parts)
            if joined:
                return (
                    f'[Direct Book Excerpt from "{title}" - Chapter: "{matched_ch["title"]}" (Pages {start_p}–{end_p})]:\n'
                    f'"{joined[:max_chars]}"'
                )

    # 4. Target by active page from reading position
    if page is not None and is_pdf:
        pages = _get_pages()
        p_clamped = max(1, min(page, len(pages)))
        end_p = min(len(pages), p_clamped + 2)
        parts = []
        for p_num in range(p_clamped, end_p + 1):
            t = pages[p_num - 1].strip()
            if t:
                parts.append(f"--- Page {p_num} ---\n{t}")
        joined = "\n\n".join(parts)
        if joined:
            ch_tag = f' - Chapter: "{chapter}"' if chapter and chapter.lower() not in ("start", "beginning", "document") else ""
            return (
                f'[Direct Book Excerpt from "{title}"{ch_tag} (Pages {p_clamped}–{end_p})]:\n'
                f'"{joined[:max_chars]}"'
            )

    # 5. Qdrant vector search
    try:
        from .nexus_rag import NexusRagStore, ensure_book_indexed

        ensure_book_indexed(rel_path)
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

    # 6. Fallback: Search PDF pages directly by keyword scoring
    if is_pdf:
        pages = _get_pages()
        res = _search_pdf_pages(pages, title, query, max_chars=max_chars)
        if res:
            return res
        res = _search_pdf_pages(pages, title, query, max_chars=max_chars)
        if res:
            return res

    # Sibling EPUB search fallback
    epub_file = book_file.with_suffix(".epub")
    if epub_file.is_file():
        ex = _search_epub(epub_file, query, max_chars=max_chars)
        if ex:
            return ex

    return ""


def _search_pdf_pages(pages: list[str], title: str, query: str, max_chars: int = 5000) -> str:
    """Score PDF pages for keywords in the query and return relevant excerpts."""
    stop_words = {
        "what", "when", "where", "which", "their", "this", "that", "with",
        "from", "have", "does", "about", "how", "many", "the", "and", "for",
        "are", "use", "using", "been", "can", "you", "tell", "explain",
    }
    q_words = set(w.lower() for w in re.findall(r"\b[a-zA-Z]{3,}\b", query) if w.lower() not in stop_words)
    if not q_words:
        first_p = next((p for p in pages if len(p.strip()) > 50), "")
        return f'[Excerpt from "{title}"]:\n"{first_p[:max_chars]}"' if first_p else ""

    scored: list[tuple[int, int, str]] = []
    for idx, p_text in enumerate(pages):
        page_num = idx + 1
        blocks = re.split(r"\n{2,}|\.\s+", p_text)
        for b in blocks:
            b_clean = b.strip()
            if len(b_clean) < 40:
                continue
            lower = b_clean.lower()
            distinct_hits = sum(1 for w in q_words if w in lower)
            if distinct_hits > 0:
                total_freq = sum(lower.count(w) for w in q_words)
                score = distinct_hits * 100 + total_freq
                scored.append((score, page_num, b_clean))

    scored.sort(key=lambda x: x[0], reverse=True)
    if scored:
        out: list[str] = []
        cur_len = 0
        seen_blocks: set[str] = set()
        for _score, page_num, text in scored[:4]:
            if text in seen_blocks:
                continue
            seen_blocks.add(text)
            snippet = f'[Excerpt from "{title}" (Page {page_num})]:\n"{text}"'
            if cur_len + len(snippet) > max_chars:
                break
            out.append(snippet)
            cur_len += len(snippet)
        if out:
            return "\n\n".join(out)

    return ""


def _search_pdf(pdf_path: Path, query: str, max_chars: int = 5000) -> str:
    """Search readable text in a PDF for relevant paragraphs using cached page extraction."""
    pages = extract_pdf_pages(pdf_path)
    if not pages:
        return ""
    title = format_book_title(pdf_path.name)
    return _search_pdf_pages(pages, title, query, max_chars=max_chars)


def _search_epub(epub_path: Path, query: str, max_chars: int = 5000) -> str:
    """Search an EPUB file for chapter summaries or relevant topic paragraphs."""
    q_lower = query.lower()
    ch_match = re.search(r"\bchapter\s+(\d+)\b", q_lower)

    try:
        with zipfile.ZipFile(epub_path, "r") as z:
            html_files = [f for f in z.namelist() if f.lower().endswith((".html", ".xhtml"))]
            book_name = format_book_title(epub_path.name)

            # 1. User asked specifically for a chapter number (e.g. Chapter 1, Chapter 18)
            if ch_match:
                ch_num = ch_match.group(1)
                match_file: str | None = None

                # 1a. Check toc.ncx or nav.xhtml for exact chapter title and target href
                ncx_files = [f for f in z.namelist() if f.lower().endswith((".ncx", "nav.xhtml"))]
                for ncx_f in ncx_files:
                    try:
                        raw_ncx = z.read(ncx_f).decode("utf-8", errors="ignore")
                        for m in re.finditer(
                            r"<navPoint[^>]*>[\s\S]*?<text>(.*?)</text>[\s\S]*?<content\s+src=\"([^\"]+)\"",
                            raw_ncx,
                        ):
                            title_text = m.group(1).strip()
                            if re.search(rf"\bchapter\s+{ch_num}\b|^{ch_num}\.|\bch(?:apter)?[_\-]?{ch_num}\b", title_text, re.I):
                                src = m.group(2).split("#")[0]
                                target_f = next((f for f in html_files if f.endswith(src) or src.endswith(f)), None)
                                if target_f:
                                    match_file = target_f
                                    break
                        if match_file:
                            break
                    except Exception:
                        pass

                # 1b. Check filenames for ch18.html, chapter-18.html, ch01.html, etc.
                if not match_file:
                    ch_pat = re.compile(rf"(?:^|[_\-/])(?:ch|chapter)[_\-]?0*{ch_num}\.(?:x?html)$", re.I)
                    match_file = next((f for f in html_files if ch_pat.search(f)), None)

                # 1c. Check inside HTML files for heading tags matching Chapter X
                if not match_file:
                    for h_file in html_files:
                        try:
                            sample = z.read(h_file)[:4000].decode("utf-8", errors="ignore")
                            if re.search(rf"<h[1-3][^>]*>[^<]*\b(?:chapter\s+{ch_num}|{ch_num}\.)\b", sample, re.I):
                                match_file = h_file
                                break
                        except Exception:
                            continue

                if match_file:
                    raw = z.read(match_file).decode("utf-8", errors="ignore")
                    txt = re.sub(r"<[^>]+>", " ", raw)
                    txt = re.sub(r"\s+", " ", txt).strip()
                    if txt:
                        return (
                            f'[Direct Excerpt from "{book_name}", Chapter {ch_num}]:\n'
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
                for w in re.findall(r"\b[a-zA-Z0-9]{2,}\b", query)
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
                blocks = re.split(r"<(?:p|div|h[1-6]|section)[^>]*>", raw)
                for b in blocks:
                    txt = re.sub(r"<[^>]+>", " ", b).strip()
                    txt = re.sub(r"\s+", " ", txt)
                    if len(txt) < 45:
                        continue
                    lower = txt.lower()
                    distinct_hits = sum(1 for w in q_words if w in lower)
                    if distinct_hits >= 2 or (len(q_words) == 1 and distinct_hits == 1):
                        if len(txt) > 1500:
                            first_idx = min(lower.find(w) for w in q_words if w in lower)
                            start_pos = max(0, first_idx - 200)
                            end_pos = min(len(txt), start_pos + 1200)
                            txt = ("..." if start_pos > 0 else "") + txt[start_pos:end_pos].strip() + ("..." if end_pos < len(txt) else "")

                        is_ch = bool(re.search(r"(?:^|[_\-/])(?:ch|chapter)\d", name.lower()))
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
