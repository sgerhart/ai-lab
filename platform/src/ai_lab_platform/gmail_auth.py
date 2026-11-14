"""CLI / Interactive Setup tool to authorize Steward with Gmail OAuth2."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import sys
import threading
from typing import Optional
import urllib.parse
import urllib.request
import webbrowser

from .gmail import (
    DEFAULT_CREDENTIALS_PATH,
    DEFAULT_SCOPES,
    DEFAULT_TOKEN_PATH,
    GOOGLE_TOKEN_URL,
    GmailClient,
)

AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
CALLBACK_HOST = "127.0.0.1"
CALLBACK_PORT = 8095
REDIRECT_URI = f"http://{CALLBACK_HOST}:{CALLBACK_PORT}/callback"


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    auth_code: Optional[str] = None
    error: Optional[str] = None

    def do_GET(self) -> None:
        parsed = urllib.parse.urlsplit(self.path)
        qs = urllib.parse.parse_qs(parsed.query)

        if "code" in qs:
            OAuthCallbackHandler.auth_code = qs["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                b"<html><body style='font-family:sans-serif;background:#111;color:#eee;text-align:center;padding:40px;'>"
                b"<h2 style='color:#7cb8ff;'>Gmail Authorization Received!</h2>"
                b"<p>You can close this browser tab and return to the terminal.</p>"
                b"</body></html>"
            )
        elif "error" in qs:
            OAuthCallbackHandler.error = qs["error"][0]
            self.send_response(400)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"<html><body><h2>Authorization Denied</h2></body></html>")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format: str, *args: object) -> None:
        pass


def run_auth_flow(
    credentials_path: Path = DEFAULT_CREDENTIALS_PATH,
    token_path: Path = DEFAULT_TOKEN_PATH,
    manual: bool = False,
) -> bool:
    client = GmailClient(credentials_path=credentials_path, token_path=token_path)
    if not client.has_credentials():
        print(f"\n[!] Missing credentials file at: {credentials_path}")
        print("To set up Gmail:")
        print("1. Go to Google Cloud Console (https://console.cloud.google.com)")
        print("2. Create or select a project (e.g. 'AI Lab')")
        print("3. Enable the 'Gmail API' under APIs & Services")
        print("4. Configure OAuth Consent Screen:")
        print("   - User Type: External")
        print("   - Add your email under 'Test users'")
        print("5. Create Credentials:")
        print("   - Type: 'OAuth client ID' -> Application type: 'Desktop app'")
        print("   - Download the JSON file")
        print(f"6. Save it to: {credentials_path}")
        print("   (e.g., mkdir -p ~/.ai-lab/secrets && cp ~/Downloads/client_secret_*.json ~/.ai-lab/secrets/gmail-credentials.json)\n")
        return False

    creds = client.load_credentials()
    client_id = creds.get("client_id")
    client_secret = creds.get("client_secret")
    if not client_id or not client_secret:
        print("[!] Client ID or Client Secret missing in credentials file.")
        return False

    scope_str = " ".join(DEFAULT_SCOPES)
    auth_params = {
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": scope_str,
        "access_type": "offline",
        "prompt": "consent",
    }
    auth_url = f"{AUTH_ENDPOINT}?{urllib.parse.urlencode(auth_params)}"

    print("\n=== Steward Gmail Authorization ===")
    print("Scopes requested:")
    for s in DEFAULT_SCOPES:
        print(f" - {s}")
    print("\nPlease open the following URL in your browser to sign in:\n")
    print(auth_url)
    print("\n--------------------------------------------------------------")

    code = None
    if not manual:
        try:
            webbrowser.open(auth_url)
        except Exception:
            pass

        try:
            server = HTTPServer((CALLBACK_HOST, CALLBACK_PORT), OAuthCallbackHandler)
            print(f"Waiting for authorization callback on http://{CALLBACK_HOST}:{CALLBACK_PORT}/callback ...")
            print("(Or press Ctrl+C if you prefer to paste the code manually)\n")
            server.handle_request()
            code = OAuthCallbackHandler.auth_code
            server.server_close()
        except KeyboardInterrupt:
            print("\nSwitched to manual entry.")
        except Exception as exc:
            print(f"[Notice] Local callback server unavailable ({exc}). Switched to manual entry.")

    if not code:
        code_input = input("\nEnter the authorization code (or the full redirect URL): ").strip()
        if "code=" in code_input:
            parsed = urllib.parse.urlsplit(code_input)
            qs = urllib.parse.parse_qs(parsed.query)
            code = qs.get("code", [""])[0]
        else:
            code = code_input

    if not code:
        print("[!] No authorization code provided. Aborted.")
        return False

    # Exchange authorization code for token
    token_params = urllib.parse.urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
    }).encode("utf-8")

    req = urllib.request.Request(
        GOOGLE_TOKEN_URL,
        data=token_params,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        err = exc.read().decode("utf-8", "ignore")
        print(f"[!] Token exchange failed: {err}")
        return False
    except Exception as exc:
        print(f"[!] Request error: {exc}")
        return False

    access_token = data.get("access_token")
    refresh_token = data.get("refresh_token")
    if not access_token:
        print(f"[!] No access token received: {data}")
        return False

    expires_in = data.get("expires_in", 3600)
    expiry = datetime.fromtimestamp(
        datetime.now(timezone.utc).timestamp() + expires_in, tz=timezone.utc
    ).isoformat()

    token_payload = {
        "token": access_token,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
        "scopes": DEFAULT_SCOPES,
        "expiry": expiry,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    client.save_token_data(token_payload)

    # Test profile connection
    try:
        prof = client.get_profile()
        email = prof.get("emailAddress", "Unknown")
        print(f"\n[+] SUCCESS! Steward is now connected to Gmail for: {email}")
        print(f"Token saved to: {token_path}")
        return True
    except Exception as exc:
        print(f"[!] Saved token but profile verification failed: {exc}")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Authorize Steward with Gmail OAuth2")
    parser.add_argument("--status", action="store_true", help="Check current Gmail connection status")
    parser.add_argument("--manual", action="store_true", help="Paste auth code manually without local server")
    args = parser.parse_args()

    client = GmailClient()
    if args.status:
        st = client.status()
        print(json.dumps(st, indent=2))
        sys.exit(0 if st.get("connected") else 1)

    ok = run_auth_flow(manual=args.manual)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

