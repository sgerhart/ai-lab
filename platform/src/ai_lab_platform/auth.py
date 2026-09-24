"""Control-plane auth helpers.

Modes (AI_LAB_AUTH_MODE):

- ``token`` (default): require ``Authorization: Bearer <AI_LAB_API_TOKEN>``.
- ``trusted_tailnet``: same bearer requirement when a token is configured.
  ``peer_trusted`` is informational only (Tailscale CGNAT / loopback). Tailnet
  membership is **not** a substitute for application authentication.

Fail closed: if ``AI_LAB_API_TOKEN`` is unset, authenticated routes refuse
(401). Public endpoints (`/health`, `/v1/auth/status`) must not call
``require_auth``.

Keep the API off ``0.0.0.0``.
"""

from __future__ import annotations

import ipaddress
from typing import Any

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
    # Bearer is always required when a token is configured (all modes).
    paste_required = bool(token_configured)
    note = (
        "Bearer token required for API routes when AI_LAB_API_TOKEN is set. "
        "Tailnet peer trust is informational only."
        if token_configured
        else "AI_LAB_API_TOKEN is unset — authenticated routes refuse (fail closed)."
    )
    return {
        "ok": True,
        "mode": mode_n if mode_n in {"token", "trusted_tailnet"} else "token",
        "token_configured": token_configured,
        "peer_trusted": trusted,
        "paste_required": paste_required,
        "note": note,
    }


def require_auth(
    *,
    mode: str,
    expected_token: str,
    authorization: str | None,
    request: Any,
) -> None:
    """Raise AuthError when the caller is not allowed.

    When a token is configured, a matching Bearer header is always required —
    including for Tailscale CGNAT and loopback peers.
    When no token is configured, refuse (fail closed).
    """
    _ = mode  # retained for status / future policy; not a peer waiver
    _ = request
    if not expected_token:
        raise AuthError("api_token_not_configured")
    if authorization == f"Bearer {expected_token}":
        return
    raise AuthError("unauthorized")
