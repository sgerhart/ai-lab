"""Book cover images from EPUB metadata and embedded PDF pictures.

No extra image libraries. Covers are cached under ~/.ai-lab/nexus-covers so the
library list does not reopen every book on each page view.
"""

from __future__ import annotations

import hashlib
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from urllib.parse import unquote

from .nexus_study import find_nexus_root

_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
_MEDIA = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
}


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _media_for(name: str, blob: bytes) -> str:
    suffix = Path(name).suffix.lower()
    if suffix in _MEDIA:
        return _MEDIA[suffix]
    if blob.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if blob.startswith(b"\x89PNG"):
        return "image/png"
    if blob.startswith(b"RIFF") and blob[8:12] == b"WEBP":
        return "image/webp"
    if blob.startswith(b"GIF8"):
        return "image/gif"
    return "application/octet-stream"


def _zip_join(base: str, href: str) -> str | None:
    href = unquote(href.split("#", 1)[0]).replace("\\", "/")
    if not href:
        return None
    parts: list[str] = []
    prefix = [] if base in {"", "."} else base.split("/")
    for part in prefix + href.split("/"):
        if part in {"", "."}:
            continue
        if part == "..":
            return None
        parts.append(part)
    return "/".join(parts)


def _named_cover(zf: zipfile.ZipFile) -> tuple[bytes, str] | None:
    images = [
        name
        for name in zf.namelist()
        if Path(name).suffix.lower() in _IMAGE_SUFFIXES and "cover" in name.lower()
    ]
    if not images:
        return None
    images.sort(key=len)
    blob = zf.read(images[0])
    if len(blob) < 64:
        return None
    return blob, _media_for(images[0], blob)


def epub_cover(path: Path) -> tuple[bytes, str] | None:
    """Return the EPUB cover image bytes and media type."""
    try:
        zf = zipfile.ZipFile(path)
    except (OSError, zipfile.BadZipFile):
        return None
    with zf:
        names = set(zf.namelist())
        opf_path = ""
        if "META-INF/container.xml" in names:
            try:
                container = ET.fromstring(zf.read("META-INF/container.xml"))
            except ET.ParseError:
                container = None
            if container is not None:
                for el in container.iter():
                    if _local(el.tag) == "rootfile":
                        opf_path = el.attrib.get("full-path") or ""
                        break
        if not opf_path or opf_path not in names or ".." in Path(opf_path).parts:
            return _named_cover(zf)
        try:
            opf = ET.fromstring(zf.read(opf_path))
        except ET.ParseError:
            return _named_cover(zf)
        cover_id = ""
        items: list[dict[str, str]] = []
        for el in opf.iter():
            kind = _local(el.tag)
            if kind == "meta" and (el.attrib.get("name") or "").lower() == "cover":
                cover_id = el.attrib.get("content") or ""
            elif kind == "item":
                items.append(dict(el.attrib))
        href = ""
        for item in items:
            if cover_id and item.get("id") == cover_id:
                href = item.get("href") or ""
                break
        if not href:
            for item in items:
                if "cover-image" in (item.get("properties") or ""):
                    href = item.get("href") or ""
                    break
        if not href:
            for item in items:
                candidate = (item.get("href") or "").lower()
                if "cover" in candidate and Path(candidate).suffix.lower() in _IMAGE_SUFFIXES:
                    href = item.get("href") or ""
                    break
        if not href:
            return _named_cover(zf)
        base = str(Path(opf_path).parent)
        target = _zip_join(base, href)
        if target not in names:
            return _named_cover(zf)
        blob = zf.read(target)
        if len(blob) < 64:
            return None
        return blob, _media_for(target, blob)


def _largest_marked(data: bytes, start: bytes, end: bytes, end_len: int) -> bytes | None:
    best: bytes | None = None
    cursor = 0
    window = data[:12_000_000]
    while True:
        begin = window.find(start, cursor)
        if begin < 0:
            break
        finish = window.find(end, begin + len(start))
        if finish < 0:
            break
        chunk = window[begin : finish + end_len]
        if 64 <= len(chunk) <= 2_500_000 and (best is None or len(chunk) > len(best)):
            best = chunk
        cursor = begin + len(start)
    return best


def embedded_image(data: bytes) -> tuple[bytes, str] | None:
    """Largest JPEG or PNG embedded in a PDF byte string."""
    jpeg = _largest_marked(data, b"\xff\xd8\xff", b"\xff\xd9", 2)
    png = _largest_marked(data, b"\x89PNG\r\n\x1a\n", b"IEND\xaeB`\x82", 8)
    if jpeg and (png is None or len(jpeg) >= len(png)):
        return jpeg, "image/jpeg"
    if png:
        return png, "image/png"
    return None


def pdf_cover(path: Path) -> tuple[bytes, str] | None:
    try:
        with path.open("rb") as handle:
            data = handle.read(12_000_000)
    except OSError:
        return None
    return embedded_image(data)


def book_file_for_cover(rel_path: str) -> Path | None:
    """Resolve a library-relative EPUB or PDF and refuse paths that leave the library."""
    if not rel_path or len(rel_path) > 500:
        return None
    root = find_nexus_root()
    if root is None:
        return None
    clean = rel_path.strip().strip("\"'").lstrip("/\\")
    if ".." in Path(clean).parts:
        return None
    try:
        root_resolved = root.resolve()
        full = (root / clean).resolve()
    except OSError:
        return None
    if not full.is_relative_to(root_resolved):
        return None
    candidates = [full]
    if full.suffix.lower() == ".pdf":
        candidates.insert(0, full.with_suffix(".epub"))
    elif full.suffix.lower() != ".epub":
        candidates = [full.with_suffix(".epub"), full.with_suffix(".pdf")]
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        if resolved.is_relative_to(root_resolved) and resolved.is_file():
            if resolved.suffix.lower() in {".epub", ".pdf"}:
                return resolved
    return None


def load_cover(rel_path: str) -> tuple[bytes, str] | None:
    """Cover for a library path, served from the local cache when possible."""
    path = book_file_for_cover(rel_path)
    if path is None:
        return None
    try:
        stat = path.stat()
    except OSError:
        return None
    key = hashlib.sha256(f"{path}:{stat.st_mtime_ns}:{stat.st_size}".encode()).hexdigest()
    cache = Path.home() / ".ai-lab" / "nexus-covers"
    blob_path = cache / f"{key}.bin"
    kind_path = cache / f"{key}.type"
    if blob_path.is_file() and kind_path.is_file():
        kind = kind_path.read_text(encoding="utf-8").strip()
        if kind.startswith("image/"):
            return blob_path.read_bytes(), kind
    found = epub_cover(path) if path.suffix.lower() == ".epub" else pdf_cover(path)
    if found is None or not found[1].startswith("image/"):
        return None
    try:
        cache.mkdir(parents=True, exist_ok=True)
        blob_path.write_bytes(found[0])
        kind_path.write_text(found[1], encoding="utf-8")
    except OSError:
        return found
    return found
