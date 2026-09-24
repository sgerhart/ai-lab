"""Control-plane auth helpers.

Accepts either:

- ``Authorization: Bearer <AI_LAB_API_TOKEN>`` (scripts / legacy), or
- ``Authorization: Bearer <session>`` from username/password login
  (``~/.ai-lab/operator.json`` + ``sessions.json``).

Fail closed when neither an API token nor an operator login is configured.
Public endpoints (`/health`, `/v1/auth/status`, `/v1/auth/login`) must not
call ``require_auth``.

Keep the API off ``0.0.0.0``.
"""

from __future__ import annotations

import ipaddress
from typing import Any, Callable

from .operator_auth import operator_configured, session_valid

_TAILNET = ipaddress.ip_network("100.64.0.0/10")
_LOOPBACK = ipaddress.ip_network("127.0.0.0/8")


class AuthError(Exception):
    """Raised when the caller is not allowed. Mapped to HTTP 401 by the app."""

    def __init__(self, detail: str = "unauthorized", *, status_code: int = 401) -> None:
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


def client_ip(request: Any) -> str:
    if getattr(request, "client", None) and request.client and request.client.host:
        return request.client.host
    return ""


def is_trusted_peer(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return addr in _TAILNET or addr in _LOOPBACK


def auth_status(*, mode: str, token_configured: bool, peer_ip: str) -> dict[str, Any]:
    trusted = is_trusted_peer(peer_ip)
    mode_n = (mode or "token").strip().lower() or "token"
    login_ok = operator_configured()
    auth_ready = bool(token_configured) or login_ok
    note = (
        "Sign in with username and password, or use a lab API bearer token."
        if login_ok
        else (
            "Bearer token required when AI_LAB_API_TOKEN is set."
            if token_configured
            else "No operator login or API token configured — authenticated routes refuse."
        )
    )
    return {
        "ok": True,
        "mode": mode_n if mode_n in {"token", "trusted_tailnet"} else "token",
        "token_configured": bool(token_configured),
        "login_available": login_ok,
        "auth_ready": auth_ready,
        "peer_trusted": trusted,
        # Prefer login UI when operator account exists; else token paste.
        "paste_required": auth_ready and not login_ok,
        "login_required": login_ok,
        "note": note,
    }


def require_auth(
    *,
    mode: str,
    expected_token: str,
    authorization: str | None,
    request: Any,
    session_checker: Callable[[str], bool] | None = None,
) -> None:
    """Raise AuthError when the caller is not allowed."""
    _ = mode
    _ = request
    login_ok = operator_configured()
    if not expected_token and not login_ok:
        raise AuthError("api_token_not_configured")

    bearer = ""
    if authorization and authorization.startswith("Bearer "):
        bearer = authorization[7:].strip()

    if expected_token and bearer and hmac_safe_eq(bearer, expected_token):
        return

    checker = session_checker or session_valid
    if bearer and checker(bearer):
        return

    raise AuthError("unauthorized")


def hmac_safe_eq(a: str, b: str) -> bool:
    import hmac

    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))
