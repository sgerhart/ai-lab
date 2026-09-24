"""Stdio MCP *server* exposing a small lab API tool set (FEAT-005 / IWO-042).

This is the opposite of agents-as-MCP-clients (FEAT-013). IDEs connect here;
tools call the control plane over HTTP with ``AI_LAB_API_TOKEN``.

Run::

    export AI_LAB_API_BASE=http://127.0.0.1:8088
    export AI_LAB_API_TOKEN=...   # or session from login
    python -m ai_lab_platform.lab_mcp_server

Cursor example (operator machine, no secrets in Git)::

    {
      "mcpServers": {
        "ai-lab": {
          "command": "/path/to/ai-lab/scripts/lab-mcp-server.sh",
          "env": {
            "AI_LAB_API_BASE": "http://mac-mini:8088",
            "AI_LAB_API_TOKEN": "(from ~/.ai-lab or login session)"
          }
        }
      }
    }
"""

from __future__ import annotations

import json
import sys
from typing import Any, Callable

from .lab_api_client import LabApiClient, LabApiError

_PROTOCOL = "2024-11-05"
_SERVER_NAME = "ai-lab"
_SERVER_VERSION = "0.1.0"

ToolHandler = Callable[[dict[str, Any], LabApiClient], str]


def _tool_defs() -> list[dict[str, Any]]:
    return [
        {
            "name": "lab_health",
            "description": "Control-plane /health (no secrets).",
            "inputSchema": {"type": "object", "properties": {}},
        },
        {
            "name": "lab_memory_search",
            "description": "Search scoped lab memory (FEAT-008). Empty results must not invent citations.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 20},
                },
                "required": ["query"],
            },
        },
        {
            "name": "lab_memory_upsert",
            "description": "Upsert a cited memory document (source required).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "source": {"type": "string"},
                    "id": {"type": "string"},
                },
                "required": ["text", "source"],
            },
        },
        {
            "name": "lab_scheduler_status",
            "description": "Personal-agent schedule status (FEAT-009).",
            "inputSchema": {"type": "object", "properties": {}},
        },
    ]


def _lab_health(_args: dict[str, Any], client: LabApiClient) -> str:
    return json.dumps(client.get("/health", auth=False), indent=2)


def _lab_memory_search(args: dict[str, Any], client: LabApiClient) -> str:
    query = str(args.get("query") or "").strip()
    limit = int(args.get("limit") or 5)
    return json.dumps(client.post("/v1/memory/search", {"query": query, "limit": limit}), indent=2)


def _lab_memory_upsert(args: dict[str, Any], client: LabApiClient) -> str:
    body: dict[str, Any] = {
        "text": str(args.get("text") or ""),
        "source": str(args.get("source") or ""),
    }
    if args.get("id"):
        body["id"] = str(args["id"])
    return json.dumps(client.post("/v1/memory/documents", body), indent=2)


def _lab_scheduler_status(_args: dict[str, Any], client: LabApiClient) -> str:
    return json.dumps(client.get("/v1/scheduler/status"), indent=2)


_HANDLERS: dict[str, ToolHandler] = {
    "lab_health": _lab_health,
    "lab_memory_search": _lab_memory_search,
    "lab_memory_upsert": _lab_memory_upsert,
    "lab_scheduler_status": _lab_scheduler_status,
}


def handle_message(msg: dict[str, Any], client: LabApiClient) -> dict[str, Any] | None:
    """Handle one JSON-RPC MCP message. Returns a response or None for notifications."""
    method = msg.get("method")
    req_id = msg.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": _PROTOCOL,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": _SERVER_NAME, "version": _SERVER_VERSION},
            },
        }

    if method == "notifications/initialized" or method == "initialized":
        return None

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"tools": _tool_defs()},
        }

    if method == "tools/call":
        params = msg.get("params") or {}
        name = str(params.get("name") or "")
        args = params.get("arguments") or {}
        if not isinstance(args, dict):
            args = {}
        handler = _HANDLERS.get(name)
        if handler is None:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"unknown tool {name}"},
            }
        try:
            text = handler(args, client)
            is_error = False
        except LabApiError as exc:
            text = str(exc)
            is_error = True
        except Exception as exc:  # noqa: BLE001
            text = f"tool_error:{exc}"
            is_error = True
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [{"type": "text", "text": text}],
                "isError": is_error,
            },
        }

    if method == "ping":
        return {"jsonrpc": "2.0", "id": req_id, "result": {}}

    if req_id is not None:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"unknown method {method}"},
        }
    return None


def read_message(stdin: Any = None) -> dict[str, Any]:
    stdin = stdin or sys.stdin.buffer
    headers: dict[str, str] = {}
    while True:
        line = stdin.readline()
        if not line:
            raise EOFError
        if line in (b"\r\n", b"\n"):
            break
        text = line.decode("ascii", errors="replace").strip()
        if ":" in text:
            k, v = text.split(":", 1)
            headers[k.strip().lower()] = v.strip()
    n = int(headers["content-length"])
    body = stdin.read(n)
    return json.loads(body.decode("utf-8"))


def write_message(msg: dict[str, Any], stdout: Any = None) -> None:
    stdout = stdout or sys.stdout.buffer
    raw = json.dumps(msg, separators=(",", ":")).encode("utf-8")
    stdout.write(f"Content-Length: {len(raw)}\r\n\r\n".encode("ascii"))
    stdout.write(raw)
    stdout.flush()


def serve_stdio(client: LabApiClient | None = None) -> None:
    client = client or LabApiClient()
    while True:
        try:
            msg = read_message()
        except EOFError:
            break
        response = handle_message(msg, client)
        if response is not None:
            write_message(response)


def main() -> None:
    serve_stdio()


if __name__ == "__main__":
    main()
