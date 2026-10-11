"""Personal files folder: read notes, refuse paths outside the folder."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.agent_loop import run_until_idle  # noqa: E402
from ai_lab_platform.conversation import AgentRun, AgentRunStatus, BillingClass  # noqa: E402
from ai_lab_platform.model_router import ModelRouter, ScriptedToolBackend  # noqa: E402
from ai_lab_platform.operator_files import DocumentLibrary, FilesError  # noqa: E402
from ai_lab_platform.store import SqliteStore  # noqa: E402
from ai_lab_platform.tool_runtime import execute_allowed_tool  # noqa: E402
from ai_lab_platform.tools import ToolContext  # noqa: E402


def _library() -> DocumentLibrary:
    return DocumentLibrary(Path(tempfile.mkdtemp()))


class OperatorFilesTests(unittest.TestCase):
    def test_grep_finds_a_note_and_a_missing_phrase_does_not(self) -> None:
        library = _library()
        (library.root / "packing.txt").write_text("Pack the blue suitcase.\n", encoding="utf-8")
        found = library.grep("suitcase")
        self.assertIn("packing.txt", found)
        self.assertIn("hits=1", found)
        missed = library.grep("passport photo")
        self.assertIn("hits=0", missed)

    def test_read_rejects_parent_segments(self) -> None:
        library = _library()
        with self.assertRaises(FilesError):
            library.read("../../etc/passwd")
        with self.assertRaises(FilesError):
            library.read("/etc/passwd")

    def test_symlink_outside_the_folder_is_skipped(self) -> None:
        library = _library()
        outside = Path(tempfile.mkdtemp()) / "secret.txt"
        outside.write_text("token material stays outside", encoding="utf-8")
        link = library.root / "leak.txt"
        link.symlink_to(outside)
        self.assertNotIn("leak.txt", library.list_files())
        with self.assertRaises(FilesError):
            library.read("leak.txt")

    def test_does_not_read_the_memory_vault(self) -> None:
        library = _library()
        (library.root / "note.md").write_text("only the files folder\n", encoding="utf-8")
        vault = Path(tempfile.mkdtemp())
        (vault / "secret.md").write_text("vault only\n", encoding="utf-8")
        self.assertNotIn("vault only", library.grep("vault"))
        self.assertIn("only the files folder", library.grep("files folder"))

    def test_personal_run_greps_then_reads(self) -> None:
        library = _library()
        (library.root / "packing.txt").write_text("Pack the blue suitcase.\n", encoding="utf-8")
        store_path = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
        store_path.close()
        store = SqliteStore(store_path.name)
        scripted = ScriptedToolBackend(
            [
                {"type": "tool", "name": "files_grep", "args": {"query": "suitcase"}},
                {"type": "tool", "name": "files_read", "args": {"path": "packing.txt"}},
                {"type": "final", "text": "Pack the blue suitcase."},
            ]
        )
        router = ModelRouter(backends={"scripted": scripted}, default_backend="scripted")
        run = AgentRun.new(
            agent="personal",
            objective="What should I pack?",
            backend="scripted",
            billing_class=BillingClass.LOCAL,
        )
        run.budget.max_steps = 10
        store.put_agent_run(run)
        ctx = ToolContext(
            workspace_root=ROOT,
            artifact_root=ROOT / "artifacts",
            vault_root=Path(tempfile.mkdtemp()),
            files_root=library.root,
        )
        done = run_until_idle(run, router=router, store_put=store.put_agent_run, ctx=ctx)
        self.assertEqual(done.status, AgentRunStatus.COMPLETED, done.final_result)
        tools = [trace.get("tool") for trace in done.traces if trace.get("kind") == "tool_result"]
        self.assertEqual(tools, ["files_grep", "files_read"])
        self.assertIn("blue suitcase", done.final_result or "")

    def test_tool_path_escape_is_an_observation(self) -> None:
        library = _library()
        ctx = ToolContext(
            workspace_root=ROOT,
            artifact_root=ROOT / "artifacts",
            files_root=library.root,
        )
        result = execute_allowed_tool(
            "files_read",
            {"path": "../../etc/passwd"},
            allowed_tools=["files_read"],
            approved_tools=set(),
            ctx=ctx,
        )
        self.assertFalse(result.ok)
        self.assertIn("escapes", result.observation)


if __name__ == "__main__":
    unittest.main()
