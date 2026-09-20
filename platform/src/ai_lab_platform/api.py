"""Loopback HTTP API. Binds 127.0.0.1 only. Not a deployed M1 service."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .orchestrator import Orchestrator
from .policy import load_policy
from .store import SqliteStore
from .work_order import Status, WorkOrder
from .worker import tick


class App:
    def __init__(
        self,
        orch: Orchestrator,
        *,
        workspace_root: Path,
        artifact_root: Path,
        agents_root: Path | None = None,
        token: str = "",
    ) -> None:
        self.orch = orch
        self.workspace_root = workspace_root
        self.artifact_root = artifact_root
        self.agents_root = agents_root
        self.token = token


def _dumps(payload: Any) -> bytes:
    return json.dumps(payload, indent=2).encode("utf-8")


def make_handler(app: App) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args: object) -> None:
            return

        def _auth(self) -> bool:
            if not app.token:
                return True
            header = self.headers.get("Authorization", "")
            return header == f"Bearer {app.token}"

        def _send(self, code: int, payload: Any) -> None:
            body = _dumps(payload)
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _read_json(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length") or "0")
            if length <= 0:
                return {}
            raw = self.rfile.read(length)
            data = json.loads(raw.decode("utf-8"))
            if not isinstance(data, dict):
                raise ValueError("JSON object required")
            return data

        def do_GET(self) -> None:  # noqa: N802
            if not self._auth():
                self._send(401, {"error": "unauthorized"})
                return
            path = urlparse(self.path).path
            if path == "/health":
                self._send(200, {"ok": True, "service": "ai-lab-harness", "deployed": False})
                return
            if path == "/work-orders":
                items = [o.to_dict() for o in app.orch.store.list()]
                self._send(200, {"work_orders": items})
                return
            if path.startswith("/work-orders/"):
                order_id = path.split("/")[2]
                order = app.orch.store.get(order_id)
                if order is None:
                    self._send(404, {"error": "not found"})
                    return
                self._send(200, order.to_dict())
                return
            self._send(404, {"error": "not found"})

        def do_POST(self) -> None:  # noqa: N802
            if not self._auth():
                self._send(401, {"error": "unauthorized"})
                return
            path = urlparse(self.path).path
            try:
                body = self._read_json()
            except (ValueError, json.JSONDecodeError) as exc:
                self._send(400, {"error": str(exc)})
                return
            if path == "/work-orders":
                agent = str(body.get("agent") or "")
                objective = str(body.get("objective") or "")
                if not agent or not objective:
                    self._send(400, {"error": "agent and objective are required"})
                    return
                try:
                    policy = load_policy(agent, agents_root=app.agents_root)
                except (OSError, ValueError) as exc:
                    self._send(400, {"error": str(exc)})
                    return
                order = WorkOrder.new(
                    objective=objective,
                    agent=agent,
                    allowed_tools=list(policy.allowed_tools),
                    bounded_scope=str(body.get("bounded_scope") or ""),
                    input_references=list(body.get("input_references") or []),
                    completion_criteria=str(body.get("completion_criteria") or ""),
                )
                order = app.orch.submit(order)
                self._send(201, order.to_dict())
                return
            if path == "/worker/tick":
                result = tick(
                    app.orch,
                    workspace_root=app.workspace_root,
                    artifact_root=app.artifact_root,
                    agents_root=app.agents_root,
                )
                self._send(200, {"order": None if result is None else result.to_dict()})
                return
            if path.endswith("/approve"):
                order_id = path.split("/")[2]
                tools = list(body.get("tools") or [])
                try:
                    order = app.orch.approve(order_id, tools)
                except (KeyError, ValueError) as exc:
                    self._send(400, {"error": str(exc)})
                    return
                self._send(200, order.to_dict())
                return
            if path.endswith("/cancel"):
                order_id = path.split("/")[2]
                try:
                    order = app.orch.cancel(order_id)
                except (KeyError, ValueError) as exc:
                    self._send(400, {"error": str(exc)})
                    return
                self._send(200, order.to_dict())
                return
            self._send(404, {"error": "not found"})

    return Handler


def serve(
    db_path: Path,
    *,
    host: str = "127.0.0.1",
    port: int = 8088,
    workspace_root: Path | None = None,
    artifact_root: Path | None = None,
    token: str = "",
) -> ThreadingHTTPServer:
    if host not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("API may only bind loopback")
    store = SqliteStore(db_path)
    orch = Orchestrator(store)
    orch.hydrate_queue()
    orch.recover_running()
    app = App(
        orch,
        workspace_root=workspace_root or Path.cwd(),
        artifact_root=artifact_root or Path(db_path).parent / "artifacts",
        token=token,
    )
    httpd = ThreadingHTTPServer((host, port), make_handler(app))
    return httpd
