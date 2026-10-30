"""Local macOS MCP Bridge for Steward.

Exposes governed, read-only tools to inspect local Markdown notes and
system status on the operator's Mac, bounded by Steward's See ceiling.
"""

from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_NOTES_DIR = Path.home() / ".ai-lab" / "notes"
MAX_READ_BYTES = 64 * 1024  # 64 KB limit for safe read-only context


def get_notes_root() -> Path:
    override = os.environ.get("STEWARD_MAC_NOTES_DIR")
    if override:
        return Path(override).expanduser().resolve()
    return DEFAULT_NOTES_DIR.expanduser().resolve()


def _resolve_safe_path(root: Path, subpath: str) -> Optional[Path]:
    try:
        norm = (root / subpath).resolve()
        norm.relative_to(root)
        return norm
    except (ValueError, RuntimeError):
        return None


def mac_notes_list(subpath: str = "") -> Dict[str, Any]:
    root = get_notes_root()
    if not root.exists():
        return {
            "root": str(root),
            "exists": False,
            "count": 0,
            "notes": [],
            "message": f"Notes directory {root} does not exist yet.",
        }

    target_dir = _resolve_safe_path(root, subpath)
    if target_dir is None or not target_dir.is_dir():
        return {
            "error": "Invalid subpath or path traversal denied",
            "root": str(root),
            "subpath": subpath,
            "notes": [],
        }

    items: List[Dict[str, Any]] = []
    for entry in sorted(target_dir.rglob("*.md")):
        if entry.is_file():
            rel = entry.relative_to(root).as_posix()
            stat = entry.stat()
            mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
            items.append({
                "path": rel,
                "name": entry.name,
                "size_bytes": stat.st_size,
                "modified": mtime,
            })

    return {
        "root": str(root),
        "count": len(items),
        "notes": items,
    }


def mac_notes_read(path: str) -> Dict[str, Any]:
    root = get_notes_root()
    target_file = _resolve_safe_path(root, path)
    if target_file is None:
        return {"error": "Path traversal denied or invalid path", "path": path}

    if not target_file.exists() or not target_file.is_file():
        return {"error": "File not found", "path": path}

    try:
        stat = target_file.stat()
        if stat.st_size > MAX_READ_BYTES:
            with open(target_file, "r", encoding="utf-8", errors="replace") as f:
                content = f.read(MAX_READ_BYTES)
            truncated = True
        else:
            with open(target_file, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            truncated = False

        mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
        return {
            "path": target_file.relative_to(root).as_posix(),
            "content": content,
            "size_bytes": stat.st_size,
            "truncated": truncated,
            "modified": mtime,
        }
    except Exception as exc:
        return {"error": f"Failed to read file: {exc}", "path": path}


def mac_notes_search(query: str, subpath: str = "") -> Dict[str, Any]:
    if not query or not query.strip():
        return {"error": "Query string cannot be empty", "matches": []}

    q = query.strip().lower()
    listing = mac_notes_list(subpath)
    if "notes" not in listing or not listing["notes"]:
        return {"query": query, "count": 0, "matches": []}

    root = Path(listing["root"])
    matches: List[Dict[str, Any]] = []

    for item in listing["notes"]:
        rel = item["path"]
        filepath = root / rel
        name_match = q in item["name"].lower()
        snippet = ""
        matched_content = False

        if filepath.exists() and filepath.is_file():
            try:
                with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                    text = f.read(MAX_READ_BYTES)
                idx = text.lower().find(q)
                if idx != -1:
                    matched_content = True
                    start = max(0, idx - 40)
                    end = min(len(text), idx + len(q) + 60)
                    snippet = text[start:end].replace("\n", " ")
            except Exception:
                pass

        if name_match or matched_content:
            matches.append({
                "path": rel,
                "name": item["name"],
                "name_match": name_match,
                "content_match": matched_content,
                "snippet": snippet,
                "modified": item.get("modified"),
            })

    return {
        "query": query,
        "count": len(matches),
        "matches": matches,
    }


def mac_system_status() -> Dict[str, Any]:
    battery_info = "unavailable"
    power_source = "unknown"
    if sys.platform == "darwin":
        try:
            res = subprocess.run(
                ["pmset", "-g", "batt"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if res.returncode == 0:
                lines = [line.strip() for line in res.stdout.strip().splitlines() if line.strip()]
                if lines:
                    power_source = lines[0]
                    if len(lines) > 1:
                        battery_info = lines[1]
        except Exception as exc:
            battery_info = f"pmset error: {exc}"

    return {
        "hostname": platform.node(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "power_source": power_source,
        "battery_info": battery_info,
        "notes_root": str(get_notes_root()),
        "time_utc": datetime.now(timezone.utc).isoformat(),
    }


def get_bridge_capabilities() -> List[Dict[str, Any]]:
    return [
        {
            "name": "mac_notes_list",
            "description": "List markdown note files in the operator's local Mac notes directory.",
            "permission_class": "read",
            "parameters": {
                "type": "object",
                "properties": {
                    "subpath": {
                        "type": "string",
                        "description": "Optional subdirectory within notes root",
                    }
                },
            },
        },
        {
            "name": "mac_notes_read",
            "description": "Read the text content of a markdown note on the operator's Mac.",
            "permission_class": "read",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path of the markdown note to read",
                    }
                },
                "required": ["path"],
            },
        },
        {
            "name": "mac_notes_search",
            "description": "Search local markdown notes on the operator's Mac for keywords or phrases.",
            "permission_class": "read",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Keywords or search term",
                    },
                    "subpath": {
                        "type": "string",
                        "description": "Optional subpath to narrow search",
                    },
                },
                "required": ["query"],
            },
        },
        {
            "name": "mac_system_status",
            "description": "Inspect local Mac hardware and power state (battery, AC power, host).",
            "permission_class": "read",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    ]


def handle_call(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    if tool_name == "mac_notes_list":
        return mac_notes_list(arguments.get("subpath", ""))
    elif tool_name == "mac_notes_read":
        return mac_notes_read(arguments.get("path", ""))
    elif tool_name == "mac_notes_search":
        return mac_notes_search(arguments.get("query", ""), arguments.get("subpath", ""))
    elif tool_name == "mac_system_status":
        return mac_system_status()
    else:
        return {"error": f"Unknown tool: {tool_name}"}


def run_stdio_server() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception as exc:
            resp = {"error": f"Invalid JSON: {exc}"}
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()
            continue

        method = req.get("method")
        msg_id = req.get("id")

        if method == "tools/list":
            result = {"tools": get_bridge_capabilities()}
            resp = {"jsonrpc": "2.0", "id": msg_id, "result": result}
        elif method == "tools/call":
            params = req.get("params", {})
            name = params.get("name", "")
            args = params.get("arguments", {})
            call_res = handle_call(name, args)
            resp = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"content": [{"type": "text", "text": json.dumps(call_res)}]},
            }
        elif method == "initialize":
            resp = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {"name": "steward-mac-bridge", "version": "1.0.0"},
                    "capabilities": {"tools": {}},
                },
            }
        else:
            resp = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            }

        sys.stdout.write(json.dumps(resp) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    run_stdio_server()
