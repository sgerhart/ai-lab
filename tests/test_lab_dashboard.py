"""Status dashboard payload stays redacted and uses live module facts."""

from __future__ import annotations

import json
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.connect import parse_ollama_installed, parse_ollama_loaded  # noqa: E402
from ai_lab_platform.host_resources import parse_memory_free_percent  # noqa: E402
from ai_lab_platform.lab_dashboard import (  # noqa: E402
    build_lab_dashboard,
    fetch_remote_resources,
    sanitize_resources,
)


def _dashboard() -> dict:
    return build_lab_dashboard(
        mini_resources={
            "available": True,
            "chip": "Apple M1",
            "cpu_count": 8,
            "memory_bytes": 17179869184,
            "memory_free_percent": 64,
            "disk_bytes": 494384795648,
            "disk_free_bytes": 268271935488,
            "command": "must-not-leak",
        },
        services={"postgres": True, "redis": True, "qdrant": False},
        connect={
            "ollama": {
                "http_ok": True,
                "url_host": "must-not-leak",
                "installed": [
                    {"name": "llama3.2:3b", "size_bytes": 2019393189, "parameter_size": "3.2B"}
                ],
                "loaded": [],
            },
            "jupyter": {"http_ok": True, "port_open": True},
            "studio_worker": {"http_ok": False},
        },
        studio_resources={"available": False, "reason": "Studio has not reported memory or disk yet."},
        memory={"backend": "qdrant", "ok": True, "documents": 3},
        scheduler_last_tick=None,
        antares_jobs_up=True,
        antares_completions_up=False,
        frontier_configured=0,
        frontier_authorized=False,
        mcp_servers=[{"id": "files", "label": "Files", "enabled": True, "command": "must-not-leak"}],
        local_models=[{"model": "llama3.2:3b", "available": True}],
    )


class DashboardTests(unittest.TestCase):
    def test_memory_pressure_percent(self) -> None:
        text = "Pages free: 1\nSystem-wide memory free percentage: 64%\n"
        self.assertEqual(parse_memory_free_percent(text), 64)
        self.assertIsNone(parse_memory_free_percent("no percent"))

    def test_sanitize_drops_extra_fields(self) -> None:
        clean = sanitize_resources(
            {"available": True, "chip": "Apple M1", "memory_bytes": 16, "note": "must-not-leak"},
            reason="missing",
        )
        self.assertNotIn("note", clean)
        self.assertNotIn("must-not-leak", json.dumps(clean))

    def test_dashboard_omits_secrets_and_addresses(self) -> None:
        body = json.dumps(_dashboard())
        self.assertNotIn("must-not-leak", body)
        self.assertIn("llama3.2:3b", body)
        modules = {row["id"]: row for row in _dashboard()["modules"]}
        self.assertEqual(modules["chat"]["state"], "ready")
        self.assertEqual(modules["memory"]["state"], "ready")
        self.assertEqual(modules["antares"]["state"], "limited")
        self.assertEqual(modules["jupyter"]["open"], "jupyter")
        self.assertNotIn("command", modules["mcp"])

    def test_ollama_parsers(self) -> None:
        installed = parse_ollama_installed(
            {"models": [{"name": "llama3.2:3b", "size": 10, "digest": "abc", "details": {"parameter_size": "3.2B"}}]}
        )
        self.assertEqual(installed[0]["name"], "llama3.2:3b")
        self.assertNotIn("digest", installed[0])
        loaded = parse_ollama_loaded({"models": [{"name": "llama3.2:3b", "size": 10}]})
        self.assertEqual(loaded[0]["size_bytes"], 10)

    def test_remote_resources_drop_unknown_fields(self) -> None:
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802
                raw = json.dumps(
                    {"available": True, "chip": "Apple M5 Max", "memory_bytes": 64, "secret": "must-not-leak"}
                ).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def log_message(self, fmt: str, *args: object) -> None:
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            body = fetch_remote_resources(f"http://127.0.0.1:{port}")
            self.assertTrue(body["available"])
            self.assertEqual(body["chip"], "Apple M5 Max")
            self.assertNotIn("must-not-leak", json.dumps(body))
            denied = fetch_remote_resources("file:///tmp/nope")
            self.assertFalse(denied["available"])
        finally:
            server.shutdown()


if __name__ == "__main__":
    unittest.main()
