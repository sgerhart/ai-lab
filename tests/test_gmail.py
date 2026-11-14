"""Tests for Gmail integration, OAuth handling, and Steward tool runtime."""

from __future__ import annotations

import base64
from datetime import datetime, timedelta, timezone
from io import BytesIO
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.gmail import (
    GmailAuthError,
    GmailClient,
    format_single_thread_markdown,
    format_threads_markdown,
)
from ai_lab_platform.tool_runtime import ToolContext, execute_allowed_tool


class MockResponse:
    def __init__(self, data: dict, status: int = 200) -> None:
        self.raw = json.dumps(data).encode("utf-8")
        self.status = status

    def read(self) -> bytes:
        return self.raw

    def __enter__(self) -> MockResponse:
        return self

    def __exit__(self, *args: object) -> None:
        pass


class GmailClientTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.creds_path = Path(self.tmp.name) / "gmail-credentials.json"
        self.token_path = Path(self.tmp.name) / "gmail-token.json"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_status_when_files_missing(self) -> None:
        client = GmailClient(credentials_path=self.creds_path, token_path=self.token_path)
        st = client.status()
        self.assertFalse(st["configured"])
        self.assertFalse(st["connected"])

    def test_status_when_only_credentials_present(self) -> None:
        self.creds_path.write_text(json.dumps({"installed": {"client_id": "c1", "client_secret": "s1"}}))
        client = GmailClient(credentials_path=self.creds_path, token_path=self.token_path)
        st = client.status()
        self.assertTrue(st["configured"])
        self.assertFalse(st["connected"])

    def test_status_when_connected(self) -> None:
        self.creds_path.write_text(json.dumps({"installed": {"client_id": "c1", "client_secret": "s1"}}))
        self.token_path.write_text(json.dumps({
            "token": "valid_token",
            "expiry": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        }))

        mock_opener = MagicMock()
        mock_opener.return_value = MockResponse({
            "emailAddress": "steven@example.com",
            "messagesTotal": 42,
            "threadsTotal": 12,
        })

        client = GmailClient(
            credentials_path=self.creds_path,
            token_path=self.token_path,
            opener=mock_opener,
        )
        st = client.status()
        self.assertTrue(st["configured"])
        self.assertTrue(st["connected"])
        self.assertEqual(st["email"], "steven@example.com")
        self.assertEqual(st["messages_total"], 42)

    def test_token_refresh_when_expired(self) -> None:
        self.creds_path.write_text(json.dumps({"installed": {"client_id": "c1", "client_secret": "s1"}}))
        self.token_path.write_text(json.dumps({
            "token": "expired_token",
            "refresh_token": "refresh_123",
            "expiry": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
        }))

        mock_opener = MagicMock()
        mock_opener.return_value = MockResponse({
            "access_token": "new_refreshed_token",
            "expires_in": 3600,
        })

        client = GmailClient(
            credentials_path=self.creds_path,
            token_path=self.token_path,
            opener=mock_opener,
        )
        new_tok = client.get_valid_access_token()
        self.assertEqual(new_tok, "new_refreshed_token")

        # Verify token file was updated on disk
        saved = json.loads(self.token_path.read_text())
        self.assertEqual(saved["token"], "new_refreshed_token")

    def test_search_and_get_thread(self) -> None:
        self.creds_path.write_text(json.dumps({"installed": {"client_id": "c1", "client_secret": "s1"}}))
        self.token_path.write_text(json.dumps({"token": "tok"}))

        body_b64 = base64.urlsafe_b64encode(b"Hello Steven, the servers are all healthy.").decode("utf-8")
        thread_payload = {
            "id": "t100",
            "snippet": "Hello Steven...",
            "messages": [
                {
                    "id": "m100",
                    "threadId": "t100",
                    "snippet": "Hello Steven...",
                    "payload": {
                        "headers": [
                            {"name": "Subject", "value": "Daily Server Health"},
                            {"name": "From", "value": "devops@company.com"},
                            {"name": "To", "value": "sgerhart@example.com"},
                            {"name": "Date", "value": "Sat, 14 Nov 2026 09:00:00 EST"},
                        ],
                        "mimeType": "text/plain",
                        "body": {"data": body_b64},
                    },
                }
            ],
        }

        mock_opener = MagicMock()
        # 1st call for thread search, 2nd call for get_thread
        mock_opener.side_effect = [
            MockResponse({"threads": [{"id": "t100"}]}),
            MockResponse(thread_payload),
        ]

        client = GmailClient(
            credentials_path=self.creds_path,
            token_path=self.token_path,
            opener=mock_opener,
        )
        results = client.search_threads("is:unread", limit=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["subject"], "Daily Server Health")
        self.assertIn("Hello Steven", results[0]["messages"][0]["body"])

        md = format_threads_markdown(results)
        self.assertIn("Daily Server Health", md)
        self.assertIn("devops@company.com", md)

    def test_create_draft(self) -> None:
        self.creds_path.write_text(json.dumps({"installed": {"client_id": "c1", "client_secret": "s1"}}))
        self.token_path.write_text(json.dumps({"token": "tok"}))

        mock_opener = MagicMock()
        mock_opener.return_value = MockResponse({
            "id": "draft_999",
            "message": {"id": "msg_999"},
        })

        client = GmailClient(
            credentials_path=self.creds_path,
            token_path=self.token_path,
            opener=mock_opener,
        )
        draft = client.create_draft(
            to="alex@example.com",
            subject="Project Timeline Review",
            body="Hi Alex,\n\nI reviewed the proposal and it looks great.",
        )
        self.assertTrue(draft["ok"])
        self.assertEqual(draft["draft_id"], "draft_999")
        self.assertIn("approval", draft["note"])


class ToolRuntimeGmailTests(unittest.TestCase):
    def test_gmail_tools_execute_in_runtime_when_unauthorized(self) -> None:
        ctx = ToolContext(workspace_root=ROOT, artifact_root=ROOT / "artifacts")
        allowed = ["gmail_search", "gmail_read_thread", "gmail_list_unread", "gmail_create_draft"]

        res = execute_allowed_tool("gmail_search", {"query": "test"}, allowed_tools=allowed, approved_tools=set(), ctx=ctx)
        self.assertTrue(res.ok)
        self.assertIn("auth-gmail.sh", res.observation)

        res_list = execute_allowed_tool("gmail_list_unread", {}, allowed_tools=allowed, approved_tools=set(), ctx=ctx)
        self.assertTrue(res_list.ok)
        self.assertIn("auth-gmail.sh", res_list.observation)

        res_draft = execute_allowed_tool(
            "gmail_create_draft",
            {"to": "test@test.com", "subject": "Test", "body": "Body"},
            allowed_tools=allowed,
            approved_tools=set(),
            ctx=ctx,
        )
        self.assertTrue(res_draft.ok)
        self.assertIn("auth-gmail.sh", res_draft.observation)
