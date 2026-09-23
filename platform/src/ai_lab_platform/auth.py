"""Control-plane auth helpers.

Modes (AI_LAB_AUTH_MODE):

- ``token`` (default): require ``Authorization: Bearer <AI_LAB_API_TOKEN>`` when
  the token is configured.
- ``trusted_tailnet``: single-operator lab — requests from Tailscale CGNAT
  (100.64.0.0/10) or loopback are trusted; bearer token still accepted as an
  override. Non-tailnet clients still need the bearer token when configured.

Tailscale membership is still not a substitute for public-Internet exposure.
Keep the API off ``0.0.0.0``.
"""

from __future__ import annotations

import ipaddress
from typing import Any

from fastapi import HTTPException, Request

_TAILNET = ipaddress.ip_network("100.64.0.0/10")
_LOOPBACK = ipaddress.ip_network("127.0.0.0/8")


def client_ip(request: Request) -> str:
    if request.client and request.client.host:
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
    mode_n = (mode or "token").strip().lower()
    if mode_n == "trusted_tailnet":
        paste_required = bool(token_configured) and not trusted
        return {
            "ok": True,
            "mode": "trusted_tailnet",
            "token_configured": token_configured,
            "peer_trusted": trusted,
            "paste_required": paste_required,
            "note": "Tailnet/loopback peers skip bearer paste. Keep API off public Internet.",
        }
    paste_required = bool(token_configured)
    return {
        "ok": True,
        "mode": "token",
        "token_configured": token_configured,
        "peer_trusted": trusted,
        "paste_required": paste_required,
        "note": "Bearer token required when AI_LAB_API_TOKEN is set.",
    }


def require_auth(
    *,
    mode: str,
    expected_token: str,
    authorization: str | None,
    request: Request,
) -> None:
    """Raise 401 when the caller is not allowed."""
    if not expected_token:
        return
    mode_n = (mode or "token").strip().lower()
    if authorization == f"Bearer {expected_token}":
        return
    if mode_n == "trusted_tailnet" and is_trusted_peer(client_ip(request)):
        return
    raise HTTPException(status_code=401, detail="unauthorized")
