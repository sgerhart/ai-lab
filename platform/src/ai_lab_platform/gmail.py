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
import re
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

    def get_valid_access_token(self) -> str:
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

        if token and not is_expired:
            return str(token)

        if not refresh_token:
            if token:
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
    ) -> Dict[str, Any]:
        token = self.get_valid_access_token()
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
            with self.opener(req, timeout=15) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            err_body = exc.read().decode("utf-8", "ignore")
            raise GmailAPIError(f"Gmail API error {exc.code} for {url}: {err_body}") from exc
        except Exception as exc:
            raise GmailAPIError(f"Request to {url} failed: {exc}") from exc

    def get_profile(self) -> Dict[str, Any]:
        """Fetch user profile to verify connection and email address."""
        return self._api_request("profile")

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
        res = self._api_request("threads", params={"q": query or None, "maxResults": bounded})
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


def format_threads_markdown(threads: List[Dict[str, Any]]) -> str:
    """Format thread list for Steward's tool observation."""
    if not threads:
        return "No email threads found matching the search criteria."
    lines = [f"Found {len(threads)} email thread(s):\n"]
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

