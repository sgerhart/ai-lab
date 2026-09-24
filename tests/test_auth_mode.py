"""Auth mode: bearer token and username/password sessions."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.auth import (  # noqa: E402
    AuthError,
    auth_status,
    is_trusted_peer,
    require_auth,
)
from ai_lab_platform.operator_auth import (  # noqa: E402
    login,
    operator_configured,
    session_valid,
    set_operator_password,
)


class AuthHelperTests(unittest.TestCase):
    def test_trusted_peers(self) -> None:
        self.assertTrue(is_trusted_peer("127.0.0.1"))
        self.assertTrue(is_trusted_peer("100.64.198.100"))
        self.assertFalse(is_trusted_peer("8.8.8.8"))

    def test_status_token_only(self) -> None:
        with patch("ai_lab_platform.auth.operator_configured", return_value=False):
            st = auth_status(mode="token", token_configured=True, peer_ip="100.82.1.1")
        self.assertTrue(st["paste_required"])
        self.assertFalse(st["login_available"])
        self.assertTrue(st["auth_ready"])

    def test_status_login_preferred(self) -> None:
        with patch("ai_lab_platform.auth.operator_configured", return_value=True):
            st = auth_status(mode="token", token_configured=True, peer_ip="127.0.0.1")
        self.assertTrue(st["login_required"])
        self.assertFalse(st["paste_required"])
        self.assertTrue(st["login_available"])

    def test_require_auth_accepts_bearer(self) -> None:
        req = MagicMock()
        req.client.host = "100.64.1.2"
        with patch("ai_lab_platform.auth.operator_configured", return_value=False):
            require_auth(
                mode="token",
                expected_token="secret",
                authorization="Bearer secret",
                request=req,
            )

    def test_require_auth_rejects_missing_config(self) -> None:
        req = MagicMock()
        req.client.host = "127.0.0.1"
        with patch("ai_lab_platform.auth.operator_configured", return_value=False):
            with self.assertRaises(AuthError) as ctx:
                require_auth(
                    mode="token",
                    expected_token="",
                    authorization=None,
                    request=req,
                )
        self.assertEqual(ctx.exception.detail, "api_token_not_configured")

    def test_require_auth_rejects_without_bearer(self) -> None:
        req = MagicMock()
        req.client.host = "100.64.1.2"
        with patch("ai_lab_platform.auth.operator_configured", return_value=False):
            with self.assertRaises(AuthError):
                require_auth(
                    mode="trusted_tailnet",
                    expected_token="secret",
                    authorization=None,
                    request=req,
                )


class OperatorLoginTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.env = patch.dict(os.environ, {"AI_LAB_HOME": str(self.tmp)})
        self.env.start()

    def tearDown(self) -> None:
        self.env.stop()

    def test_set_login_session(self) -> None:
        self.assertFalse(operator_configured())
        set_operator_password("operator", "correct-horse")
        self.assertTrue(operator_configured())
        out = login("operator", "correct-horse")
        self.assertTrue(out["ok"])
        self.assertTrue(session_valid(out["token"]))
        with self.assertRaises(PermissionError):
            login("operator", "wrong-password")

    def test_require_auth_accepts_session(self) -> None:
        set_operator_password("operator", "correct-horse")
        tok = login("operator", "correct-horse")["token"]
        req = MagicMock()
        req.client.host = "127.0.0.1"
        require_auth(
            mode="token",
            expected_token="",
            authorization=f"Bearer {tok}",
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
class LoginApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.env = patch.dict(os.environ, {"AI_LAB_HOME": str(self.tmp)})
        self.env.start()
        set_operator_password("operator", "correct-horse")
        sqlite = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
        sqlite.close()
        self.app = create_control_app(
            store=SqliteStore(sqlite.name),
            token="lab-token",
            settings=Settings(auth_mode="token", api_token="lab-token"),
        )
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.env.stop()

    def test_login_and_secrets(self) -> None:
        st = self.client.get("/v1/auth/status").json()
        self.assertTrue(st["login_available"])
        bad = self.client.post(
            "/v1/auth/login",
            json={"username": "operator", "password": "nope-nope"},
        )
        self.assertEqual(bad.status_code, 401)
        ok = self.client.post(
            "/v1/auth/login",
            json={"username": "operator", "password": "correct-horse"},
        )
        self.assertEqual(ok.status_code, 200)
        token = ok.json()["token"]
        denied = self.client.get("/v1/secrets/status")
        self.assertEqual(denied.status_code, 401)
        allowed = self.client.get(
            "/v1/secrets/status",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(allowed.status_code, 200)


if __name__ == "__main__":
    unittest.main()
