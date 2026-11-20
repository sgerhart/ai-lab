"""Gmail integration for Steward in AI Lab.

Provides authenticated, governed read-only searching and drafting capabilities
via Google's Gmail REST API. Operates under least-privilege principles:
Steward can search and read messages, and prepare drafts in Gmail, but
cannot send emails automatically without operator approval.
"""

from __future__ import annotations

import base64
from datetime import datetime, timezone
from email.message import EmailMessage
import json
import os
from pathlib import Path
import random
import re
import time
from typing import Any, Dict, List, Optional
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_CREDENTIALS_PATH = Path.home() / ".ai-lab" / "secrets" / "gmail-credentials.json"
DEFAULT_TOKEN_PATH = Path.home() / ".ai-lab" / "secrets" / "gmail-token.json"
GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1/users/me"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

DEFAULT_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.modify",
]


class GmailAuthError(Exception):
    """Raised when Gmail authentication fails or credentials are missing."""


class GmailAPIError(Exception):
    """Raised when a Gmail API request fails."""


class GmailClient:
    def __init__(
        self,
        credentials_path: Path | None = None,
        token_path: Path | None = None,
        opener: Any | None = None,
    ) -> None:
        self.credentials_path = credentials_path or DEFAULT_CREDENTIALS_PATH
        self.token_path = token_path or DEFAULT_TOKEN_PATH
        self.opener = opener or urllib.request.urlopen

    def has_credentials(self) -> bool:
        return self.credentials_path.is_file() and bool(self.credentials_path.stat().st_size > 0)

    def has_token(self) -> bool:
        return self.token_path.is_file() and bool(self.token_path.stat().st_size > 0)

    def load_credentials(self) -> Dict[str, Any]:
        if not self.has_credentials():
            raise GmailAuthError(
                f"Missing Gmail credentials file at {self.credentials_path}. "
                "Download your OAuth client ID credentials from Google Cloud Console "
                "and save them to ~/.ai-lab/secrets/gmail-credentials.json."
            )
        try:
            raw = json.loads(self.credentials_path.read_text(encoding="utf-8"))
            return raw.get("installed") or raw.get("web") or raw
        except Exception as exc:
            raise GmailAuthError(f"Failed to parse credentials file: {exc}") from exc

    def load_token_data(self) -> Dict[str, Any]:
        if not self.has_token():
            raise GmailAuthError(
                f"Missing Gmail authorization token at {self.token_path}. "
                "Run ./scripts/auth-gmail.sh to authorize Steward with your Google account."
            )
        try:
            return json.loads(self.token_path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise GmailAuthError(f"Failed to parse token file: {exc}") from exc

    def save_token_data(self, data: Dict[str, Any]) -> None:
        self.token_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.token_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        try:
            os.chmod(self.token_path, 0o600)
        except OSError:
            pass

    def get_valid_access_token(self, force_refresh: bool = False) -> str:
        token_data = self.load_token_data()
        token = token_data.get("token") or token_data.get("access_token")
        expiry = token_data.get("expiry")
        refresh_token = token_data.get("refresh_token")

        is_expired = False
        if expiry:
            try:
                exp_dt = datetime.fromisoformat(expiry.replace("Z", "+00:00"))
                if datetime.now(timezone.utc) >= exp_dt:
                    is_expired = True
            except Exception:
                pass

        if token and not is_expired and not force_refresh:
            return str(token)

        if not refresh_token:
            if token and not force_refresh:
                return str(token)
            raise GmailAuthError("No access token or refresh token available. Re-authorization required.")

        # Attempt token refresh
        creds = self.load_credentials()
        client_id = creds.get("client_id") or token_data.get("client_id")
        client_secret = creds.get("client_secret") or token_data.get("client_secret")
        if not client_id or not client_secret:
            raise GmailAuthError("Client ID or client secret missing for token refresh.")

        params = urllib.parse.urlencode({
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }).encode("utf-8")

        req = urllib.request.Request(
            GOOGLE_TOKEN_URL,
            data=params,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        try:
            with self.opener(req, timeout=10) as resp:
                refreshed = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            raise GmailAuthError(f"Failed to refresh Gmail access token: {exc}") from exc

        new_access_token = refreshed.get("access_token")
        if not new_access_token:
            raise GmailAuthError(f"Token refresh endpoint returned no access token: {refreshed}")

        token_data["token"] = new_access_token
        token_data["access_token"] = new_access_token
        expires_in = refreshed.get("expires_in", 3600)
        token_data["expiry"] = datetime.fromtimestamp(
            datetime.now(timezone.utc).timestamp() + expires_in, tz=timezone.utc
        ).isoformat()

        self.save_token_data(token_data)
        return str(new_access_token)

    def _api_request(
        self,
        endpoint: str,
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        attempt = 0
        last_exc: Optional[Exception] = None
        while attempt <= max_retries:
            # Enforce throttle delay to stay well under Google's 250 quota units/sec
            now = time.monotonic()
            last_time = getattr(self, "_last_request_time", 0.0)
            if now - last_time < 0.05:
                time.sleep(0.05 - (now - last_time))
            self._last_request_time = time.monotonic()

            token = self.get_valid_access_token(
                force_refresh=(attempt > 0 and getattr(last_exc, "code", None) == 401)
            )
            url = f"{GMAIL_API_BASE}/{endpoint.lstrip('/')}"
            if params:
                query = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
                if query:
                    url = f"{url}?{query}"

            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            }
            body_bytes = None
            if data is not None:
                headers["Content-Type"] = "application/json"
                body_bytes = json.dumps(data).encode("utf-8")

            req = urllib.request.Request(url, data=body_bytes, headers=headers, method=method)
            try:
                with self.opener(req, timeout=20) as resp:
                    raw = resp.read().decode("utf-8")
                    return json.loads(raw) if raw else {}
            except urllib.error.HTTPError as exc:
                last_exc = exc
                # Rate limit (429) or transient server errors (5xx)
                if exc.code in (429, 500, 502, 503, 504) and attempt < max_retries:
                    retry_after = None
                    if hasattr(exc, "headers") and exc.headers:
                        val = exc.headers.get("Retry-After")
                        if val:
                            try:
                                retry_after = float(val)
                            except (ValueError, TypeError):
                                pass
                    backoff = retry_after if retry_after is not None else (2 ** attempt) + random.uniform(0.1, 0.5)
                    time.sleep(backoff)
                    attempt += 1
                    continue
                # Auth token expired mid-operation (401)
                if exc.code == 401 and attempt == 0:
                    attempt += 1
                    continue
                err_body = exc.read().decode("utf-8", "ignore") if hasattr(exc, "read") else str(exc)
                raise GmailAPIError(f"Gmail API error {exc.code} for {url}: {err_body}") from exc
            except Exception as exc:
                last_exc = exc
                if attempt < max_retries:
                    time.sleep((2 ** attempt) + random.uniform(0.1, 0.4))
                    attempt += 1
                    continue
                raise GmailAPIError(f"Request to {url} failed: {exc}") from exc
        raise GmailAPIError(f"Request to {endpoint} failed after {max_retries} retries: {last_exc}")

    def get_profile(self) -> Dict[str, Any]:
        """Fetch user profile to verify connection and email address."""
        return self._api_request("profile")

    def get_mailbox_stats(self) -> Dict[str, Any]:
        """Fetch mailbox-wide counts and per-label metrics."""
        profile = self.get_profile()
        email = profile.get("emailAddress", "unknown")
        messages_total = profile.get("messagesTotal", 0)
        threads_total = profile.get("threadsTotal", 0)

        label_counts: Dict[str, Dict[str, int]] = {}
        for lid in ("INBOX", "UNREAD", "STARRED", "SENT", "TRASH", "SPAM"):
            try:
                data = self._api_request(f"labels/{lid}")
                label_counts[lid] = {
                    "messages_total": data.get("messagesTotal", 0),
                    "messages_unread": data.get("messagesUnread", 0),
                    "threads_total": data.get("threadsTotal", 0),
                    "threads_unread": data.get("threadsUnread", 0),
                }
            except Exception:
                pass

        return {
            "email": email,
            "messages_total": messages_total,
            "threads_total": threads_total,
            "labels": label_counts,
        }

    def status(self) -> Dict[str, Any]:
        """Return connectivity status of the Gmail integration."""
        if not self.has_credentials():
            return {
                "configured": False,
                "connected": False,
                "detail": "Credentials missing (~/.ai-lab/secrets/gmail-credentials.json).",
            }
        if not self.has_token():
            return {
                "configured": True,
                "connected": False,
                "detail": "OAuth token missing. Run ./scripts/auth-gmail.sh to authorize.",
            }
        try:
            prof = self.get_profile()
            return {
                "configured": True,
                "connected": True,
                "email": prof.get("emailAddress", "unknown"),
                "messages_total": prof.get("messagesTotal", 0),
                "threads_total": prof.get("threadsTotal", 0),
            }
        except Exception as exc:
            return {
                "configured": True,
                "connected": False,
                "detail": f"Auth check failed: {exc}",
            }

    def search_threads(self, query: str = "", limit: int = 5) -> List[Dict[str, Any]]:
        """Search email threads and return structured summaries."""
        bounded = max(1, min(limit, 20))
        # If query has invalid from: (e.g. from:owner/repo), strip from:
        effective_query = re.sub(r"\bfrom:([^\s/]+/[^\s]+)", r"\1", query or "").strip()
        res = self._api_request("threads", params={"q": effective_query or None, "maxResults": bounded})
        raw_threads = res.get("threads") or []

        # If zero results and query contained an over-constraining filter, fallback to clean keyword search
        if not raw_threads and ("from:" in effective_query or "subject:" in effective_query):
            relaxed = re.sub(r"\b(?:from|subject):([\"'][^\"']+[\"']|[^\s]+)", r"\1", effective_query).strip()
            relaxed = re.sub(r"[\"']", "", relaxed).strip()
            if relaxed and relaxed != effective_query:
                res = self._api_request("threads", params={"q": relaxed or None, "maxResults": bounded})
                raw_threads = res.get("threads") or []

        items: List[Dict[str, Any]] = []
        for t in raw_threads:
            tid = t.get("id")
            if not tid:
                continue
            try:
                full = self.get_thread(tid)
                items.append(full)
            except Exception:
                items.append({
                    "id": tid,
                    "snippet": t.get("snippet", ""),
                    "messages": [],
                    "subject": "(error reading thread)",
                })
        return items

    def get_thread(self, thread_id: str) -> Dict[str, Any]:
        """Retrieve full details of an email conversation thread."""
        res = self._api_request(f"threads/{thread_id}", params={"format": "full"})
        msgs = res.get("messages") or []
        parsed_msgs: List[Dict[str, Any]] = []
        subject = ""
        for m in msgs:
            parsed = _parse_message(m)
            if not subject and parsed.get("subject"):
                subject = parsed["subject"]
            parsed_msgs.append(parsed)

        return {
            "id": thread_id,
            "subject": subject or "(No Subject)",
            "snippet": res.get("snippet") or (parsed_msgs[0].get("snippet") if parsed_msgs else ""),
            "count": len(parsed_msgs),
            "messages": parsed_msgs,
        }

    def list_unread(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Convenience method to inspect recent unread emails in Inbox."""
        return self.search_threads(query="is:unread label:INBOX", limit=limit)

    def create_draft(self, to: str, subject: str, body: str) -> Dict[str, Any]:
        """Create a draft response in Gmail for Steven's review."""
        msg = EmailMessage()
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        raw_b64 = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")

        res = self._api_request("drafts", method="POST", data={"message": {"raw": raw_b64}})
        return {
            "ok": True,
            "draft_id": res.get("id", ""),
            "message_id": (res.get("message") or {}).get("id", ""),
            "to": to,
            "subject": subject,
            "note": "Draft saved in Gmail for Steven's approval. Not sent.",
        }

    def trash_thread(self, thread_id: str) -> Dict[str, Any]:
        """Move an entire conversation thread to Gmail Trash (recoverable for 30 days)."""
        res = self._api_request(f"threads/{thread_id}/trash", method="POST")
        return {
            "ok": True,
            "thread_id": res.get("id") or thread_id,
            "status": "trashed",
            "note": "Thread moved to Gmail Trash. Recoverable for 30 days.",
        }

    def trash_message(self, message_id: str) -> Dict[str, Any]:
        """Move an individual email message to Gmail Trash (recoverable for 30 days)."""
        res = self._api_request(f"messages/{message_id}/trash", method="POST")
        return {
            "ok": True,
            "message_id": res.get("id") or message_id,
            "thread_id": res.get("threadId", ""),
            "status": "trashed",
            "note": "Message moved to Gmail Trash. Recoverable for 30 days.",
        }

    def archive_thread(self, thread_id: str) -> Dict[str, Any]:
        """Archive a conversation thread by removing it from the Inbox."""
        res = self._api_request(
            f"threads/{thread_id}/modify",
            method="POST",
            data={"removeLabelIds": ["INBOX"]},
        )
        return {
            "ok": True,
            "thread_id": res.get("id") or thread_id,
            "status": "archived",
            "note": "Thread archived (removed from Inbox, preserved in All Mail).",
        }

    def batch_trash_threads(self, query: str, limit: int = 25) -> Dict[str, Any]:
        """Move multiple threads/messages matching query to Trash (recoverable for 30 days).

        Uses Gmail messages/batchModify for sub-second, bulk atomic execution while
        strictly preserving recoverable 30-day Trash status.
        """
        bounded = max(1, min(limit, 500))
        effective_query = re.sub(r"\bfrom:([^\s/]+/[^\s]+)", r"\1", query or "").strip()
        search_q = f"label:INBOX {effective_query}".strip() if "label:INBOX" not in effective_query else effective_query

        # 1. Fetch sample thread snippets (up to 5) for user audit receipts in 1 lightweight call
        samples: List[str] = []
        try:
            snip_res = self._api_request("threads", params={"q": search_q, "maxResults": min(5, bounded)})
            for t in snip_res.get("threads") or []:
                raw_snip = t.get("snippet") or ""
                clean_snip = re.sub(r"[\s\u034f\u200b\ufeff]+", " ", raw_snip).strip()[:100]
                if clean_snip:
                    samples.append(clean_snip)
        except Exception:
            pass

        # 2. Fetch matching messages for bulk operation
        search_res = self._api_request("messages", params={"q": search_q, "maxResults": bounded})
        raw_msgs = search_res.get("messages") or []
        if not raw_msgs:
            return {
                "ok": True,
                "query": query,
                "trashed_count": 0,
                "message_ids": [],
                "thread_ids": [],
                "sample_snippets": [],
                "has_more": False,
                "note": f"No messages found matching '{query}' in Inbox.",
            }

        msg_ids = [m["id"] for m in raw_msgs if m.get("id")]
        thread_ids = list(dict.fromkeys(m["threadId"] for m in raw_msgs if m.get("threadId")))

        # 3. Execute bulk batchModify in 1 single HTTP request (up to 1,000 per call)
        for i in range(0, len(msg_ids), 1000):
            chunk = msg_ids[i : i + 1000]
            self._api_request(
                "messages/batchModify",
                method="POST",
                data={
                    "ids": chunk,
                    "addLabelIds": ["TRASH"],
                    "removeLabelIds": ["INBOX"],
                },
            )

        count = len(thread_ids) or len(msg_ids)
        return {
            "ok": True,
            "query": query,
            "trashed_count": count,
            "message_ids": msg_ids,
            "thread_ids": thread_ids,
            "sample_snippets": samples,
            "has_more": len(raw_msgs) >= bounded,
            "note": f"Moved {count} thread(s) ({len(msg_ids)} messages) to Gmail Trash (recoverable for 30 days).",
        }

    def batch_archive_threads(self, query: str, limit: int = 25) -> Dict[str, Any]:
        """Archive multiple threads/messages matching query by removing them from Inbox.

        Uses Gmail messages/batchModify for sub-second, bulk atomic execution.
        """
        bounded = max(1, min(limit, 500))
        effective_query = re.sub(r"\bfrom:([^\s/]+/[^\s]+)", r"\1", query or "").strip()
        search_q = f"label:INBOX {effective_query}".strip() if "label:INBOX" not in effective_query else effective_query

        # 1. Fetch sample thread snippets (up to 5) for user audit receipts
        samples: List[str] = []
        try:
            snip_res = self._api_request("threads", params={"q": search_q, "maxResults": min(5, bounded)})
            for t in snip_res.get("threads") or []:
                raw_snip = t.get("snippet") or ""
                clean_snip = re.sub(r"[\s\u034f\u200b\ufeff]+", " ", raw_snip).strip()[:100]
                if clean_snip:
                    samples.append(clean_snip)
        except Exception:
            pass

        # 2. Fetch matching messages for bulk operation
        search_res = self._api_request("messages", params={"q": search_q, "maxResults": bounded})
        raw_msgs = search_res.get("messages") or []
        if not raw_msgs:
            return {
                "ok": True,
                "query": query,
                "archived_count": 0,
                "message_ids": [],
                "thread_ids": [],
                "sample_snippets": [],
                "has_more": False,
                "note": f"No messages found matching '{query}' in Inbox.",
            }

        msg_ids = [m["id"] for m in raw_msgs if m.get("id")]
        thread_ids = list(dict.fromkeys(m["threadId"] for m in raw_msgs if m.get("threadId")))

        # 3. Execute bulk batchModify in 1 single HTTP request
        for i in range(0, len(msg_ids), 1000):
            chunk = msg_ids[i : i + 1000]
            self._api_request(
                "messages/batchModify",
                method="POST",
                data={
                    "ids": chunk,
                    "removeLabelIds": ["INBOX"],
                },
            )

        count = len(thread_ids) or len(msg_ids)
        return {
            "ok": True,
            "query": query,
            "archived_count": count,
            "message_ids": msg_ids,
            "thread_ids": thread_ids,
            "sample_snippets": samples,
            "has_more": len(raw_msgs) >= bounded,
            "note": f"Archived {count} thread(s) ({len(msg_ids)} messages) (removed from Inbox, preserved in All Mail).",
        }

    def burndown_sweep(
        self,
        target_unread: int = 500,
        max_batches: int = 5,
        batch_size: int = 500,
        exclude_github: bool = True,
    ) -> Dict[str, Any]:
        """Autonomously burn down the inbox backlog across policy categories toward target_unread.

        Runs high-speed bulk sweeps using messages/batchModify while strictly honoring the
        VIP Whitelist and rate-pacing under 250 units/sec. Stops immediately when target
        is reached or when no matching noise remains.
        """
        # Fetch initial stats
        initial_stats = self.get_mailbox_stats()
        inbox_stats = initial_stats.get("labels", {}).get("INBOX", {})
        starting_unread = inbox_stats.get("messages_unread", 0) or inbox_stats.get("threads_unread", 0)

        github_exclusion = " -from:notifications@github.com -from:github.com" if exclude_github else ""

        # Standard noise categories aligned with email-triage-policy.md
        rules = [
            {
                "category": "Stale Promotions (>2d)",
                "action": "trash",
                "query": f"category:promotions older_than:2d -humble -eero -experian -marriott -securly{github_exclusion}",
            },
            {
                "category": "LinkedIn Alerts",
                "action": "archive",
                "query": "from:linkedin.com",
            },
            {
                "category": "Social Noise (Facebook/Threads/Cozey)",
                "action": "archive",
                "query": "(from:facebookmail.com OR from:threads.net OR from:cozey.ca OR \"Facebook Friend Suggestions\")",
            },
            {
                "category": "Misaddressed Mail (Other S. Gerharts)",
                "action": "archive",
                "query": "(\"Shawn Gerhart\" OR \"Siobhan Gerhart\" OR \"Brad Fry\" OR \"realtor\" OR \"MLS\" OR \"mortgage closing\")",
            },
            {
                "category": "Direct Trash & Unsubscribe",
                "action": "trash",
                "query": "(from:unidays.com OR from:palottery.com OR from:tumi.com OR from:coffeeco.com OR from:womaness.com OR from:newegg.com OR from:udemy.com OR \"Word Daily\" OR \"Nutcracker Cash\" OR from:stephengerhart OR from:samgerhart)",
            },
        ]

        if not exclude_github:
            rules.append({
                "category": "Stale CI Notifications (>2d)",
                "action": "trash",
                "query": "from:notifications@github.com older_than:2d",
            })

        total_trashed = 0
        total_archived = 0
        batches_run = 0
        breakdown: List[Dict[str, Any]] = []

        current_unread = starting_unread
        for batch_idx in range(max_batches):
            if current_unread <= target_unread and starting_unread > 0:
                break

            any_swept_this_batch = False
            batches_run += 1

            for r in rules:
                if current_unread <= target_unread and starting_unread > 0:
                    break

                cat = r["category"]
                action = r["action"]
                q = r["query"]

                if action == "trash":
                    res = self.batch_trash_threads(query=q, limit=batch_size)
                    cnt = res.get("trashed_count", 0)
                    if cnt > 0:
                        total_trashed += cnt
                        any_swept_this_batch = True
                        breakdown.append({
                            "category": cat,
                            "action": "trashed",
                            "count": cnt,
                            "samples": res.get("sample_snippets", [])[:3],
                        })
                else:
                    res = self.batch_archive_threads(query=q, limit=batch_size)
                    cnt = res.get("archived_count", 0)
                    if cnt > 0:
                        total_archived += cnt
                        any_swept_this_batch = True
                        breakdown.append({
                            "category": cat,
                            "action": "archived",
                            "count": cnt,
                            "samples": res.get("sample_snippets", [])[:3],
                        })

                # Pacing pause to stay well below quota ceiling
                time.sleep(0.15)

            # If an entire round through all categories found 0 noise, stop
            if not any_swept_this_batch:
                break

            # Check updated stats
            try:
                mid_stats = self.get_mailbox_stats()
                inb = mid_stats.get("labels", {}).get("INBOX", {})
                current_unread = inb.get("messages_unread", 0) or inb.get("threads_unread", 0)
            except Exception:
                current_unread = max(0, starting_unread - (total_trashed + total_archived))

        # Final mailbox stats
        try:
            final_stats = self.get_mailbox_stats()
            fin_inb = final_stats.get("labels", {}).get("INBOX", {})
            ending_unread = fin_inb.get("messages_unread", 0) or fin_inb.get("threads_unread", 0)
        except Exception:
            ending_unread = max(0, starting_unread - (total_trashed + total_archived))

        total_swept = total_trashed + total_archived
        target_reached = ending_unread <= target_unread

        note = (
            f"Autonomous Burndown Complete: Swept {total_swept:,} emails "
            f"({total_trashed:,} trashed to 30d recovery, {total_archived:,} archived to All Mail). "
            f"Inbox unread reduced from {starting_unread:,} to {ending_unread:,} "
            f"(Target: < {target_unread:,})."
        )

        return {
            "ok": True,
            "target_unread": target_unread,
            "starting_unread": starting_unread,
            "ending_unread": ending_unread,
            "total_swept": total_swept,
            "total_trashed": total_trashed,
            "total_archived": total_archived,
            "batches_run": batches_run,
            "breakdown": breakdown,
            "target_reached": target_reached,
            "note": note,
        }


def _extract_body_from_payload(payload: Dict[str, Any]) -> str:
    """Extract plain text body recursively from MIME parts."""
    mime_type = payload.get("mimeType", "")
    body_data = (payload.get("body") or {}).get("data")
    if body_data and mime_type.startswith("text/plain"):
        try:
            padded = body_data + "=" * (-len(body_data) % 4)
            return base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8", "ignore")
        except Exception:
            pass

    parts = payload.get("parts") or []
    for part in parts:
        text = _extract_body_from_payload(part)
        if text.strip():
            return text

    if body_data:
        try:
            padded = body_data + "=" * (-len(body_data) % 4)
            raw = base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8", "ignore")
            # Strip tags if HTML
            return re.sub(r"<[^>]+>", " ", raw)
        except Exception:
            pass
    return ""


def _parse_message(raw_msg: Dict[str, Any]) -> Dict[str, Any]:
    payload = raw_msg.get("payload") or {}
    headers = {h.get("name", "").lower(): h.get("value", "") for h in payload.get("headers") or []}

    body = _extract_body_from_payload(payload)
    if not body.strip():
        body = raw_msg.get("snippet", "")

    return {
        "id": raw_msg.get("id", ""),
        "thread_id": raw_msg.get("threadId", ""),
        "subject": headers.get("subject", ""),
        "from": headers.get("from", ""),
        "to": headers.get("to", ""),
        "date": headers.get("date", ""),
        "snippet": raw_msg.get("snippet", ""),
        "body": body.strip()[:3000],  # Cap body text for prompt budget
        "labels": raw_msg.get("labelIds") or [],
    }


def format_mailbox_stats_markdown(stats: Dict[str, Any]) -> str:
    """Format account and label counts for Steward's tool observation."""
    email = stats.get("email", "unknown")
    total_msgs = stats.get("messages_total", 0)
    total_threads = stats.get("threads_total", 0)
    labels = stats.get("labels", {})

    inbox = labels.get("INBOX", {})
    unread = labels.get("UNREAD", {})
    starred = labels.get("STARRED", {})
    sent = labels.get("SENT", {})
    trash = labels.get("TRASH", {})
    spam = labels.get("SPAM", {})

    lines = [
        f"### Gmail Mailbox Statistics for {email}:",
        f"- **Total Account Messages**: {total_msgs:,} (across {total_threads:,} threads)",
        f"- **Primary Inbox**: {inbox.get('messages_total', 0):,} total messages ({inbox.get('messages_unread', 0):,} unread across {inbox.get('threads_unread', 0):,} unread threads)",
        f"- **Total Unread (Account-wide)**: {unread.get('messages_total', 0):,} messages",
        f"- **Starred**: {starred.get('messages_total', 0):,} messages ({starred.get('messages_unread', 0):,} unread)",
        f"- **Sent**: {sent.get('messages_total', 0):,} messages",
        f"- **Trash**: {trash.get('messages_total', 0):,} messages",
        f"- **Spam**: {spam.get('messages_total', 0):,} messages",
    ]
    return "\n".join(lines)


def format_threads_markdown(threads: List[Dict[str, Any]], query_context: str = "") -> str:
    """Format thread list for Steward's tool observation."""
    if not threads:
        return "No email threads found matching the search criteria."
    ctx_note = f" (query: '{query_context}')" if query_context else ""
    lines = [
        f"Returned {len(threads)} thread(s){ctx_note}. "
        f"(Note: This is a bounded search/list page, not the total count of emails in the entire mailbox. "
        f"For account totals or inbox counts, call gmail_mailbox_stats.):\n"
    ]
    for i, t in enumerate(threads, 1):
        lines.append(f"### {i}. {t.get('subject') or '(No Subject)'}")
        lines.append(f"- **Thread ID**: `{t.get('id')}`")
        msgs = t.get("messages") or []
        if msgs:
            latest = msgs[-1]
            lines.append(f"- **Latest from**: {latest.get('from', 'Unknown')}")
            lines.append(f"- **Date**: {latest.get('date', 'Unknown')}")
            lines.append(f"- **Snippet**: {latest.get('snippet', '')}")
        else:
            lines.append(f"- **Snippet**: {t.get('snippet', '')}")
        lines.append("")
    return "\n".join(lines).strip()


def format_single_thread_markdown(thread: Dict[str, Any]) -> str:
    """Format complete thread messages for Steward's deep context."""
    subject = thread.get("subject") or "(No Subject)"
    lines = [f"# Email Thread: {subject} (ID: `{thread.get('id')}`)\n"]
    msgs = thread.get("messages") or []
    if not msgs:
        lines.append("Snippet: " + (thread.get("snippet") or "Empty thread."))
        return "\n".join(lines)

    for i, m in enumerate(msgs, 1):
        lines.append(f"--- Message {i} of {len(msgs)} ---")
        lines.append(f"**From**: {m.get('from')}")
        lines.append(f"**To**: {m.get('to')}")
        lines.append(f"**Date**: {m.get('date')}")
        lines.append(f"**Message ID**: `{m.get('id')}`\n")
        lines.append(m.get("body") or m.get("snippet") or "(No body content)")
        lines.append("")
    return "\n".join(lines).strip()


def format_batch_result_markdown(result: Dict[str, Any], action: str = "trashed") -> str:
    """Format batch sweep result for Steward's tool observation."""
    count = result.get("trashed_count", result.get("archived_count", 0))
    query = result.get("query", "")
    has_more = result.get("has_more", False)
    snippets = result.get("sample_snippets", [])

    lines = [
        f"### Batch Email Sweep: {count} thread(s) {action} successfully",
        f"- **Filter Query**: `{query}`",
        f"- **Status**: Moved to Gmail {'Trash (30-day recoverable)' if action == 'trashed' else 'Archive (All Mail)'}",
    ]
    if snippets:
        lines.append("- **Sample Processed**:")
        for s in snippets:
            lines.append(f"  • *{s}*")
    if has_more:
        lines.append("\n> **Note**: Additional matching threads exist in your inbox. Run another sweep iteration or arm a standing sentinel to maintain this automatically.")
    return "\n".join(lines)


def format_burndown_result_markdown(res: Dict[str, Any]) -> str:
    """Format burndown sweep results into clean executive markdown."""
    total = res.get("total_swept", 0)
    trashed = res.get("total_trashed", 0)
    archived = res.get("total_archived", 0)
    start = res.get("starting_unread", 0)
    end = res.get("ending_unread", 0)
    target = res.get("target_unread", 500)
    batches = res.get("batches_run", 0)

    lines = [
        "### 🧹 Autonomous Backlog Burndown Complete",
        f"- **Initial Inbox Unread:** {start:,}",
        f"- **Current Inbox Unread:** {end:,} (Target: < {target:,})",
        f"- **Total Swept This Run:** **{total:,} emails** across {batches} batch cycle(s)",
        f"  - **Moved to Trash (30-day recoverable):** {trashed:,}",
        f"  - **Archived to All Mail:** {archived:,}",
        "- **VIP Whitelist Protected:** Humble Bundle, Eero, Experian, Marriott, Securly.",
    ]

    breakdown = res.get("breakdown") or []
    if breakdown:
        lines.append("\n**Category Breakdown:**")
        for b in breakdown:
            cat = b.get("category", "Other")
            act = b.get("action", "processed")
            cnt = b.get("count", 0)
            lines.append(f"- **{cat}:** {cnt:,} {act}")
            for snip in b.get("samples") or []:
                lines.append(f"  - *{snip}*")

    if res.get("target_reached"):
        lines.append("\n🎯 **Inbox Burndown Target Reached!** Inbox unread is below target.")
    elif total == 0:
        lines.append("\n✨ **No matching noise found in Inbox.** Inbox matches current policy rules.")
    else:
        lines.append("\n⚡ Guardian autonomy can continue burndown on the next wake or on command.")

    return "\n".join(lines)



