"""Nexus files are read as bytes so iCloud Drive sendfile does not stall."""

from __future__ import annotations

import asyncio
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.control_app import _ICloudFileResponse, _ICloudStaticFiles  # noqa: E402
from starlette.responses import FileResponse  # noqa: E402


class ICloudStaticTests(unittest.TestCase):
    def test_pathsend_offer_still_sends_file_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "index.html"
            path.write_text("hello nexus", encoding="utf-8")
            messages: list[dict] = []

            async def send(message: dict) -> None:
                messages.append(message)

            async def receive() -> dict:
                return {"type": "http.disconnect"}

            scope = {
                "type": "http",
                "method": "GET",
                "headers": [],
                "extensions": {"http.response.pathsend": {}},
            }
            response = _ICloudFileResponse(path, stat_result=path.stat())
            asyncio.run(response(scope, receive, send))

        self.assertFalse(any(message.get("type") == "http.response.pathsend" for message in messages))
        body = b"".join(message.get("body", b"") for message in messages)
        self.assertEqual(body, b"hello nexus")

    def test_static_mount_uses_byte_response(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "index.html").write_text("hello nexus", encoding="utf-8")
            files = _ICloudStaticFiles(directory=tmp, html=True)
            scope = {"type": "http", "headers": []}
            stat_result = (Path(tmp) / "index.html").stat()
            response = files.file_response(Path(tmp) / "index.html", stat_result, scope)
        self.assertIs(type(response), _ICloudFileResponse)
        self.assertIsInstance(response, FileResponse)
