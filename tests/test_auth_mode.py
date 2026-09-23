"""Auth mode: token vs trusted_tailnet."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.auth import auth_status, is_trusted_peer, require_auth  # noqa: E402
from fastapi import HTTPException  # noqa: E402


class AuthHelperTests(unittest.TestCase):
    def test_trusted_peers(self) -> None:
        self.assertTrue(is_trusted_peer("127.0.0.1"))
        self.assertTrue(is_trusted_peer("100.64.198.100"))
        self.assertFalse(is_trusted_peer("8.8.8.8"))

    def test_status_trusted_tailnet_no_paste(self) -> None:
        st = auth_status(mode="trusted_tailnet", token_configured=True, peer_ip="100.82.1.1")
        self.assertFalse(st["paste_required"])
        self.assertTrue(st["peer_trusted"])

    def test_status_token_mode_requires_paste(self) -> None:
        st = auth_status(mode="token", token_configured=True, peer_ip="100.82.1.1")
        self.assertTrue(st["paste_required"])

    def test_require_auth_trusted(self) -> None:
        req = MagicMock()
        req.client.host = "100.64.1.2"
        require_auth(
            mode="trusted_tailnet",
            expected_token="secret",
            authorization=None,
            request=req,
        )

    def test_require_auth_rejects_public(self) -> None:
        req = MagicMock()
        req.client.host = "8.8.8.8"
        with self.assertRaises(HTTPException):
            require_auth(
                mode="trusted_tailnet",
                expected_token="secret",
                authorization=None,
                request=req,
            )


try:
    from fastapi.testclient import TestClient
    from ai_lab_platform.control_app import create_control_app
    from ai_lab_platform.settings import Settings
    from ai_lab_platform.store import SqliteStore
except Exception as exc:  # pragma: no cover
    TestClient = None  # type: ignore[misc, assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


@unittest.skipUnless(TestClient is not None, f"fastapi unavailable: {IMPORT_ERROR}")
class TrustedTailnetAppTests(unittest.TestCase):
    def test_secrets_without_bearer_from_loopback(self) -> None:
        tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
        tmp.close()
        app = create_control_app(
            store=SqliteStore(tmp.name),
            token="lab-token",
            settings=Settings(auth_mode="trusted_tailnet", api_token="lab-token"),
        )
        client = TestClient(app)
        res = client.get("/v1/auth/status")
        self.assertEqual(res.status_code, 200)
        self.assertFalse(res.json()["paste_required"])
        res = client.get("/v1/secrets/status")
        self.assertEqual(res.status_code, 200)


if __name__ == "__main__":
    unittest.main()
