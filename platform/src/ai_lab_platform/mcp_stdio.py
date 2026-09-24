"""Stdio MCP JSON-RPC client (FEAT-013 / IWO-029).

Speaks the Model Context Protocol over stdin/stdout with Content-Length framing.
Short-lived processes only — no connection pool in this IWO.
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import threading
import time
from typing import Any


class McpTransportError(RuntimeError):
    """stdio MCP process or protocol failure."""


_PROTOCOL = "2024-11-05"
_DEFAULT_TIMEOUT = 30.0


def _encode_message(msg: dict[str, Any]) -> bytes:
    body = json.dumps(msg, separators=(",", ":")).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
    return header + body


def _read_message(stdout: Any, *, deadline: float) -> dict[str, Any]:
    """Read one Content-Length framed JSON-RPC message from a binary stdout."""
    headers: dict[str, str] = {}
    while True:
        if time.monotonic() > deadline:
            raise McpTransportError("timeout reading MCP headers")
        line = stdout.readline()
        if not line:
            raise McpTransportError("MCP server closed stdout while reading headers")
        if line in (b"\r\n", b"\n"):
            break
        try:
            text = line.decode("ascii", errors="replace").strip()
        except Exception as exc:  # noqa: BLE001
            raise McpTransportError(f"bad MCP header encoding: {exc}") from exc
        if ":" not in text:
            continue
        key, val = text.split(":", 1)
        headers[key.strip().lower()] = val.strip()
    if "content-length" not in headers:
        raise McpTransportError("MCP message missing Content-Length")
    try:
        length = int(headers["content-length"])
    except ValueError as exc:
        raise McpTransportError("invalid Content-Length") from exc
    if length < 0 or length > 8_000_000:
        raise McpTransportError("Content-Length out of range")
    chunks: list[bytes] = []
    remaining = length
    while remaining > 0:
        if time.monotonic() > deadline:
            raise McpTransportError("timeout reading MCP body")
        chunk = stdout.read(remaining)
        if not chunk:
            raise McpTransportError("MCP server closed stdout while reading body")
        chunks.append(chunk)
        remaining -= len(chunk)
    raw = b"".join(chunks)
    try:
        data = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise McpTransportError(f"invalid MCP JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise McpTransportError("MCP message must be a JSON object")
    return data


class StdioMcpSession:
    """One short-lived stdio MCP session."""

    def __init__(
        self,
        command: list[str],
        *,
        timeout_seconds: float = _DEFAULT_TIMEOUT,
        env: dict[str, str] | None = None,
    ) -> None:
        if not command or not command[0]:
            raise McpTransportError("empty MCP command")
        self.command = list(command)
        self.timeout_seconds = timeout_seconds
        self.env = env
        self._proc: subprocess.Popen[bytes] | None = None
        self._next_id = 1
        self._lock = threading.Lock()

    def __enter__(self) -> StdioMcpSession:
        self.open()
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def open(self) -> None:
        if self._proc is not None:
            return
        child_env = os.environ.copy()
        if self.env:
            child_env.update(self.env)
        try:
            self._proc = subprocess.Popen(
                self.command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=child_env,
                shell=False,
            )
        except OSError as exc:
            raise McpTransportError(f"failed to start MCP server: {exc}") from exc
        self._initialize()

    def close(self) -> None:
        proc = self._proc
        self._proc = None
        if proc is None:
            return
        for stream in (proc.stdin, proc.stdout, proc.stderr):
            try:
                if stream is not None:
                    stream.close()
            except Exception:  # noqa: BLE001
                pass
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except Exception:  # noqa: BLE001
            try:
                proc.kill()
            except Exception:  # noqa: BLE001
                pass

    def _deadline(self) -> float:
        return time.monotonic() + self.timeout_seconds

    def _request(self, method: str, params: dict[str, Any] | None = None) -> Any:
        if self._proc is None or self._proc.stdin is None or self._proc.stdout is None:
            raise McpTransportError("MCP session not open")
        with self._lock:
            req_id = self._next_id
            self._next_id += 1
            msg: dict[str, Any] = {
                "jsonrpc": "2.0",
                "id": req_id,
                "method": method,
            }
            if params is not None:
                msg["params"] = params
            self._proc.stdin.write(_encode_message(msg))
            self._proc.stdin.flush()
            deadline = self._deadline()
            while True:
                data = _read_message(self._proc.stdout, deadline=deadline)
                # Skip notifications (no id)
                if "id" not in data:
                    continue
                if data.get("id") != req_id:
                    continue
                if "error" in data:
                    err = data["error"]
                    raise McpTransportError(f"MCP error for {method}: {err}")
                return data.get("result")

    def _notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        if self._proc is None or self._proc.stdin is None:
            raise McpTransportError("MCP session not open")
        msg: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        with self._lock:
            self._proc.stdin.write(_encode_message(msg))
            self._proc.stdin.flush()

    def _initialize(self) -> None:
        self._request(
            "initialize",
            {
                "protocolVersion": _PROTOCOL,
                "capabilities": {},
                "clientInfo": {"name": "ai-lab", "version": "0.2.0"},
            },
        )
        self._notify("notifications/initialized")

    def list_tools(self) -> list[dict[str, Any]]:
        result = self._request("tools/list", {})
        tools = []
        if isinstance(result, dict):
            for item in result.get("tools") or []:
                if isinstance(item, dict) and item.get("name"):
                    tools.append(item)
        return tools

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        result = self._request(
            "tools/call",
            {"name": name, "arguments": arguments or {}},
        )
        if not isinstance(result, dict):
            return {"content": [{"type": "text", "text": str(result)}], "isError": False}
        return result


def build_command(command: str, args: list[str] | None = None) -> list[str]:
    """Build argv from stored command string + args (never shell)."""
    parts = shlex.split(command or "")
    if not parts:
        raise McpTransportError("MCP command is empty")
    return parts + list(args or [])


def observation_from_tool_result(result: dict[str, Any]) -> str:
    parts: list[str] = []
    for item in result.get("content") or []:
        if isinstance(item, dict):
            if item.get("type") == "text":
                parts.append(str(item.get("text") or ""))
            else:
                parts.append(json.dumps(item, ensure_ascii=False))
        else:
            parts.append(str(item))
    text = "\n".join(p for p in parts if p).strip()
    if result.get("isError"):
        return text or "MCP tool returned isError"
    return text or json.dumps(result, ensure_ascii=False)[:4000]


__all__ = [
    "McpTransportError",
    "StdioMcpSession",
    "build_command",
    "observation_from_tool_result",
]
