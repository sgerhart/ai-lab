"""Lab connect hub (FEAT-012 / IWO-016)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.connect import (  # noqa: E402
    connect_status,
    jupyter_open_url,
    read_token_file,
)
from ai_lab_platform.settings import Settings  # noqa: E402
from ai_lab_platform.store import SqliteStore  # noqa: E402

try:
    from fastapi.testclient import TestClient
    from ai_lab_platform.control_app import create_control_app
except Exception as exc:  # pragma: no cover
    TestClient = None  # type: ignore[misc, assignment]
    create_control_app = None  # type: ignore[misc, assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


class ConnectHelperTests(unittest.TestCase):
    def test_jupyter_open_url(self) -> None:
        self.assertEqual(
            jupyter_open_url("http://mac-studio:8888", "abc"),
            "http://mac-studio:8888/lab?token=abc",
        )

    def test_read_token_file(self) -> None:
        with tempfile.NamedTemporaryFile("w", delete=False) as fh:
            fh.write("sekret\n")
            path = fh.name
        self.assertEqual(read_token_file(path), "sekret")
        self.assertEqual(read_token_file("/no/such/token"), "")

    def test_connect_status_redacted(self) -> None:
        status = connect_status(
            jupyter_url="http://127.0.0.1:9",
            ollama_url="http://127.0.0.1:9",
            jupyter_token="must-not-leak",
        )
        blob = str(status)
        self.assertNotIn("must-not-leak", blob)
        self.assertTrue(status["jupyter"]["token_configured"])
        self.assertFalse(status["jupyter"]["port_open"])


@unittest.skipUnless(TestClient is not None, f"fastapi testclient unavailable: {IMPORT_ERROR}")
class LabConnectAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
        self.tmp.close()
        self.token_file = tempfile.NamedTemporaryFile("w", delete=False)
        self.token_file.write("jupyter-secret-token")
        self.token_file.close()
        settings = Settings(
            studio_jupyter_url="http://mac-studio:8888",
            studio_ollama_url="http://mac-studio:11434",
            studio_jupyter_token_file=self.token_file.name,
            api_token="lab-token",
        )
        app = create_control_app(
            store=SqliteStore(self.tmp.name),
            token="lab-token",
            settings=settings,
        )
        self.client = TestClient(app)

    def test_lab_page(self) -> None:
        res = self.client.get("/lab")
        self.assertEqual(res.status_code, 200)
        self.assertIn("Open Jupyter", res.text)

    def test_connect_status_public(self) -> None:
        res = self.client.get("/v1/connect/status")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertNotIn("jupyter-secret-token", str(data))
        self.assertTrue(data["jupyter"]["token_configured"])

    def test_jupyter_requires_auth(self) -> None:
        res = self.client.get("/v1/connect/jupyter")
        self.assertEqual(res.status_code, 401)

    def test_jupyter_open_with_auth(self) -> None:
        res = self.client.get(
            "/v1/connect/jupyter",
            headers={"Authorization": "Bearer lab-token"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("token=jupyter-secret-token", data["open_url"])
        self.assertTrue(data["open_url"].startswith("http://mac-studio:8888/lab"))


if __name__ == "__main__":
    unittest.main()
