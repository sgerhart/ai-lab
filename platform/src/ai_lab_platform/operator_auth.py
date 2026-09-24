"""Operator username/password + opaque sessions (personal lab login).

Credentials and sessions live under ``~/.ai-lab/`` (never Git).
Password hashing: PBKDF2-HMAC-SHA256 (stdlib).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import time
from pathlib import Path
from typing import Any

_USER_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9._-]{0,31}$")
_PBKDF2_ROUNDS = 260_000
_SESSION_TTL_SECONDS = 60 * 60 * 24 * 30  # 30 days


def lab_dir() -> Path:
    override = os.environ.get("AI_LAB_HOME")
    if override:
        return Path(override)
    return Path.home() / ".ai-lab"


def operator_path() -> Path:
    return lab_dir() / "operator.json"


def sessions_path() -> Path:
    return lab_dir() / "sessions.json"


def _chmod600(path: Path) -> None:
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def operator_configured() -> bool:
    path = operator_path()
    if not path.is_file():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return bool(data.get("username") and data.get("password_hash") and data.get("salt"))


def set_operator_password(username: str, password: str) -> dict[str, Any]:
    """Create or replace the single operator account. Returns public metadata only."""
    username = (username or "").strip()
    if not _USER_RE.match(username):
        raise ValueError("invalid username")
    if len(password) < 8:
        raise ValueError("password must be at least 8 characters")
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        _PBKDF2_ROUNDS,
    ).hex()
    lab_dir().mkdir(parents=True, exist_ok=True)
    payload = {
        "username": username,
        "salt": salt,
        "password_hash": digest,
        "kdf": "pbkdf2_sha256",
        "rounds": _PBKDF2_ROUNDS,
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    path = operator_path()
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    _chmod600(path)
    return {"ok": True, "username": username, "path": str(path)}


def verify_operator_password(username: str, password: str) -> bool:
    path = operator_path()
    if not path.is_file():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if (username or "").strip() != data.get("username"):
        return False
    salt = str(data.get("salt") or "")
    expected = str(data.get("password_hash") or "")
    rounds = int(data.get("rounds") or _PBKDF2_ROUNDS)
    if not salt or not expected:
        return False
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        rounds,
    ).hex()
    return hmac.compare_digest(digest, expected)


def _read_sessions() -> dict[str, Any]:
    path = sessions_path()
    if not path.is_file():
        return {"sessions": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"sessions": {}}
    if not isinstance(data.get("sessions"), dict):
        return {"sessions": {}}
    return data


def _write_sessions(data: dict[str, Any]) -> None:
    lab_dir().mkdir(parents=True, exist_ok=True)
    path = sessions_path()
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    _chmod600(path)


def create_session(username: str) -> str:
    token = secrets.token_urlsafe(32)
    data = _read_sessions()
    now = int(time.time())
    # Drop expired
    sessions = {
        k: v
        for k, v in (data.get("sessions") or {}).items()
        if isinstance(v, dict) and int(v.get("expires_at") or 0) > now
    }
    sessions[token] = {
        "username": username,
        "created_at": now,
        "expires_at": now + _SESSION_TTL_SECONDS,
    }
    data["sessions"] = sessions
    _write_sessions(data)
    return token


def session_valid(token: str) -> bool:
    if not token:
        return False
    data = _read_sessions()
    entry = (data.get("sessions") or {}).get(token)
    if not isinstance(entry, dict):
        return False
    return int(entry.get("expires_at") or 0) > int(time.time())


def revoke_session(token: str) -> bool:
    data = _read_sessions()
    sessions = data.get("sessions") or {}
    if token not in sessions:
        return False
    del sessions[token]
    data["sessions"] = sessions
    _write_sessions(data)
    return True


def login(username: str, password: str) -> dict[str, Any]:
    if not operator_configured():
        raise ValueError("operator_not_configured")
    if not verify_operator_password(username, password):
        raise PermissionError("invalid_credentials")
    token = create_session(username.strip())
    return {
        "ok": True,
        "token": token,
        "token_type": "Bearer",
        "expires_in": _SESSION_TTL_SECONDS,
        "username": username.strip(),
    }


__all__ = [
    "create_session",
    "lab_dir",
    "login",
    "operator_configured",
    "operator_path",
    "revoke_session",
    "session_valid",
    "set_operator_password",
    "verify_operator_password",
]
