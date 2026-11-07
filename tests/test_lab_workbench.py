"""Unit tests for AI Laboratory Workbench catalog and routes (IWO-129)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.lab_workbench import (  # noqa: E402
    PARADIGMS,
    get_concept,
    list_concepts,
    list_paradigms,
    search_concepts,
)

try:
    from fastapi.testclient import TestClient

    from ai_lab_platform.control_app import create_control_app
    from ai_lab_platform.settings import Settings
    from ai_lab_platform.store import SqliteStore
except Exception as exc:  # pragma: no cover
    TestClient = None  # type: ignore[misc, assignment]
    create_control_app = None  # type: ignore[misc, assignment]
    Settings = None  # type: ignore[misc, assignment]
    SqliteStore = None  # type: ignore[misc, assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


class LabWorkbenchCatalogTests(unittest.TestCase):
    def test_paradigms_catalog(self) -> None:
        paradigms = list_paradigms()
        self.assertGreaterEqual(len(paradigms), 6)
        paradigm_ids = {p["id"] for p in paradigms}
        self.assertIn("language", paradigm_ids)
        self.assertIn("vision", paradigm_ids)
        self.assertIn("diffusion", paradigm_ids)
        self.assertIn("rl", paradigm_ids)
        self.assertIn("foundations", paradigm_ids)

    def test_list_concepts_filtering(self) -> None:
        all_concepts = list_concepts()
        self.assertGreaterEqual(len(all_concepts), 6)

        lang_concepts = list_concepts("language")
        self.assertTrue(all(c["paradigm"] == "language" for c in lang_concepts))
        self.assertTrue(any(c["id"] == "self-attention" for c in lang_concepts))

        rl_concepts = list_concepts("rl")
        self.assertTrue(any(c["id"] == "grpo-reasoning" for c in rl_concepts))

    def test_concept_schema_completeness(self) -> None:
        required_fields = [
            "id",
            "title",
            "paradigm",
            "summary",
            "tensor_flow",
            "formula",
            "variables",
            "math_explanation",
            "numerical_example",
            "code_snippet",
            "nexus_citations",
        ]
        for c_summary in list_concepts():
            c = get_concept(c_summary["id"])
            self.assertIsNotNone(c)
            for f in required_fields:
                self.assertIn(f, c)
                self.assertTrue(c[f], f"Field '{f}' in concept '{c['id']}' must not be empty")

    def test_search_concepts(self) -> None:
        hits = search_concepts("attention")
        self.assertTrue(any(h["id"] == "self-attention" for h in hits))

        rope_hits = search_concepts("rotary")
        self.assertTrue(any(h["id"] == "rope" for h in rope_hits))

        unknown = search_concepts("nonexistent_concept_xyz_123")
        self.assertEqual(len(unknown), 0)


@unittest.skipUnless(TestClient is not None, f"fastapi testclient unavailable: {IMPORT_ERROR}")
class LabWorkbenchApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
        self.tmp.close()
        settings = Settings(api_token="lab-token")
        app = create_control_app(
            store=SqliteStore(self.tmp.name),
            token="lab-token",
            settings=settings,
        )
        self.client = TestClient(app)
        self.headers = {"Authorization": "Bearer lab-token"}

    def test_laboratory_page_serves_html(self) -> None:
        res = self.client.get("/laboratory")
        self.assertEqual(res.status_code, 200)
        self.assertIn("ai-lab · Laboratory", res.text)
        self.assertIn("benchTitle", res.text)
        self.assertIn("benchTensorFlow", res.text)
        self.assertIn("benchFormula", res.text)

    def test_catalog_endpoint(self) -> None:
        res = self.client.get("/v1/lab/catalog")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("paradigms", data)
        self.assertIn("concepts", data)
        self.assertGreaterEqual(len(data["concepts"]), 6)

    def test_concept_detail_endpoint(self) -> None:
        res = self.client.get("/v1/lab/concept/self-attention")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["id"], "self-attention")
        self.assertEqual(data["paradigm"], "language")
        self.assertIn("mathrm{Attention}(Q, K, V)", data["formula"])
        self.assertGreater(len(data["nexus_citations"]), 0)

    def test_concept_detail_404(self) -> None:
        res = self.client.get("/v1/lab/concept/nonexistent-model")
        self.assertEqual(res.status_code, 404)
