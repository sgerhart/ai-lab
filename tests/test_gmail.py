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
from unittest.mock import MagicMock, patch
import urllib.error

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.gmail import (
    GmailAuthError,
    GmailClient,
    format_batch_result_markdown,
    format_burndown_result_markdown,
    format_mailbox_stats_markdown,
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

    def test_get_mailbox_stats(self) -> None:
        self.creds_path.write_text(json.dumps({"installed": {"client_id": "c1", "client_secret": "s1"}}))
        self.token_path.write_text(json.dumps({"token": "tok"}))

        def fake_opener(req: object, timeout: int = 10) -> MockResponse:
            url = getattr(req, "full_url", "")
            if "profile" in url:
                return MockResponse({"emailAddress": "steven@example.com", "messagesTotal": 43820, "threadsTotal": 39280})
            if "labels/INBOX" in url:
                return MockResponse({"messagesTotal": 28645, "messagesUnread": 27105, "threadsTotal": 28310, "threadsUnread": 26909})
            return MockResponse({"messagesTotal": 10, "messagesUnread": 5})

        client = GmailClient(
            credentials_path=self.creds_path,
            token_path=self.token_path,
            opener=fake_opener,
        )
        stats = client.get_mailbox_stats()
        self.assertEqual(stats["email"], "steven@example.com")
        self.assertEqual(stats["messages_total"], 43820)
        self.assertEqual(stats["threads_total"], 39280)
        self.assertEqual(stats["labels"]["INBOX"]["messages_total"], 28645)
        self.assertEqual(stats["labels"]["INBOX"]["messages_unread"], 27105)

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

    def test_search_threads_fallback_on_invalid_filter(self) -> None:
        self.creds_path.write_text(json.dumps({"installed": {"client_id": "c1", "client_secret": "s1"}}))
        self.token_path.write_text(json.dumps({"token": "tok"}))

        mock_opener = MagicMock()
        # 1st call for thread search returns empty because of bad from:, 2nd call retries with relaxed query
        mock_opener.side_effect = [
            MockResponse({"threads": [{"id": "t200"}]}),
            MockResponse({"id": "t200", "messages": []}),
        ]

        client = GmailClient(
            credentials_path=self.creds_path,
            token_path=self.token_path,
            opener=mock_opener,
        )
        # Search with invalid from: filter with slash (e.g. from:owner/repo)
        results = client.search_threads("from:owner/repo my-repo", limit=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], "t200")

    def test_trash_thread(self) -> None:
        self.creds_path.write_text(json.dumps({"installed": {"client_id": "c1", "client_secret": "s1"}}))
        self.token_path.write_text(json.dumps({"token": "tok"}))

        mock_opener = MagicMock()
        mock_opener.return_value = MockResponse({"id": "thread_abc123", "messages": []})

        client = GmailClient(
            credentials_path=self.creds_path,
            token_path=self.token_path,
            opener=mock_opener,
        )
        res = client.trash_thread("thread_abc123")
        self.assertTrue(res["ok"])
        self.assertEqual(res["thread_id"], "thread_abc123")
        self.assertEqual(res["status"], "trashed")

    def test_trash_message(self) -> None:
        self.creds_path.write_text(json.dumps({"installed": {"client_id": "c1", "client_secret": "s1"}}))
        self.token_path.write_text(json.dumps({"token": "tok"}))

        mock_opener = MagicMock()
        mock_opener.return_value = MockResponse({"id": "msg_456", "threadId": "thread_abc123"})

        client = GmailClient(
            credentials_path=self.creds_path,
            token_path=self.token_path,
            opener=mock_opener,
        )
        res = client.trash_message("msg_456")
        self.assertTrue(res["ok"])
        self.assertEqual(res["message_id"], "msg_456")
        self.assertEqual(res["thread_id"], "thread_abc123")
        self.assertEqual(res["status"], "trashed")

    def test_archive_thread(self) -> None:
        self.creds_path.write_text(json.dumps({"installed": {"client_id": "c1", "client_secret": "s1"}}))
        self.token_path.write_text(json.dumps({"token": "tok"}))

        mock_opener = MagicMock()
        mock_opener.return_value = MockResponse({"id": "thread_abc123"})

        client = GmailClient(
            credentials_path=self.creds_path,
            token_path=self.token_path,
            opener=mock_opener,
        )
        res = client.archive_thread("thread_abc123")
        self.assertTrue(res["ok"])
        self.assertEqual(res["thread_id"], "thread_abc123")
        self.assertEqual(res["status"], "archived")

    def test_api_request_429_backoff_and_retry(self) -> None:
        self.creds_path.write_text(json.dumps({"installed": {"client_id": "c1", "client_secret": "s1"}}))
        self.token_path.write_text(json.dumps({"token": "tok"}))

        err_headers = {"Retry-After": "0.01"}
        http_err = urllib.error.HTTPError(
            url="https://gmail.googleapis.com/gmail/v1/users/me/profile",
            code=429,
            msg="Too Many Requests",
            hdrs=err_headers,  # type: ignore
            fp=BytesIO(b'{"error": "rate limit"}'),
        )
        mock_opener = MagicMock()
        mock_opener.side_effect = [
            http_err,
            MockResponse({"emailAddress": "steven@example.com", "messagesTotal": 100}),
        ]

        client = GmailClient(
            credentials_path=self.creds_path,
            token_path=self.token_path,
            opener=mock_opener,
        )
        prof = client.get_profile()
        self.assertEqual(prof["emailAddress"], "steven@example.com")
        self.assertEqual(mock_opener.call_count, 2)

    def test_batch_trash_threads_uses_batch_modify(self) -> None:
        self.creds_path.write_text(json.dumps({"installed": {"client_id": "c1", "client_secret": "s1"}}))
        self.token_path.write_text(json.dumps({"token": "tok"}))

        def fake_opener(req: object, timeout: int = 10) -> MockResponse:
            url = getattr(req, "full_url", "")
            if "threads?" in url:
                return MockResponse({"threads": [{"id": "t1", "snippet": "Sale 50% off"}]})
            if "messages?" in url:
                return MockResponse({
                    "messages": [
                        {"id": "m1", "threadId": "t1"},
                        {"id": "m2", "threadId": "t1"},
                    ]
                })
            if "messages/batchModify" in url:
                return MockResponse({})
            return MockResponse({})

        client = GmailClient(
            credentials_path=self.creds_path,
            token_path=self.token_path,
            opener=fake_opener,
        )
        res = client.batch_trash_threads("category:promotions", limit=50)
        self.assertTrue(res["ok"])
        self.assertEqual(res["trashed_count"], 1)
        self.assertEqual(len(res["message_ids"]), 2)
        self.assertIn("Sale 50% off", res["sample_snippets"])

    def test_batch_archive_threads_uses_batch_modify(self) -> None:
        self.creds_path.write_text(json.dumps({"installed": {"client_id": "c1", "client_secret": "s1"}}))
        self.token_path.write_text(json.dumps({"token": "tok"}))

        def fake_opener(req: object, timeout: int = 10) -> MockResponse:
            url = getattr(req, "full_url", "")
            if "threads?" in url:
                return MockResponse({"threads": [{"id": "t10", "snippet": "LinkedIn connection request"}]})
            if "messages?" in url:
                return MockResponse({"messages": [{"id": "m10", "threadId": "t10"}]})
            if "messages/batchModify" in url:
                return MockResponse({})
            return MockResponse({})

        client = GmailClient(
            credentials_path=self.creds_path,
            token_path=self.token_path,
            opener=fake_opener,
        )
        res = client.batch_archive_threads("from:linkedin.com", limit=50)
        self.assertTrue(res["ok"])
        self.assertEqual(res["archived_count"], 1)
        self.assertEqual(res["message_ids"], ["m10"])
        self.assertIn("LinkedIn connection request", res["sample_snippets"])

    def test_burndown_sweep_flow(self) -> None:
        self.creds_path.write_text(json.dumps({"installed": {"client_id": "c1", "client_secret": "s1"}}))
        self.token_path.write_text(json.dumps({"token": "tok"}))

        client = GmailClient(credentials_path=self.creds_path, token_path=self.token_path)

        with patch.object(
            client,
            "get_mailbox_stats",
            side_effect=[
                {"labels": {"INBOX": {"messages_unread": 2500, "threads_unread": 2000}}},
                {"labels": {"INBOX": {"messages_unread": 450, "threads_unread": 400}}},
                {"labels": {"INBOX": {"messages_unread": 450, "threads_unread": 400}}},
            ],
        ), patch.object(
            client,
            "batch_trash_threads",
            return_value={"ok": True, "trashed_count": 1500, "sample_snippets": ["Promo"]},
        ), patch.object(
            client,
            "batch_archive_threads",
            return_value={"ok": True, "archived_count": 550, "sample_snippets": ["LinkedIn"]},
        ):
            res = client.burndown_sweep(target_unread=500, max_batches=2, batch_size=500)
            self.assertTrue(res["ok"])
            self.assertEqual(res["starting_unread"], 2500)
            self.assertEqual(res["ending_unread"], 450)
            self.assertTrue(res["target_reached"])
            self.assertGreater(res["total_swept"], 0)



