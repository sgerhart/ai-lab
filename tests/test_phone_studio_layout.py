"""Unit tests for Phone Studio layout and mobile contract (IWO-110, FEAT-023).

Verifies:
1. Dynamic viewport height (100dvh) on html/body and .app.
2. Composer dock padding accounts for safe-area-inset-bottom and side insets.
3. Media query for max-width 720px formats sidebar as an overlay drawer with a backdrop.
4. Touch targets for send, sidebar toggle, approve, and deny meet the 44px mobile touch criterion.
5. Composer hint hides "Press Enter" on phone viewports via .desktop-hint.
6. Desktop width (> 720px) retains the 260px sidebar column.
7. Web app manifest and Apple Home Screen title ("AI LAB", start_url="/").
8. /manifest.json route served by the control plane.
"""

from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

try:
    from fastapi.testclient import TestClient
    from langgraph.checkpoint.memory import MemorySaver

    from ai_lab_platform.control_app import create_control_app
    from ai_lab_platform.model_router import ModelRouter
    from ai_lab_platform.store import SqliteStore

    _HAS_FASTAPI = True
except ImportError:
    _HAS_FASTAPI = False


class PhoneStudioLayoutHtmlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.html_path = ROOT / "platform" / "src" / "ai_lab_platform" / "web" / "agents.html"
        cls.html = cls.html_path.read_text(encoding="utf-8")
        cls.manifest_path = ROOT / "platform" / "src" / "ai_lab_platform" / "web" / "static" / "manifest.json"

    def test_meta_viewport_and_pwa_tags(self) -> None:
        """HTML head includes viewport-fit=cover, PWA capability, and Apple Home Screen title."""
        self.assertIn('viewport-fit=cover', self.html)
        self.assertIn('<meta name="apple-mobile-web-app-capable" content="yes">', self.html)
        self.assertIn('<meta name="apple-mobile-web-app-title" content="AI LAB">', self.html)
        self.assertIn('<link rel="manifest" href="/manifest.json">', self.html)
        self.assertIn('<link rel="apple-touch-icon" href="/static/ai-lab-orb.jpg">', self.html)

    def test_dynamic_viewport_height(self) -> None:
        """Page shell uses 100dvh for modern mobile browsers."""
        self.assertIn("100dvh", self.html)
        # Check html, body has 100dvh
        self.assertTrue(re.search(r"html,\s*body\s*\{[^}]*height:\s*100dvh", self.html))
        # Check .app has 100dvh
        self.assertTrue(re.search(r"\.app\s*\{[^}]*height:\s*100dvh", self.html))

    def test_composer_dock_safe_area_insets(self) -> None:
        """Composer padding includes safe-area-inset-bottom and side insets."""
        self.assertIn("env(safe-area-inset-bottom", self.html)
        self.assertIn("env(safe-area-inset-left", self.html)
        self.assertIn("env(safe-area-inset-right", self.html)

    def test_mobile_breakpoint_drawer_and_touch_targets(self) -> None:
        """At max-width: 720px, sidebar is an overlay drawer, backdrop is present, and touch targets >= 44px."""
        # Check all 720px media queries combined
        blocks_720 = "\n".join(m.group(0) for m in re.finditer(r"@media\s*\(\s*max-width:\s*720px\s*\)\s*\{[\s\S]*?(?=\n\s*(?:@media|</style>))", self.html))
        self.assertTrue(blocks_720, "@media (max-width: 720px) block must exist in agents.html")

        # Sidebar is fixed overlay on mobile
        self.assertIn("position: fixed", blocks_720)
        self.assertIn("z-index: 200", blocks_720)
        self.assertIn("translateX(-100%)", blocks_720)

        # Sidebar backdrop element exists in markup and styled in CSS
        self.assertIn('id="sidebar-backdrop"', self.html)
        self.assertIn(".sidebar-backdrop", blocks_720)

        # Touch targets >= 44px
        self.assertIn("44px", blocks_720)
        self.assertTrue(re.search(r"#toggle-side,\s*#show-side\s*\{[^}]*min-height:\s*44px", blocks_720))
        self.assertTrue(re.search(r"\.send\s*\{[^}]*min-height:\s*44px", blocks_720))
        self.assertTrue(re.search(r"#approve-action,\s*#deny-action\s*\{[^}]*min-height:\s*44px", blocks_720))

    def test_composer_hint_phone_suppression(self) -> None:
        """Keyboard shortcut 'Press Enter' is wrapped in desktop-hint and hidden under 720px."""
        self.assertIn('<span class="desktop-hint">Press Enter to send · Shift+Enter for newline · </span>', self.html)
        self.assertTrue(re.search(r"#composer-hint\s+\.desktop-hint\s*\{\s*display:\s*none;\s*\}", self.html))

    def test_desktop_sidebar_retains_standard_column(self) -> None:
        """Above 720px, the sidebar is a 260px column."""
        self.assertTrue(re.search(r"\.sidebar\s*\{[^}]*width:\s*260px", self.html))

    def test_manifest_file_content(self) -> None:
        """The web app manifest is valid JSON naming AI LAB and starting at /."""
        self.assertTrue(self.manifest_path.is_file(), "manifest.json must exist in web/static")
        data = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(data.get("start_url"), "/")
        self.assertEqual(data.get("short_name"), "AI LAB")
        self.assertEqual(data.get("display"), "standalone")
        self.assertTrue(len(data.get("icons", [])) > 0)


@unittest.skipUnless(_HAS_FASTAPI, "fastapi not installed")
class PhoneStudioApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        store = SqliteStore(Path(self.tmp.name) / "wo.sqlite")
        self.app = create_control_app(
            store=store,
            checkpointer=MemorySaver(),
            token="lab-token",
            dispatch=lambda _p: {"ok": True, "detail": "x"},
            model_router=ModelRouter(backends={}),
        )
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_manifest_route_returns_json(self) -> None:
        """GET /manifest.json returns 200 with application/manifest+json media type."""
        resp = self.client.get("/manifest.json")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("application/manifest+json", resp.headers.get("content-type", ""))
        payload = resp.json()
        self.assertEqual(payload.get("short_name"), "AI LAB")
        self.assertEqual(payload.get("start_url"), "/")

    def test_static_manifest_route_returns_json(self) -> None:
        """GET /static/manifest.json is also accessible via the static mount."""
        resp = self.client.get("/static/manifest.json")
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertEqual(payload.get("short_name"), "AI LAB")


if __name__ == "__main__":
    unittest.main()
