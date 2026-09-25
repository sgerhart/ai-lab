"""Local macOS memory and disk snapshot. No hostnames, addresses, or secrets."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from typing import Any

_FREE_RE = re.compile(r"System-wide memory free percentage:\s*(\d{1,3})%")
_CHIP_RE = re.compile(r"^[A-Za-z0-9 .+-]{1,80}$")


def parse_memory_free_percent(text: str) -> int | None:
    match = _FREE_RE.search(text or "")
    if not match:
        return None
    value = int(match.group(1))
    if value > 100:
        return None
    return value


def _sysctl(name: str) -> str:
    result = subprocess.run(
        ["sysctl", "-n", name],
        check=False,
        capture_output=True,
        text=True,
        timeout=2,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def collect() -> dict[str, Any]:
    """Read this machine's chip, memory, and disk. Safe to show in the lab UI."""
    missing = {
        "available": False,
        "reason": "This machine did not report memory or disk.",
    }
    if sys.platform != "darwin":
        return missing
    try:
        mem_raw = _sysctl("hw.memsize")
        cpu_raw = _sysctl("hw.ncpu")
        chip = _sysctl("machdep.cpu.brand_string")
        pressure = subprocess.run(
            ["memory_pressure"],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
        usage = shutil.disk_usage("/")
    except (OSError, subprocess.TimeoutExpired):
        return missing

    memory_bytes = int(mem_raw) if mem_raw.isdigit() else None
    cpu_count = int(cpu_raw) if cpu_raw.isdigit() else None
    free_percent = parse_memory_free_percent(pressure.stdout)
    if memory_bytes is None or usage.total <= 0:
        return missing
    return {
        "available": True,
        "chip": chip if _CHIP_RE.match(chip) else None,
        "cpu_count": cpu_count,
        "memory_bytes": memory_bytes,
        "memory_free_percent": free_percent,
        "disk_bytes": usage.total,
        "disk_free_bytes": usage.free,
    }