class ToolRuntimeGmailTests(unittest.TestCase):
    @patch("ai_lab_platform.gmail.GmailClient.has_token", return_value=False)
    def test_gmail_tools_execute_in_runtime_when_unauthorized(self, _mock_has_token: MagicMock) -> None:
        ctx = ToolContext(workspace_root=ROOT, artifact_root=ROOT / "artifacts")
        allowed = [
            "gmail_search",
            "gmail_read_thread",
            "gmail_list_unread",
            "gmail_create_draft",
            "gmail_trash_thread",
            "gmail_trash_message",
            "gmail_archive_thread",
        ]

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

        res_trash_t = execute_allowed_tool(
            "gmail_trash_thread",
            {"thread_id": "thread_123"},
            allowed_tools=allowed,
            approved_tools=set(),
            ctx=ctx,
        )
        self.assertTrue(res_trash_t.ok)
        self.assertIn("auth-gmail.sh", res_trash_t.observation)

        res_trash_m = execute_allowed_tool(
            "gmail_trash_message",
            {"message_id": "msg_123"},
            allowed_tools=allowed,
            approved_tools=set(),
            ctx=ctx,
        )
        self.assertTrue(res_trash_m.ok)
        self.assertIn("auth-gmail.sh", res_trash_m.observation)

        res_arch = execute_allowed_tool(
            "gmail_archive_thread",
            {"thread_id": "thread_123"},
            allowed_tools=allowed,
            approved_tools=set(),
            ctx=ctx,
        )
        self.assertTrue(res_arch.ok)
        self.assertIn("auth-gmail.sh", res_arch.observation)

    @patch("ai_lab_platform.gmail.GmailClient.has_token", return_value=True)
    def test_gmail_delete_and_archive_runtime_dispatch(self, _mock_has_token: MagicMock) -> None:
        ctx = ToolContext(workspace_root=ROOT, artifact_root=ROOT / "artifacts")
        allowed = ["gmail_trash_thread", "gmail_trash_message", "gmail_archive_thread"]

        with patch("ai_lab_platform.gmail.GmailClient.trash_thread", return_value={"ok": True, "thread_id": "t99", "status": "trashed"}):
            res = execute_allowed_tool("gmail_trash_thread", {"thread_id": "t99"}, allowed_tools=allowed, approved_tools=set(), ctx=ctx)
            self.assertTrue(res.ok)
            self.assertIn("moved to Gmail Trash", res.observation)
            self.assertIn("t99", res.observation)

        with patch("ai_lab_platform.gmail.GmailClient.trash_message", return_value={"ok": True, "message_id": "m88", "thread_id": "t99", "status": "trashed"}):
            res = execute_allowed_tool("gmail_trash_message", {"message_id": "m88"}, allowed_tools=allowed, approved_tools=set(), ctx=ctx)
            self.assertTrue(res.ok)
            self.assertIn("moved to Gmail Trash", res.observation)
            self.assertIn("m88", res.observation)

        with patch("ai_lab_platform.gmail.GmailClient.archive_thread", return_value={"ok": True, "thread_id": "t99", "status": "archived"}):
            res = execute_allowed_tool("gmail_archive_thread", {"thread_id": "t99"}, allowed_tools=allowed, approved_tools=set(), ctx=ctx)
            self.assertTrue(res.ok)
            self.assertIn("has been archived", res.observation)
            self.assertIn("t99", res.observation)

    def test_format_mailbox_stats_markdown(self) -> None:
        stats = {
            "email": "test@example.com",
            "messages_total": 43820,
            "threads_total": 39280,
            "labels": {
                "INBOX": {"messages_total": 28645, "messages_unread": 27105, "threads_total": 28310, "threads_unread": 26909},
                "UNREAD": {"messages_total": 38098, "threads_total": 35319},
                "STARRED": {"messages_total": 20, "messages_unread": 12},
                "SENT": {"messages_total": 725},
                "TRASH": {"messages_total": 2032},
                "SPAM": {"messages_total": 575},
            },
        }
        md = format_mailbox_stats_markdown(stats)
        self.assertIn("43,820", md)
        self.assertIn("28,645", md)
        self.assertIn("27,105", md)
        self.assertIn("test@example.com", md)

    @patch("ai_lab_platform.gmail.GmailClient.has_token", return_value=True)
    def test_gmail_mailbox_stats_runtime_dispatch(self, _mock_has_token: MagicMock) -> None:
        ctx = ToolContext(workspace_root=ROOT, artifact_root=ROOT / "artifacts")
        allowed = ["gmail_mailbox_stats"]

        mock_stats = {
            "email": "test@example.com",
            "messages_total": 100,
            "threads_total": 50,
            "labels": {
                "INBOX": {"messages_total": 80, "messages_unread": 10, "threads_total": 40, "threads_unread": 5},
            },
        }
        with patch("ai_lab_platform.gmail.GmailClient.get_mailbox_stats", return_value=mock_stats):
            res = execute_allowed_tool("gmail_mailbox_stats", {}, allowed_tools=allowed, approved_tools=set(), ctx=ctx)
            self.assertTrue(res.ok)
            self.assertIn("100", res.observation)
            self.assertIn("80", res.observation)
            self.assertIn("test@example.com", res.observation)

    def test_format_batch_result_markdown(self) -> None:
        res = {
            "query": "from:notifications@github.com",
            "trashed_count": 25,
            "sample_snippets": ["Run failed", "PR approved"],
            "has_more": True,
        }
        md = format_batch_result_markdown(res, action="trashed")
        self.assertIn("25 thread(s) trashed", md)
        self.assertIn("from:notifications@github.com", md)
        self.assertIn("Run failed", md)

    @patch("ai_lab_platform.gmail.GmailClient.has_token", return_value=True)
    def test_gmail_batch_tools_runtime_dispatch(self, _mock_has_token: MagicMock) -> None:
        ctx = ToolContext(workspace_root=ROOT, artifact_root=ROOT / "artifacts")
        allowed = ["gmail_batch_trash", "gmail_batch_archive"]

        mock_trash_res = {
            "ok": True,
            "query": "category:promotions",
            "trashed_count": 10,
            "sample_snippets": ["Sale now"],
            "has_more": False,
        }
        with patch("ai_lab_platform.gmail.GmailClient.batch_trash_threads", return_value=mock_trash_res):
            res = execute_allowed_tool("gmail_batch_trash", {"query": "category:promotions"}, allowed_tools=allowed, approved_tools=set(), ctx=ctx)
            self.assertTrue(res.ok)
            self.assertIn("10 thread(s) trashed", res.observation)
            self.assertIn("category:promotions", res.observation)

        mock_arch_res = {
            "ok": True,
            "query": "category:updates",
            "archived_count": 5,
            "sample_snippets": ["Update note"],
            "has_more": False,
        }
        with patch("ai_lab_platform.gmail.GmailClient.batch_archive_threads", return_value=mock_arch_res):
            res = execute_allowed_tool("gmail_batch_archive", {"query": "category:updates"}, allowed_tools=allowed, approved_tools=set(), ctx=ctx)
            self.assertTrue(res.ok)
            self.assertIn("5 thread(s) archived", res.observation)

    def test_format_burndown_result_markdown(self) -> None:
        res = {
            "ok": True,
            "starting_unread": 26900,
            "ending_unread": 480,
            "target_unread": 500,
            "total_swept": 26420,
            "total_trashed": 21000,
            "total_archived": 5420,
            "batches_run": 3,
            "target_reached": True,
            "breakdown": [
                {"category": "Stale Promotions (>2d)", "action": "trashed", "count": 20000, "samples": ["Promo 1"]},
                {"category": "LinkedIn Alerts", "action": "archived", "count": 5000, "samples": ["Alert 1"]},
            ],
        }
        md = format_burndown_result_markdown(res)
        self.assertIn("26,420 emails", md)
        self.assertIn("26,900", md)
        self.assertIn("480", md)
        self.assertIn("Stale Promotions (>2d)", md)
        self.assertIn("LinkedIn Alerts", md)
        self.assertIn("Target Reached", md)

    @patch("ai_lab_platform.gmail.GmailClient.has_token", return_value=True)
    def test_gmail_burndown_sweep_runtime_dispatch(self, _mock_has_token: MagicMock) -> None:
        ctx = ToolContext(workspace_root=ROOT, artifact_root=ROOT / "artifacts")
        allowed = ["gmail_burndown_sweep"]

        mock_burndown_res = {
            "ok": True,
            "starting_unread": 1000,
            "ending_unread": 400,
            "target_unread": 500,
            "total_swept": 600,
            "total_trashed": 400,
            "total_archived": 200,
            "batches_run": 1,
            "target_reached": True,
            "breakdown": [],
        }
        with patch("ai_lab_platform.gmail.GmailClient.burndown_sweep", return_value=mock_burndown_res):
            res = execute_allowed_tool("gmail_burndown_sweep", {"target_unread": 500}, allowed_tools=allowed, approved_tools=set(), ctx=ctx)
            self.assertTrue(res.ok)
            self.assertIn("600 emails", res.observation)
            self.assertIn("Target Reached", res.observation)

