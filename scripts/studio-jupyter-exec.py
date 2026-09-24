#!/usr/bin/env python3
"""Execute a short Python cell on Studio Jupyter (FEAT-015 / IWO-047 helper).

Reads token from ~/.ai-lab/studio-jupyter.token (never prints it).
Dry-run prints connectivity only unless --exec CODE or --preflight.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
import urllib.error
import urllib.request
from pathlib import Path

PREFLIGHT_CODE = r"""
import os, platform, shutil, sys
print("python", sys.version.split()[0])
print("machine", platform.machine())
print("hostname", platform.node())
usage = shutil.disk_usage(os.path.expanduser("~"))
print(f"disk_free_gb={usage.free / 1e9:.1f}")
print(f"disk_total_gb={usage.total / 1e9:.1f}")
for mod in ("torch", "transformers", "mlx", "mlx_lm", "huggingface_hub"):
    try:
        m = __import__(mod)
        print(f"{mod}=yes ver={getattr(m, '__version__', '?')}")
    except Exception:
        print(f"{mod}=no")
home = os.path.expanduser("~")
for p in (
    f"{home}/.cache/huggingface/hub",
    f"{home}/models",
    f"{home}/.ai-lab/antares",
):
    print(f"path_exists {p}={os.path.isdir(p)}")
"""


def _token() -> str:
    path = Path.home() / ".ai-lab" / "studio-jupyter.token"
    if not path.is_file():
        raise SystemExit(f"missing token file: {path}")
    return path.read_text(encoding="utf-8").strip()


def _api(base: str, token: str, path: str, data=None, method: str | None = None):
    url = base.rstrip("/") + path
    headers = {"Authorization": f"token {token}", "Content-Type": "application/json"}
    body = None if data is None else json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers=headers,
        method=method or ("POST" if body is not None else "GET"),
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        raw = resp.read()
        return json.loads(raw) if raw else {}


def _delete_kernel(base: str, token: str, kid: str) -> None:
    req = urllib.request.Request(
        f"{base.rstrip('/')}/api/kernels/{kid}",
        headers={"Authorization": f"token {token}"},
        method="DELETE",
    )
    try:
        urllib.request.urlopen(req, timeout=30)
    except urllib.error.HTTPError:
        pass


def execute_on_studio(code: str, *, base: str, kernel_name: str | None = None, timeout: int = 300) -> str:
    try:
        import websocket  # type: ignore
    except ImportError as exc:
        raise SystemExit(
            "websocket-client required on the caller host: python3 -m pip install --user websocket-client"
        ) from exc

    token = _token()
    info = _api(base, token, "/api")
    specs = _api(base, token, "/api/kernelspecs")
    available = specs.get("kernelspecs") or {}
    name = kernel_name or (
        "studio-m5" if "studio-m5" in available else (specs.get("default") or "python3")
    )
    kernel = _api(base, token, "/api/kernels", {"name": name})
    kid = kernel["id"]
    ws_url = base.replace("http://", "ws://").replace("https://", "wss://")
    ws_url = f"{ws_url.rstrip('/')}/api/kernels/{kid}/channels?token={token}"
    ws = websocket.create_connection(ws_url, timeout=60)
    try:
        msg_id = str(uuid.uuid4())
        session = str(uuid.uuid4())
        ws.send(
            json.dumps(
                {
                    "header": {
                        "msg_id": msg_id,
                        "username": "ai-lab",
                        "session": session,
                        "msg_type": "execute_request",
                        "version": "5.3",
                    },
                    "parent_header": {},
                    "metadata": {},
                    "content": {
                        "code": code,
                        "silent": False,
                        "store_history": False,
                        "user_expressions": {},
                        "allow_stdin": False,
                        "stop_on_error": True,
                    },
                    "channel": "shell",
                    "buffers": [],
                }
            )
        )
        outs: list[str] = []
        deadline = time.time() + timeout
        while time.time() < deadline:
            msg = json.loads(ws.recv())
            parent = msg.get("parent_header") or {}
            if parent.get("msg_id") not in (None, "", msg_id):
                continue
            mt = msg.get("msg_type")
            if mt == "stream":
                outs.append(msg.get("content", {}).get("text", ""))
            elif mt == "execute_result":
                data = msg.get("content", {}).get("data") or {}
                outs.append(str(data.get("text/plain", "")))
            elif mt == "error":
                tb = msg.get("content", {}).get("traceback") or []
                outs.append("ERROR:\n" + "\n".join(tb[-5:]))
                break
            elif mt == "execute_reply":
                break
        else:
            outs.append("ERROR: timeout waiting for execute_reply")
        return "".join(outs)
    finally:
        try:
            ws.close()
        except Exception:
            pass
        _delete_kernel(base, token, kid)
        _ = info  # silence lint


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base",
        default="http://mac-studio:8888",
        help="Studio Jupyter base URL",
    )
    parser.add_argument("--preflight", action="store_true", help="Disk + package probe")
    parser.add_argument("--exec-file", help="Run Python file contents on Studio")
    parser.add_argument("--dry-run", action="store_true", help="Only hit /api (no kernel)")
    args = parser.parse_args()

    token = _token()
    try:
        info = _api(args.base, token, "/api")
    except Exception as exc:
        print(f"jupyter_unreachable: {exc}", file=sys.stderr)
        return 1
    print(f"jupyter_ok version={info.get('version')}")

    if args.dry_run and not args.preflight and not args.exec_file:
        return 0

    if args.preflight:
        print(execute_on_studio(PREFLIGHT_CODE, base=args.base))
        return 0

    if args.exec_file:
        code = Path(args.exec_file).read_text(encoding="utf-8")
        print(execute_on_studio(code, base=args.base, timeout=3600))
        return 0

    print("pass --preflight, --exec-file, or --dry-run", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
