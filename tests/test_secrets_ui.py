"""Secret store + browser API-key entry (FEAT-012)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.secrets_store import SecretStore  # noqa: E402
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


class SecretStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.store = SecretStore(self.root)

    def test_set_has_clear_redacted_status(self) -> None:
        self.store.set_provider("openai", "sk-test-not-real")
        self.assertTrue(self.store.has_provider("openai"))
        status = self.store.status()
        blob = str(status)
        self.assertNotIn("sk-test-not-real", blob)
        self.assertTrue(status["providers"][0]["configured"])
        self.store.clear_provider("openai")
        self.assertFalse(self.store.has_provider("openai"))

    def test_usage_billed_flag(self) -> None:
        self.assertFalse(self.store.usage_billed_authorized())
        self.store.set_usage_billed_authorized(True)
        self.assertTrue(self.store.usage_billed_authorized())
        self.store.set_usage_billed_authorized(False)
        self.assertFalse(self.store.usage_billed_authorized())

    def test_rejects_unknown_provider(self) -> None:
        with self.assertRaises(ValueError):
            self.store.set_provider("not-a-provider", "x")


@unittest.skipUnless(TestClient is not None, f"fastapi testclient unavailable: {IMPORT_ERROR}")
class SecretsApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
        self.tmp.close()
        self.secrets = SecretStore(Path(tempfile.mkdtemp()))
        app = create_control_app(
            store=SqliteStore(self.tmp.name),
            token="lab-token",
            secret_store=self.secrets,
        )
        self.client = TestClient(app)

    def test_secrets_page(self) -> None:
        res = self.client.get("/secrets")
        self.assertEqual(res.status_code, 200)
        self.assertIn("Foundation model API keys", res.text)

    def test_status_requires_auth(self) -> None:
        self.assertEqual(self.client.get("/v1/secrets/status").status_code, 401)

    def test_put_and_status_never_echo_value(self) -> None:
        res = self.client.put(
            "/v1/secrets/providers/openai",
            headers={"Authorization": "Bearer lab-token"},
            json={"value": "sk-live-should-not-echo"},
        )
        self.assertEqual(res.status_code, 200)
        self.assertNotIn("sk-live-should-not-echo", res.text)
        st = self.client.get(
            "/v1/secrets/status",
            headers={"Authorization": "Bearer lab-token"},
        )
        self.assertEqual(st.status_code, 200)
        self.assertNotIn("sk-live-should-not-echo", st.text)
        self.assertTrue(st.json()["providers"][0]["configured"])


if __name__ == "__main__":
    unittest.main()
