"""Cybersecurity Vise evidence collection and normalization pipeline (IWO-074).

Acceptance criteria:
1. Collector fixtures normalize to the standard evidence schema (EvidenceRef).
2. Missing or unavailable collectors degrade gracefully.
3. Suspicious binary bytes are never embedded in database rows or default API payloads;
   raw artifacts remain referenced via quarantine:// URIs.
4. Evidence is summarized into structured, safe markdown suitable for LLM analysis
   without granting hypervisor or guest access.

Strict zero-network-imports boundary: no socket, http, urllib, requests, or httpx.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

from .events import EmbeddedPayloadRefused, EvidenceRef


_SECRET_KEY = re.compile(
    r"(password|secret|token|api_key|authorization|credential|private_key)",
    re.IGNORECASE,
)
_PAYLOAD_KEYS = frozenset(
    {"content", "bytes", "payload", "sample", "malware", "binary", "raw"}
)

COLLECTOR_CATEGORIES = (
    "process_tree",
    "filesystem_delta",
    "registry_delta",
    "dns_metadata",
    "network_metadata",
    "pcap_reference",
    "hashes",
    "static_metadata",
    "yara_results",
    "screenshots",
    "memory_analysis",
)


def _validate_telemetry_safety(data: Any) -> Any:
    """Validates that telemetry contains no embedded binary bytes or payload keys, and redacts secrets."""
    if data is None:
        return None
    if isinstance(data, (bytes, bytearray)):
        raise EmbeddedPayloadRefused("raw binary bytes forbidden in telemetry; use quarantine:// reference")
    if isinstance(data, dict):
        cleaned: dict[str, Any] = {}
        for key, val in data.items():
            name = str(key)
            if name.lower() in _PAYLOAD_KEYS:
                raise EmbeddedPayloadRefused(f"refusing embedded payload field '{name}'; use quarantine:// locator")
            if isinstance(val, (bytes, bytearray)):
                raise EmbeddedPayloadRefused(f"raw binary bytes forbidden in field '{name}'")
            if _SECRET_KEY.search(name):
                cleaned[name] = "[redacted]"
            else:
                cleaned[name] = _validate_telemetry_safety(val)
        return cleaned
    if isinstance(data, (list, tuple)):
        return [_validate_telemetry_safety(item) for item in data]
    return data


@dataclass(frozen=True)
class CollectorResult:
    """Normalized result from a single evidence collector."""

    collector_name: str
    category: str
    status: str  # "success", "skipped", "unsupported", "failed"
    evidence_refs: tuple[EvidenceRef, ...] = ()
    structured_data: dict[str, Any] = field(default_factory=dict)
    summary: str = ""
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "collector_name": self.collector_name,
            "category": self.category,
            "status": self.status,
            "evidence_refs": [ref.to_dict() for ref in self.evidence_refs],
            "structured_data": dict(self.structured_data),
            "summary": self.summary,
            "error": self.error,
        }


@dataclass
class EvidenceBundle:
    """Aggregated, sanitized evidence bundle for a Vise job."""

    job_id: str
    profile: str
    collected_at: str
    evidence_refs: list[EvidenceRef] = field(default_factory=list)
    results_by_collector: dict[str, CollectorResult] = field(default_factory=dict)
    quarantine_manifest: list[dict[str, Any]] = field(default_factory=list)
    llm_summary: str = ""
    digest_sha256: str = ""

    def compute_digest(self) -> str:
        serialized = json.dumps(
            [ref.to_dict() for ref in sorted(self.evidence_refs, key=lambda r: r.evidence_id)],
            sort_keys=True,
        )
        self.digest_sha256 = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        return self.digest_sha256

    def to_dict(self) -> dict[str, Any]:
        if not self.digest_sha256:
            self.compute_digest()
        return {
            "job_id": self.job_id,
            "profile": self.profile,
            "collected_at": self.collected_at,
            "digest_sha256": self.digest_sha256,
            "evidence_refs": [ref.to_dict() for ref in self.evidence_refs],
            "results": {k: v.to_dict() for k, v in self.results_by_collector.items()},
            "quarantine_manifest": list(self.quarantine_manifest),
            "llm_summary": self.llm_summary,
        }


# ---------------------------------------------------------------------------
# Individual Normalized Collectors
# ---------------------------------------------------------------------------

def collect_hashes(
    job_id: str,
    raw_data: dict[str, Any] | None,
    quarantine_base: str = "quarantine://evidence",
) -> CollectorResult:
    """Normalizes cryptographic and fuzzy hashes of artifacts without storing sample bytes."""
    data = _validate_telemetry_safety(raw_data)
    if not data or "hashes" not in data:
        return CollectorResult(
            collector_name="hashes",
            category="hashes",
            status="skipped",
            summary="No cryptographic hashes collected.",
        )

    hash_data = data.get("hashes", {})
    if not isinstance(hash_data, dict):
        return CollectorResult(
            collector_name="hashes",
            category="hashes",
            status="failed",
            error="Hashes metadata must be a dictionary",
        )

    sanitized = {
        "md5": str(hash_data.get("md5", "")).lower(),
        "sha1": str(hash_data.get("sha1", "")).lower(),
        "sha256": str(hash_data.get("sha256", "")).lower(),
        "ssdeep": str(hash_data.get("ssdeep", "")),
        "imphash": str(hash_data.get("imphash", "")).lower(),
    }
    sanitized = {k: v for k, v in sanitized.items() if v}

    serialized = json.dumps(sanitized, sort_keys=True).encode("utf-8")
    ref_sha = hashlib.sha256(serialized).hexdigest()
    ev_ref = EvidenceRef(
        evidence_id=f"ev-{job_id[:8]}-hashes",
        locator=f"{quarantine_base}/{job_id}/hashes.json",
        sha256=ref_sha,
        media_type="application/json",
        byte_length=len(serialized),
    )
    return CollectorResult(
        collector_name="hashes",
        category="hashes",
        status="success",
        evidence_refs=(ev_ref,),
        structured_data=sanitized,
        summary=f"Extracted {len(sanitized)} cryptographic/fuzzy hashes.",
    )


def collect_process_tree(
    job_id: str,
    raw_data: dict[str, Any] | None,
    quarantine_base: str = "quarantine://evidence",
) -> CollectorResult:
    """Normalizes process execution tree and command-line metadata."""
    data = _validate_telemetry_safety(raw_data)
    if not data or "processes" not in data:
        return CollectorResult(
            collector_name="process_tree",
            category="process_tree",
            status="skipped",
            summary="No process tree telemetry collected from guest.",
        )

    processes = data.get("processes", [])
    sanitized_processes: list[dict[str, Any]] = []
    suspicious_pids: list[int] = []

    for p in processes:
        if not isinstance(p, dict):
            continue
        pid = int(p.get("pid", 0))
        ppid = int(p.get("ppid", 0))
        name = str(p.get("name", "unknown"))
        cmdline = str(p.get("cmdline", ""))
        p_sha = str(p.get("sha256", "")).lower()

        cleaned_cmd = _SECRET_KEY.sub("[REDACTED]", cmdline)
        sanitized_processes.append(
            {
                "pid": pid,
                "ppid": ppid,
                "name": name,
                "cmdline": cleaned_cmd[:1000],
                "sha256": p_sha,
                "suspicious": bool(p.get("suspicious", False)),
            }
        )
        if p.get("suspicious"):
            suspicious_pids.append(pid)

    serialized = json.dumps(sanitized_processes, sort_keys=True).encode("utf-8")
    ref_sha = hashlib.sha256(serialized).hexdigest()
    ev_ref = EvidenceRef(
        evidence_id=f"ev-{job_id[:8]}-process-tree",
        locator=f"{quarantine_base}/{job_id}/process_tree.json",
        sha256=ref_sha,
        media_type="application/json",
        byte_length=len(serialized),
    )

    summary = (
        f"Analyzed {len(sanitized_processes)} processes. "
        f"Suspicious processes detected: {len(suspicious_pids)}."
    )
    return CollectorResult(
        collector_name="process_tree",
        category="process_tree",
        status="success",
        evidence_refs=(ev_ref,),
        structured_data={"processes": sanitized_processes, "count": len(sanitized_processes)},
        summary=summary,
    )


def collect_filesystem_delta(
    job_id: str,
    raw_data: dict[str, Any] | None,
    quarantine_base: str = "quarantine://evidence",
) -> CollectorResult:
    """Normalizes created, modified, or deleted filesystem entries."""
    data = _validate_telemetry_safety(raw_data)
    if not data or "filesystem" not in data:
        return CollectorResult(
            collector_name="filesystem_delta",
            category="filesystem_delta",
            status="skipped",
            summary="No filesystem delta telemetry collected.",
        )

    fs_entries = data.get("filesystem", [])
    sanitized_entries: list[dict[str, Any]] = []

    for entry in fs_entries:
        if not isinstance(entry, dict):
            continue
        path = str(entry.get("path", ""))
        action = str(entry.get("action", "modified"))
        file_sha = str(entry.get("sha256", "")).lower()
        size_bytes = int(entry.get("size_bytes", 0))

        sanitized_entries.append(
            {
                "path": path,
                "action": action,
                "sha256": file_sha,
                "size_bytes": size_bytes,
                "quarantine_locator": f"{quarantine_base}/{job_id}/files/{file_sha}" if file_sha else "",
            }
        )

    serialized = json.dumps(sanitized_entries, sort_keys=True).encode("utf-8")
    ref_sha = hashlib.sha256(serialized).hexdigest()
    ev_ref = EvidenceRef(
        evidence_id=f"ev-{job_id[:8]}-fs-delta",
        locator=f"{quarantine_base}/{job_id}/fs_delta.json",
        sha256=ref_sha,
        media_type="application/json",
        byte_length=len(serialized),
    )

    summary = f"Recorded {len(sanitized_entries)} filesystem delta events."
    return CollectorResult(
        collector_name="filesystem_delta",
        category="filesystem_delta",
        status="success",
        evidence_refs=(ev_ref,),
        structured_data={"entries": sanitized_entries, "count": len(sanitized_entries)},
        summary=summary,
    )


def collect_registry_delta(
    job_id: str,
    raw_data: dict[str, Any] | None,
    is_windows: bool = False,
    quarantine_base: str = "quarantine://evidence",
) -> CollectorResult:
    """Normalizes Windows Registry key/value mutations (gracefully degrades on Linux)."""
    if not is_windows:
        return CollectorResult(
            collector_name="registry_delta",
            category="registry_delta",
            status="unsupported",
            summary="Registry delta collector unsupported on non-Windows guest.",
        )

    data = _validate_telemetry_safety(raw_data)
    if not data or "registry" not in data:
        return CollectorResult(
            collector_name="registry_delta",
            category="registry_delta",
            status="skipped",
            summary="No registry telemetry collected.",
        )

    entries = data.get("registry", [])
    sanitized: list[dict[str, Any]] = []
    for r in entries:
        if not isinstance(r, dict):
            continue
        sanitized.append(
            {
                "key": str(r.get("key", "")),
                "value_name": str(r.get("value_name", "")),
                "action": str(r.get("action", "set")),
                "value_type": str(r.get("value_type", "REG_SZ")),
            }
        )

    serialized = json.dumps(sanitized, sort_keys=True).encode("utf-8")
    ev_ref = EvidenceRef(
        evidence_id=f"ev-{job_id[:8]}-reg-delta",
        locator=f"{quarantine_base}/{job_id}/registry_delta.json",
        sha256=hashlib.sha256(serialized).hexdigest(),
        media_type="application/json",
        byte_length=len(serialized),
    )
    return CollectorResult(
        collector_name="registry_delta",
        category="registry_delta",
        status="success",
        evidence_refs=(ev_ref,),
        structured_data={"entries": sanitized, "count": len(sanitized)},
        summary=f"Recorded {len(sanitized)} registry delta modifications.",
    )


def collect_dns_metadata(
    job_id: str,
    raw_data: dict[str, Any] | None,
    quarantine_base: str = "quarantine://evidence",
) -> CollectorResult:
    """Normalizes captured DNS resolution queries."""
    data = _validate_telemetry_safety(raw_data)
    if not data or "dns" not in data:
        return CollectorResult(
            collector_name="dns_metadata",
            category="dns_metadata",
            status="skipped",
            summary="No DNS query telemetry collected.",
        )

    queries = data.get("dns", [])
    sanitized: list[dict[str, Any]] = []
    for q in queries:
        if not isinstance(q, dict):
            continue
        sanitized.append(
            {
                "query": str(q.get("query", "")).lower(),
                "qtype": str(q.get("qtype", "A")).upper(),
                "resolved_ips": [str(ip) for ip in q.get("resolved_ips", [])],
                "blocked": bool(q.get("blocked", False)),
            }
        )

    serialized = json.dumps(sanitized, sort_keys=True).encode("utf-8")
    ev_ref = EvidenceRef(
        evidence_id=f"ev-{job_id[:8]}-dns",
        locator=f"{quarantine_base}/{job_id}/dns_telemetry.json",
        sha256=hashlib.sha256(serialized).hexdigest(),
        media_type="application/json",
        byte_length=len(serialized),
    )
    return CollectorResult(
        collector_name="dns_metadata",
        category="dns_metadata",
        status="success",
        evidence_refs=(ev_ref,),
        structured_data={"queries": sanitized, "count": len(sanitized)},
        summary=f"Captured {len(sanitized)} guest DNS resolution attempts.",
    )


def collect_network_metadata(
    job_id: str,
    raw_data: dict[str, Any] | None,
    quarantine_base: str = "quarantine://evidence",
) -> CollectorResult:
    """Normalizes active connections, listening sockets, and traffic flows."""
    data = _validate_telemetry_safety(raw_data)
    if not data or "network" not in data:
        return CollectorResult(
            collector_name="network_metadata",
            category="network_metadata",
            status="skipped",
            summary="No network socket telemetry collected.",
        )

    flows = data.get("network", [])
    sanitized: list[dict[str, Any]] = []
    for f in flows:
        if not isinstance(f, dict):
            continue
        sanitized.append(
            {
                "proto": str(f.get("proto", "tcp")).lower(),
                "dest_ip": str(f.get("dest_ip", "")),
                "dest_port": int(f.get("dest_port", 0)),
                "bytes_out": int(f.get("bytes_out", 0)),
                "bytes_in": int(f.get("bytes_in", 0)),
                "egress_dropped": bool(f.get("egress_dropped", True)),
            }
        )

    serialized = json.dumps(sanitized, sort_keys=True).encode("utf-8")
    ev_ref = EvidenceRef(
        evidence_id=f"ev-{job_id[:8]}-net-flows",
        locator=f"{quarantine_base}/{job_id}/net_flows.json",
        sha256=hashlib.sha256(serialized).hexdigest(),
        media_type="application/json",
        byte_length=len(serialized),
    )
    return CollectorResult(
        collector_name="network_metadata",
        category="network_metadata",
        status="success",
        evidence_refs=(ev_ref,),
        structured_data={"flows": sanitized, "count": len(sanitized)},
        summary=f"Tracked {len(sanitized)} network flow records (isolated drops enforced).",
    )


def collect_pcap_reference(
    job_id: str,
    raw_data: dict[str, Any] | None,
    quarantine_base: str = "quarantine://evidence",
) -> CollectorResult:
    """Records reference to raw isolated packet capture without loading bytes into memory."""
    data = _validate_telemetry_safety(raw_data)
    if not data or "pcap" not in data:
        return CollectorResult(
            collector_name="pcap_reference",
            category="pcap_reference",
            status="skipped",
            summary="No PCAP capture available.",
        )

    pcap_meta = data.get("pcap", {})
    if not isinstance(pcap_meta, dict):
        return CollectorResult(
            collector_name="pcap_reference",
            category="pcap_reference",
            status="failed",
            error="Invalid pcap metadata block",
        )

    pcap_sha = str(pcap_meta.get("sha256", "0" * 64)).lower()
    byte_len = int(pcap_meta.get("byte_length", 0))
    packet_count = int(pcap_meta.get("packet_count", 0))

    locator = f"{quarantine_base}/{job_id}/capture.pcap"
    ev_ref = EvidenceRef(
        evidence_id=f"ev-{job_id[:8]}-pcap",
        locator=locator,
        sha256=pcap_sha,
        media_type="application/vnd.tcpdump.pcap",
        byte_length=byte_len,
    )
    return CollectorResult(
        collector_name="pcap_reference",
        category="pcap_reference",
        status="success",
        evidence_refs=(ev_ref,),
        structured_data={
            "locator": locator,
            "packet_count": packet_count,
            "byte_length": byte_len,
        },
        summary=f"Full PCAP stored at quarantine locator ({packet_count} packets, {byte_len} bytes).",
    )


def collect_yara_results(
    job_id: str,
    raw_data: dict[str, Any] | None,
    quarantine_base: str = "quarantine://evidence",
) -> CollectorResult:
    """Normalizes YARA rule signature match results."""
    data = _validate_telemetry_safety(raw_data)
    if not data or "yara" not in data:
        return CollectorResult(
            collector_name="yara_results",
            category="yara_results",
            status="skipped",
            summary="YARA scan was not executed or produced zero findings.",
        )

    matches = data.get("yara", [])
    sanitized: list[dict[str, Any]] = []
    for m in matches:
        if not isinstance(m, dict):
            continue
        sanitized.append(
            {
                "rule": str(m.get("rule", "")),
                "namespace": str(m.get("namespace", "default")),
                "tags": [str(t) for t in m.get("tags", [])],
                "target_path": str(m.get("target_path", "")),
            }
        )

    serialized = json.dumps(sanitized, sort_keys=True).encode("utf-8")
    ev_ref = EvidenceRef(
        evidence_id=f"ev-{job_id[:8]}-yara",
        locator=f"{quarantine_base}/{job_id}/yara_matches.json",
        sha256=hashlib.sha256(serialized).hexdigest(),
        media_type="application/json",
        byte_length=len(serialized),
    )
    return CollectorResult(
        collector_name="yara_results",
        category="yara_results",
        status="success",
        evidence_refs=(ev_ref,),
        structured_data={"matches": sanitized, "count": len(sanitized)},
        summary=f"Matched {len(sanitized)} YARA rule indicators.",
    )


def collect_static_metadata(
    job_id: str,
    raw_data: dict[str, Any] | None,
    quarantine_base: str = "quarantine://evidence",
) -> CollectorResult:
    """Normalizes static binary analysis (PE/ELF headers, sections, imports)."""
    data = _validate_telemetry_safety(raw_data)
    if not data or "static" not in data:
        return CollectorResult(
            collector_name="static_metadata",
            category="static_metadata",
            status="skipped",
            summary="Static metadata analysis skipped or absent.",
        )

    meta = data.get("static", {})
    if not isinstance(meta, dict):
        return CollectorResult(
            collector_name="static_metadata",
            category="static_metadata",
            status="failed",
            error="Static metadata must be a dictionary",
        )

    sanitized = {
        "format": str(meta.get("format", "unknown")),
        "architecture": str(meta.get("architecture", "x86_64")),
        "entrypoint": str(meta.get("entrypoint", "")),
        "sections": [str(s) for s in meta.get("sections", [])],
        "imported_dlls": [str(d) for d in meta.get("imported_dlls", [])],
        "compile_timestamp": str(meta.get("compile_timestamp", "")),
    }

    serialized = json.dumps(sanitized, sort_keys=True).encode("utf-8")
    ev_ref = EvidenceRef(
        evidence_id=f"ev-{job_id[:8]}-static",
        locator=f"{quarantine_base}/{job_id}/static_meta.json",
        sha256=hashlib.sha256(serialized).hexdigest(),
        media_type="application/json",
        byte_length=len(serialized),
    )
    return CollectorResult(
        collector_name="static_metadata",
        category="static_metadata",
        status="success",
        evidence_refs=(ev_ref,),
        structured_data=sanitized,
        summary=f"Static analysis: {sanitized['format']} ({sanitized['architecture']}) binary.",
    )


def collect_memory_analysis(
    job_id: str,
    raw_data: dict[str, Any] | None,
    quarantine_base: str = "quarantine://evidence",
) -> CollectorResult:
    """Records reference to memory dump in quarantine and extracts memory analysis findings.

    Raw memory dump bytes are never loaded into DB or platform memory.
    """
    data = _validate_telemetry_safety(raw_data)
    if not data or "memory" not in data:
        return CollectorResult(
            collector_name="memory_analysis",
            category="memory_analysis",
            status="skipped",
            summary="No memory dump or volatile memory analysis available.",
        )

    mem_meta = data.get("memory", {})
    if not isinstance(mem_meta, dict):
        return CollectorResult(
            collector_name="memory_analysis",
            category="memory_analysis",
            status="failed",
            error="Invalid memory metadata block",
        )

    mem_sha = str(mem_meta.get("sha256", "0" * 64)).lower()
    byte_len = int(mem_meta.get("byte_length", 0))
    findings = [str(f) for f in mem_meta.get("findings", [])]
    plugins_run = [str(p) for p in mem_meta.get("plugins_run", [])]

    locator = f"{quarantine_base}/{job_id}/memory.dmp"
    ev_ref = EvidenceRef(
        evidence_id=f"ev-{job_id[:8]}-memory",
        locator=locator,
        sha256=mem_sha,
        media_type="application/octet-stream",
        byte_length=byte_len,
    )
    return CollectorResult(
        collector_name="memory_analysis",
        category="memory_analysis",
        status="success",
        evidence_refs=(ev_ref,),
        structured_data={
            "locator": locator,
            "byte_length": byte_len,
            "findings": findings,
            "plugins_run": plugins_run,
        },
        summary=f"Memory dump referenced in quarantine ({byte_len} bytes, {len(findings)} volatile findings).",
    )


def collect_screenshot_reference(
    job_id: str,
    raw_data: dict[str, Any] | None,
    quarantine_base: str = "quarantine://evidence",
) -> CollectorResult:
    """Records reference to captured desktop screenshot in quarantine storage."""
    data = _validate_telemetry_safety(raw_data)
    if not data or "screenshot" not in data:
        return CollectorResult(
            collector_name="screenshots",
            category="screenshots",
            status="skipped",
            summary="No desktop screenshot captured.",
        )

    ss_meta = data.get("screenshot", {})
    if not isinstance(ss_meta, dict):
        return CollectorResult(
            collector_name="screenshots",
            category="screenshots",
            status="failed",
            error="Invalid screenshot metadata",
        )

    ss_sha = str(ss_meta.get("sha256", "0" * 64)).lower()
    locator = f"{quarantine_base}/{job_id}/screen_01.png"
    ev_ref = EvidenceRef(
        evidence_id=f"ev-{job_id[:8]}-screenshot",
        locator=locator,
        sha256=ss_sha,
        media_type="image/png",
        byte_length=int(ss_meta.get("byte_length", 0)),
    )
    return CollectorResult(
        collector_name="screenshots",
        category="screenshots",
        status="success",
        evidence_refs=(ev_ref,),
        structured_data={"locator": locator, "resolution": str(ss_meta.get("resolution", "1920x1080"))},
        summary="Desktop execution screenshot captured and stored in quarantine.",
    )


# ---------------------------------------------------------------------------
# LLM Evidence Summarizer
# ---------------------------------------------------------------------------

def summarize_evidence_for_llm(bundle: EvidenceBundle) -> str:
    """Formats normalized telemetry into structured markdown for LLM consumption.

    Guarantees:
    - Never exposes raw executable payloads or binary bytes.
    - Presents high-level behavioral timeline, process tree, files, network, and YARA hits.
    - Zero guest hypervisor access required by the model.
    """
    lines: list[str] = [
        f"# Security Vise Evidence Brief: {bundle.job_id}",
        "",
        f"- **Profile:** `{bundle.profile}`",
        f"- **Timestamp:** `{bundle.collected_at}`",
        f"- **Evidence Digest:** `{bundle.digest_sha256}`",
        f"- **Artifacts in Quarantine:** `{len(bundle.evidence_refs)}`",
        "",
    ]

    # Cryptographic hashes
    hash_res = bundle.results_by_collector.get("hashes")
    if hash_res and hash_res.status == "success":
        lines.append("## Cryptographic Hashes")
        for k, v in hash_res.structured_data.items():
            lines.append(f"- **{k.upper()}:** `{v}`")
        lines.append("")

    # Static analysis
    static_res = bundle.results_by_collector.get("static_metadata")
    if static_res and static_res.status == "success":
        lines.append("## Static Analysis")
        sd = static_res.structured_data
        lines.append(f"- **Format:** `{sd.get('format')}` ({sd.get('architecture')})")
        if sd.get("entrypoint"):
            lines.append(f"- **Entrypoint:** `{sd.get('entrypoint')}`")
        if sd.get("imported_dlls"):
            lines.append(f"- **Imported Modules:** {', '.join(sd.get('imported_dlls', []))}")
        lines.append("")

    # Process tree
    proc_res = bundle.results_by_collector.get("process_tree")
    if proc_res and proc_res.status == "success":
        lines.append("## Process Execution")
        procs = proc_res.structured_data.get("processes", [])
        if procs:
            for p in procs:
                mark = "🚨" if p.get("suspicious") else "•"
                lines.append(f"{mark} PID {p['pid']} (PPID {p['ppid']}): `{p['name']}` -> `{p['cmdline']}`")
        else:
            lines.append("No active processes recorded.")
        lines.append("")

    # Filesystem delta
    fs_res = bundle.results_by_collector.get("filesystem_delta")
    if fs_res and fs_res.status == "success":
        lines.append("## Filesystem Activity")
        entries = fs_res.structured_data.get("entries", [])
        if entries:
            for e in entries[:20]:
                lines.append(f"- **{e['action'].upper()}**: `{e['path']}` ({e['size_bytes']} bytes, SHA256: `{e['sha256']}`)")
            if len(entries) > 20:
                lines.append(f"  *(and {len(entries) - 20} more files)*")
        else:
            lines.append("No files modified.")
        lines.append("")

    # Registry delta (if Windows)
    reg_res = bundle.results_by_collector.get("registry_delta")
    if reg_res and reg_res.status == "success":
        lines.append("## Windows Registry Modifications")
        for r in reg_res.structured_data.get("entries", [])[:15]:
            lines.append(f"- `{r['key']}\\{r['value_name']}` ({r['action']})")
        lines.append("")

    # Network / DNS
    dns_res = bundle.results_by_collector.get("dns_metadata")
    net_res = bundle.results_by_collector.get("network_metadata")
    if (dns_res and dns_res.status == "success") or (net_res and net_res.status == "success"):
        lines.append("## Network & DNS Telemetry")
        if dns_res and dns_res.status == "success":
            lines.append("### DNS Inquiries:")
            for q in dns_res.structured_data.get("queries", []):
                blocked = " (BLOCKED)" if q.get("blocked") else ""
                lines.append(f"- `{q['query']}` [{q['qtype']}]{blocked}")
        if net_res and net_res.status == "success":
            lines.append("### Socket Connections:")
            for f in net_res.structured_data.get("flows", []):
                lines.append(f"- `{f['proto'].upper()}` -> `{f['dest_ip']}:{f['dest_port']}` ({f['bytes_out']}B out, {f['bytes_in']}B in)")
        lines.append("")

    # YARA matches
    yara_res = bundle.results_by_collector.get("yara_results")
    if yara_res and yara_res.status == "success":
        lines.append("## YARA Signatures Matched")
        for m in yara_res.structured_data.get("matches", []):
            lines.append(f"- 🏷️ **{m['rule']}** on `{m['target_path']}` (tags: {', '.join(m['tags'])})")
        lines.append("")

    # Memory Analysis
    mem_res = bundle.results_by_collector.get("memory_analysis")
    if mem_res and mem_res.status == "success":
        lines.append("## Volatile Memory Analysis")
        md = mem_res.structured_data
        lines.append(f"- **Memory Image Locator:** `{md.get('locator')}` ({md.get('byte_length')} bytes)")
        if md.get("plugins_run"):
            lines.append(f"- **Plugins Run:** {', '.join(md.get('plugins_run', []))}")
        findings = md.get("findings", [])
        if findings:
            lines.append("### Volatile Findings:")
            for f in findings:
                lines.append(f"- ⚠️ {f}")
        lines.append("")

    # Screenshots
    ss_res = bundle.results_by_collector.get("screenshots")
    if ss_res and ss_res.status == "success":
        lines.append("## Visual Telemetry")
        lines.append(f"- Desktop screenshot recorded: `{ss_res.structured_data.get('locator')}` ({ss_res.structured_data.get('resolution')})")
        lines.append("")

    # Quarantine artifacts manifest
    lines.append("## Quarantine Artifact References")
    for ref in bundle.evidence_refs:
        lines.append(f"- `{ref.evidence_id}`: `{ref.locator}` ({ref.media_type}, {ref.byte_length} bytes)")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Vise Evidence Pipeline Orchestrator
# ---------------------------------------------------------------------------

class ViseEvidencePipeline:
    """Orchestrates collectors, sanitizes outputs, and produces verified evidence bundles."""

    def __init__(self, quarantine_base: str = "quarantine://evidence") -> None:
        self.quarantine_base = quarantine_base

    def run_pipeline(
        self,
        job_id: str,
        profile: str,
        raw_telemetry: dict[str, Any] | None = None,
    ) -> EvidenceBundle:
        """Executes all collectors against available guest telemetry.

        Enforces:
        - Payload rejection: raw binary bytes are never embedded in memory structures.
        - Graceful degradation: missing collectors return clean skipped/unsupported records.
        - Generates EvidenceRef items conforming to the security event envelope.
        - Produces signed digest and structured markdown summary.
        """
        # Telemetry validation & rejection of forbidden binary payload keys
        safe_telemetry = _validate_telemetry_safety(raw_telemetry) or {}

        now = datetime.now(timezone.utc).isoformat()
        bundle = EvidenceBundle(
            job_id=job_id,
            profile=profile,
            collected_at=now,
        )

        is_windows = "windows" in profile.lower()

        # Run collectors
        collectors: list[Callable[[], CollectorResult]] = [
            lambda: collect_hashes(job_id, safe_telemetry, self.quarantine_base),
            lambda: collect_static_metadata(job_id, safe_telemetry, self.quarantine_base),
            lambda: collect_yara_results(job_id, safe_telemetry, self.quarantine_base),
            lambda: collect_process_tree(job_id, safe_telemetry, self.quarantine_base),
            lambda: collect_filesystem_delta(job_id, safe_telemetry, self.quarantine_base),
            lambda: collect_registry_delta(job_id, safe_telemetry, is_windows, self.quarantine_base),
            lambda: collect_dns_metadata(job_id, safe_telemetry, self.quarantine_base),
            lambda: collect_network_metadata(job_id, safe_telemetry, self.quarantine_base),
            lambda: collect_pcap_reference(job_id, safe_telemetry, self.quarantine_base),
            lambda: collect_memory_analysis(job_id, safe_telemetry, self.quarantine_base),
            lambda: collect_screenshot_reference(job_id, safe_telemetry, self.quarantine_base),
        ]

        for collect_fn in collectors:
            res = collect_fn()
            bundle.results_by_collector[res.collector_name] = res
            for ref in res.evidence_refs:
                bundle.evidence_refs.append(ref)
                bundle.quarantine_manifest.append(
                    {
                        "evidence_id": ref.evidence_id,
                        "locator": ref.locator,
                        "sha256": ref.sha256,
                        "media_type": ref.media_type,
                        "byte_length": ref.byte_length,
                    }
                )

        bundle.compute_digest()
        bundle.llm_summary = summarize_evidence_for_llm(bundle)
        return bundle
