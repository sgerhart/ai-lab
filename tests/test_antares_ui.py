"""Antares Studio client + control-plane routes (IWO-049)."""

from __future__ import annotations

import json
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from ai_lab_platform.antares_client import AntaresStudioClient
from ai_lab_platform.control_app import create_control_app
from ai_lab_platform.settings import Settings


class _FakeJobHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *_args):  # noqa: ANN002
        return

    def _json(self, code: int, body):
        raw = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):  # noqa: N802
        if self.path in ("/health", "/v1/health"):
            self._json(200, {"ok": True, "role": "antares-jobs"})
            return
        if self.path == "/v1/runs":
            self._json(200, {"runs": [{"id": "abc", "status": "completed", "cwe": "CWE-78", "findings": []}]})
            return
        if self.path.startswith("/v1/runs/") and self.path.endswith("/report"):
            self._json(200, {"findings": [{"file_path": "app.py", "cwe_ids": ["CWE-78"]}]})
            return
        if self.path.startswith("/v1/runs/"):
            self._json(200, {"id": "abc", "status": "completed", "findings": [{"file_path": "app.py"}]})
            return
        self._json(404, {"error": "not found"})

    def do_POST(self):  # noqa: N802
        n = int(self.headers.get("Content-Length") or "0")
        _ = self.rfile.read(n)
        if self.path == "/v1/runs":
            self._json(202, {"id": "abc", "status": "queued", "cwe": "CWE-78", "findings": []})
            return
        self._json(404, {"error": "not found"})


class AntaresClientTests(unittest.TestCase):
    def setUp(self) -> None:
        self.httpd = HTTPServer(("127.0.0.1", 0), _FakeJobHandler)
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.port}"

    def tearDown(self) -> None:
        self.httpd.shutdown()

    def test_status_and_start(self) -> None:
        client = AntaresStudioClient(job_url=self.base, completions_url="")
        st = client.status()
        self.assertTrue(st["configured"])
        self.assertEqual(st["jobs"]["http"], 200)
        code, job = client.start_run(cwe="CWE-78")
        self.assertEqual(code, 202)
        self.assertEqual(job["id"], "abc")


class AntaresApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.httpd = HTTPServer(("127.0.0.1", 0), _FakeJobHandler)
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        base = f"http://127.0.0.1:{self.port}"
        from fastapi.testclient import TestClient

        settings = Settings(
            api_token="test-token",
            auth_mode="token",
            antares_job_url=base,
            antares_completions_url="",
            agent_worker=False,
        )
        db = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
        db.close()
        from ai_lab_platform.store import SqliteStore

        self.app = create_control_app(
            store=SqliteStore(Path(db.name)),
            settings=settings,
            token="test-token",
        )
        self.client = TestClient(self.app)
        self.headers = {"Authorization": "Bearer test-token"}

    def tearDown(self) -> None:
        self.httpd.shutdown()

    def test_page_and_routes(self) -> None:
        page = self.client.get("/antares")
        self.assertEqual(page.status_code, 200)
        self.assertIn("Antares", page.text)
        st = self.client.get("/v1/antares/status", headers=self.headers)
        self.assertEqual(st.status_code, 200)
        self.assertTrue(st.json()["configured"])
        started = self.client.post(
            "/v1/antares/runs",
            headers=self.headers,
            json={"cwe": "CWE-78"},
        )
        self.assertEqual(started.status_code, 200)
        self.assertEqual(started.json()["id"], "abc")
        listing = self.client.get("/v1/antares/runs", headers=self.headers)
        self.assertEqual(listing.status_code, 200)
        self.assertTrue(listing.json()["runs"])


class VulnLocalizePolicyTests(unittest.TestCase):
    def test_no_write_tools(self) -> None:
        from ai_lab_platform.policy import load_policy

        policy = load_policy("vuln-localize")
        self.assertTrue(policy.read_only)
        self.assertEqual(policy.privileged_tools, ())
        for bad in ("shell_write", "compose_apply", "memory_write", "git_push"):
            self.assertNotIn(bad, policy.allowed_tools)


if __name__ == "__main__":
    unittest.main()
