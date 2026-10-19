"""Classroom lesson plans, board marks, and the Classroom page."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.classroom import (  # noqa: E402
    BOARD_OPS,
    answer_question,
    fallback_lesson,
    generate_lesson,
    list_posts,
    load_post,
    load_post_image,
    parse_answer,
    parse_lesson,
    save_post,
)
from ai_lab_platform.conversation import BillingClass  # noqa: E402
from ai_lab_platform.model_router import CompletionRequest, CompletionResponse, FakeBackend, ModelRouter  # noqa: E402

try:
    from fastapi.testclient import TestClient
    from langgraph.checkpoint.memory import MemorySaver

    from ai_lab_platform.control_app import create_control_app
    from ai_lab_platform.settings import Settings
    from ai_lab_platform.store import SqliteStore
except Exception as exc:  # pragma: no cover
    TestClient = None  # type: ignore[misc, assignment]
    MemorySaver = None  # type: ignore[misc, assignment]
    create_control_app = None  # type: ignore[misc, assignment]
    Settings = None  # type: ignore[misc, assignment]
    SqliteStore = None  # type: ignore[misc, assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


LESSON_JSON = {
    "title": "Photosynthesis",
    "objectives": ["Name the inputs", "<b>Name the outputs</b>"],
    "segments": [
        {
            "title": "Opening",
            "speech": "Today we learn how a leaf stores light. Raise your hand with questions.",
            "board": [
                {"op": "title", "text": "<img src=x onerror=alert(1)>Light"},
                {"op": "script", "text": "alert(1)"},
                {"op": "box", "x": 4, "y": -1, "w": 0.4, "h": 0.2, "text": "Leaf"},
            ],
        }
    ],
}


class _LessonBackend:
    def __init__(self) -> None:
        self.requests: list[CompletionRequest] = []

    def complete(self, request: CompletionRequest) -> CompletionResponse:
        self.requests.append(request)
        if "Student question" in request.prompt:
            text = json.dumps(
                {
                    "speech": "The leaf uses light, water, and carbon dioxide.",
                    "board": [{"op": "label", "text": "light + water", "x": 2, "y": 0.4}],
                }
            )
        else:
            text = "<think>plan</think>\n```json\n" + json.dumps(LESSON_JSON) + "\n```"
        return CompletionResponse(
            model=request.model,
            backend=request.backend,
            text=text,
            billing_class=BillingClass.LOCAL,
        )

    def health(self) -> dict[str, object]:
        return {"ok": True, "enabled": True, "models": ["llama3.2:3b"], "billing_class": "local"}


def _text_from(backend: _LessonBackend):
    def complete(prompt: str) -> str:
        request = CompletionRequest(model="llama3.2:3b", prompt=prompt, backend="ollama")
        return backend.complete(request).text

    return complete


class LessonPlanTests(unittest.TestCase):
    def test_topic_is_required(self) -> None:
        with self.assertRaises(ValueError):
            generate_lesson("   ")

    def test_markup_in_the_topic_is_plain_text(self) -> None:
        lesson = generate_lesson("<b>Tide pools</b>")
        self.assertEqual(lesson["topic"], "Tide pools")
        self.assertNotIn("<", lesson["title"])

    def test_scaffold_is_a_full_class(self) -> None:
        lesson = fallback_lesson("photosynthesis")
        self.assertEqual(lesson["source"], "scaffold")
        self.assertGreaterEqual(len(lesson["segments"]), 5)
        self.assertGreaterEqual(len(lesson["objectives"]), 3)
        ids = [segment["id"] for segment in lesson["segments"]]
        self.assertEqual(ids, [f"s{i}" for i in range(1, len(ids) + 1)])
        for segment in lesson["segments"]:
            self.assertTrue(segment["speech"])
            self.assertLessEqual(len(segment["speech"]), 520)
            self.assertTrue(segment["board"])
            for op in segment["board"]:
                self.assertIn(op["op"], BOARD_OPS)

    def test_unusable_model_text_uses_the_outline(self) -> None:
        lesson = parse_lesson("gravity", "[fake] not a lesson")
        self.assertEqual(lesson["source"], "scaffold")
        self.assertEqual(lesson["topic"], "gravity")

    def test_model_lesson_keeps_only_board_marks(self) -> None:
        lesson = generate_lesson("photosynthesis", _text_from(_LessonBackend()))
        self.assertEqual(lesson["source"], "model")
        self.assertEqual(lesson["title"], "Photosynthesis")
        self.assertEqual(lesson["objectives"][1], "Name the outputs")
        board = lesson["segments"][0]["board"]
        kinds = [op["op"] for op in board]
        self.assertNotIn("script", kinds)
        self.assertNotIn("box", kinds)
        self.assertEqual(board[0]["text"], "Light")
        figure = next(op for op in board if op["op"] == "figure")
        self.assertIn("Leaf", figure["labels"])
        self.assertNotIn("x", figure)
        self.assertIn(figure["kind"], {"layers", "flow", "list"})

    def test_extra_segments_are_capped(self) -> None:
        segments = [
            {"title": f"Part {i}", "speech": f"Point {i}.", "board": [{"op": "bullet", "text": str(i)}]}
            for i in range(12)
        ]
        lesson = parse_lesson("limits", json.dumps({"title": "Limits", "segments": segments}))
        self.assertEqual(len(lesson["segments"]), 8)

    def test_answer_uses_the_model_and_clamps_the_mark(self) -> None:
        backend = _LessonBackend()
        answer = answer_question(
            topic="photosynthesis",
            question="What does the leaf use?",
            segment_title="Definition",
            recent_speech="A leaf stores light.",
            complete=_text_from(backend),
        )
        self.assertEqual(answer["source"], "model")
        self.assertIn("light", answer["speech"])
        marks = json.dumps(answer["board"])
        self.assertIn("light + water", marks)
        self.assertNotIn('"x"', marks)
        self.assertIn("Student question", backend.requests[0].prompt)

    def test_label_moves_below_a_drawing(self) -> None:
        lesson = parse_lesson(
            "nets",
            json.dumps(
                {
                    "title": "Nets",
                    "segments": [
                        {
                            "title": "Parts",
                            "speech": "Two ends of a tunnel.",
                            "board": [
                                {"op": "box", "x": 0.2, "y": 0.3, "w": 0.4, "h": 0.25, "text": "VTEP"},
                                {"op": "label", "text": "VNI", "x": 0.3, "y": 0.4},
                            ],
                        }
                    ],
                }
            ),
        )
        board = lesson["segments"][0]["board"]
        self.assertNotIn("label", [op["op"] for op in board])
        self.assertNotIn("box", [op["op"] for op in board])
        figure = next(op for op in board if op["op"] == "figure")
        self.assertEqual(figure["labels"], ["VTEP", "VNI"])
        self.assertEqual(figure["kind"], "flow")
        self.assertNotIn("x", figure)

    def test_unknown_sketch_becomes_a_labeled_figure(self) -> None:
        lesson = parse_lesson(
            "nets",
            json.dumps(
                {
                    "title": "Nets",
                    "segments": [
                        {
                            "title": "Picture",
                            "speech": "A node stands for one machine.",
                            "board": [{"op": "sketch", "kind": "script", "text": "Host", "x": 0.2, "y": 0.3}],
                        }
                    ],
                }
            ),
        )
        figure = lesson["segments"][0]["board"][0]
        self.assertEqual(figure["op"], "figure")
        self.assertIn("Host", figure["labels"])
        self.assertNotIn(figure["kind"], {"node", "server", "sketch"})

    def test_review_questions_become_a_list(self) -> None:
        lesson = parse_lesson(
            "vxlan",
            json.dumps(
                {
                    "title": "VXLAN",
                    "segments": [
                        {
                            "title": "Review",
                            "speech": "Where is the VNI stored?",
                            "board": [
                                {"op": "title", "text": "Review"},
                                {"op": "sketch", "kind": "server", "text": "I"},
                                {"op": "write", "text": "Q: Where is the VNI stored?"},
                                {"op": "write", "text": "A: VXLAN Header (UDP)"},
                                {"op": "write", "text": "Q: Default UDP Port?"},
                            ],
                        }
                    ],
                }
            ),
        )
        board = lesson["segments"][0]["board"]
        self.assertEqual([op["op"] for op in board], ["title", "figure"])
        figure = board[1]
        self.assertEqual(figure["kind"], "list")
        self.assertEqual(figure["labels"][0], "Q: Where is the VNI stored?")
        self.assertNotIn("server", json.dumps(board))

    def test_packet_figure_keeps_its_key(self) -> None:
        lesson = parse_lesson(
            "vxlan",
            json.dumps(
                {
                    "title": "VXLAN",
                    "segments": [
                        {
                            "title": "Header",
                            "speech": "The VNI rides in the VXLAN header.",
                            "board": [
                                {"op": "title", "text": "Header"},
                                {
                                    "op": "figure",
                                    "kind": "packet",
                                    "labels": ["Outer IP", "UDP 4789", "VNI", "Inner frame"],
                                    "key": "VNI",
                                },
                                {"op": "hand", "text": "The underlay only sees the outer IP."},
                            ],
                        }
                    ],
                }
            ),
        )
        board = lesson["segments"][0]["board"]
        figure = next(op for op in board if op["op"] == "figure")
        self.assertEqual(figure["kind"], "packet")
        self.assertEqual(figure["key"], "VNI")
        self.assertEqual(board[-1]["op"], "hand")

    def test_bad_answer_still_replies(self) -> None:
        answer = answer_question(topic="gravity", question="Why down?", complete=lambda _prompt: "nope")
        self.assertEqual(answer["source"], "scaffold")
        self.assertTrue(answer["speech"])
        self.assertIn(answer["board"][0]["op"], BOARD_OPS)


@unittest.skipIf(IMPORT_ERROR is not None, f"fastapi/langgraph missing: {IMPORT_ERROR}")
class ClassroomApiTests(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
        tmp.close()
        self.backend = _LessonBackend()
        router = ModelRouter(backends={"ollama": self.backend}, default_backend="ollama")
        app = create_control_app(
            store=SqliteStore(tmp.name),
            checkpointer=MemorySaver(),
            token="lab-token",
            settings=Settings(auth_mode="token", agent_worker=False),
            dispatch=lambda _payload: {"ok": True, "detail": "unused"},
            model_router=router,
        )
        self.client = TestClient(app)
        self.headers = {"Authorization": "Bearer lab-token"}

    def test_page_and_sidebar_link(self) -> None:
        page = self.client.get("/classroom")
        self.assertEqual(page.status_code, 200)
        self.assertIn('id="board"', page.text)
        self.assertIn('id="raise-hand"', page.text)
        self.assertIn('id="ask-question"', page.text)
        self.assertIn('id="post-lesson"', page.text)
        self.assertIn('id="pause-instructor"', page.text)
        self.assertIn("/static/classroom.js", page.text)
        script = self.client.get("/static/classroom.js?v=2")
        self.assertEqual(script.status_code, 200)
        self.assertIn("speechSynthesis", script.text)
        self.assertIn("flo", script.text.lower())
        self.assertIn("eddy", script.text.lower())
        self.assertIn("wantsFreshBoard", script.text)
        self.assertIn("vix-lan", script.text)
        self.assertIn("V T E P", script.text)
        agents = (ROOT / "platform" / "src" / "ai_lab_platform" / "web" / "agents.html").read_text()
        self.assertIn('id="nav-classroom"', agents)
        self.assertIn('href="/classroom"', agents)

    def test_lesson_requires_auth_and_stays_on_the_local_model(self) -> None:
        denied = self.client.post("/v1/classroom/lessons", json={"topic": "photosynthesis"})
        self.assertEqual(denied.status_code, 401)
        created = self.client.post(
            "/v1/classroom/lessons",
            headers=self.headers,
            json={"topic": "photosynthesis"},
        )
        self.assertEqual(created.status_code, 200)
        body = created.json()
        self.assertEqual(body["source"], "model")
        self.assertEqual(body["segments"][0]["board"][0]["text"], "Light")
        self.assertEqual(self.backend.requests[0].backend, "ollama")
        self.assertNotIn(self.backend.requests[0].backend, {"openai", "anthropic", "gemini"})

    def test_question_and_blank_topic(self) -> None:
        blank = self.client.post("/v1/classroom/lessons", headers=self.headers, json={"topic": "  "})
        self.assertEqual(blank.status_code, 400)
        answer = self.client.post(
            "/v1/classroom/questions",
            headers=self.headers,
            json={"topic": "photosynthesis", "question": "What does the leaf use?", "segment_title": "Opening"},
        )
        self.assertEqual(answer.status_code, 200)
        self.assertEqual(answer.json()["source"], "model")
        self.assertIn("light", answer.json()["speech"])


@unittest.skipIf(IMPORT_ERROR is not None, f"fastapi/langgraph missing: {IMPORT_ERROR}")
def _tiny_png() -> str:
    import base64
    import struct
    import zlib

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 0, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(b"\x00\xff")) + chunk(b"IEND", b"")
    return base64.b64encode(png).decode("ascii")


class ClassroomPostTests(unittest.TestCase):
    def test_post_round_trip_and_reject_bad_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            saved = save_post(
                topic="Tunnel endpoints",
                title="Building a Simple VXLAN Fabric",
                lesson={
                    "title": "Building a Simple VXLAN Fabric",
                    "segments": [
                        {"title": "The Parts", "speech": "The VTEP is the tunnel endpoint.", "board": [{"op": "sketch", "kind": "switch", "text": "VTEP"}]}
                    ],
                },
                discussion=[{"who": "You", "text": "What is a VTEP?"}, {"who": "Instructor", "text": "It encapsulates the frame."}],
                image_png=_tiny_png(),
                root=root,
            )
            listed = list_posts(root)
            self.assertEqual(listed[0]["id"], saved["id"])
            loaded = load_post(saved["id"], root)
            self.assertEqual(loaded["discussion"][0]["text"], "What is a VTEP?")
            stored = loaded["lesson"]["segments"][0]["board"]
            figure = next(op for op in stored if op["op"] == "figure")
            self.assertIn("VTEP", figure["labels"])
            self.assertNotEqual(figure["kind"], "server")
            self.assertTrue(load_post_image(saved["id"], root).startswith(b"\x89PNG"))
            with self.assertRaises(ValueError):
                load_post("../secret", root)
            with self.assertRaises(ValueError):
                save_post(topic="", title="", root=root)

    def test_a_draw_request_builds_a_fabric(self) -> None:
        answer = parse_answer(
            "VXLAN",
            "Can you draw me a vxlan fabric?",
            json.dumps(
                {
                    "speech": "Absolutely. A VXLAN fabric connects remote segments over an IP network.",
                    "board": [],
                }
            ),
        )
        figure = next(op for op in answer["board"] if op["op"] == "figure")
        self.assertEqual(figure["kind"], "fabric")
        self.assertGreaterEqual(len(figure["spines"]), 1)
        self.assertGreaterEqual(len(figure["leaves"]), 2)
        self.assertTrue(figure["hosts"])
        self.assertEqual(figure["tunnel"], "VXLAN")

    def test_a_clean_slate_redraws_the_fabric(self) -> None:
        answer = parse_answer(
            "VXLAN",
            "can you start with a clean diagram? redraw it?",
            json.dumps(
                {
                    "speech": "Absolutely. Let's clear the slate and draw the fabric.",
                    "board": [],
                }
            ),
        )
        self.assertEqual(answer["board"][0]["op"], "title")
        figure = next(op for op in answer["board"] if op["op"] == "figure")
        self.assertEqual(figure["kind"], "fabric")
        self.assertGreaterEqual(len(figure["spines"]), 1)
        self.assertGreaterEqual(len(figure["leaves"]), 2)

    def test_later_sections_add_onto_the_fabric(self) -> None:
        lesson = parse_lesson(
            "VXLAN: Extending Layer 2",
            json.dumps(
                {
                    "title": "VXLAN",
                    "segments": [
                        {
                            "title": "Opening Plan",
                            "speech": "Here is the plan.",
                            "board": [{"op": "title", "text": "Plan"}, {"op": "figure", "kind": "list", "labels": ["Definition", "Parts"]}],
                        },
                        {
                            "title": "Definition",
                            "speech": "VXLAN extends layer 2.",
                            "board": [{"op": "title", "text": "Definition"}, {"op": "figure", "kind": "list", "labels": ["One"]}],
                        },
                        {
                            "title": "Components",
                            "speech": "Leaves and spines.",
                            "board": [{"op": "title", "text": "Components"}, {"op": "figure", "kind": "list", "labels": ["A", "B"]}],
                        },
                        {
                            "title": "Check for Understanding",
                            "speech": "Your turn.",
                            "board": [{"op": "title", "text": "Check"}, {"op": "figure", "kind": "list", "labels": ["Ask"]}],
                        },
                    ],
                }
            ),
        )
        segments = lesson["segments"]
        self.assertEqual(segments[0]["place"], "page")
        self.assertEqual(segments[1]["place"], "page")
        fabric = next(op for op in segments[1]["board"] if op["op"] == "figure")
        self.assertEqual(fabric["kind"], "fabric")
        self.assertEqual(segments[2]["place"], "add")
        self.assertNotIn("figure", [op["op"] for op in segments[2]["board"]])
        self.assertIn("emphasis", [op["op"] for op in segments[2]["board"]])
        self.assertEqual(segments[3]["place"], "add")


class ClassroomOutlineApiTests(unittest.TestCase):
    def test_echo_backend_still_starts_class(self) -> None:
        tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
        tmp.close()
        router = ModelRouter(
            backends={"ollama": FakeBackend(), "fake": FakeBackend()},
            default_backend="fake",
        )
        app = create_control_app(
            store=SqliteStore(tmp.name),
            checkpointer=MemorySaver(),
            token="lab-token",
            settings=Settings(auth_mode="token", agent_worker=False),
            dispatch=lambda _payload: {"ok": True, "detail": "unused"},
            model_router=router,
        )
        client = TestClient(app)
        created = client.post(
            "/v1/classroom/lessons",
            headers={"Authorization": "Bearer lab-token"},
            json={"topic": "gravity"},
        )
        self.assertEqual(created.status_code, 200)
        body = created.json()
        self.assertEqual(body["source"], "scaffold")
        self.assertGreaterEqual(len(body["segments"]), 5)


if __name__ == "__main__":
    unittest.main()
