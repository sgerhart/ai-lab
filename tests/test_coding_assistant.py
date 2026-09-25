"""Read-only coding assistant tools (IWO-056)."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.policy import load_policy
from ai_lab_platform.tool_runtime import execute_allowed_tool
from ai_lab_platform.tools import PathEscape, ToolContext, repo_read, repo_search


def _git_fixture() -> Path:
    root = Path(tempfile.mkdtemp())
    (root / "calc.py").write_text("def add(a, b):\n    return a - b\n", encoding="utf-8")
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "add", "calc.py"], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "-c", "user.email=test@example.com", "-c", "user.name=test", "commit", "-m", "init"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    (root / "calc.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    return root


class CodingAssistantPolicyTests(unittest.TestCase):
    def test_policy_is_read_only(self) -> None:
        policy = load_policy("coding-assistant")
        self.assertTrue(policy.read_only)
        self.assertEqual(
            policy.allowed_tools,
            ("repo_read", "repo_search", "git_status", "git_diff"),
        )
        self.assertEqual(policy.privileged_tools, ("apply_patch", "git_commit"))

    def test_write_tools_denied(self) -> None:
        root = Path(tempfile.mkdtemp())
        ctx = ToolContext(workspace_root=root, artifact_root=root / "artifacts")
        for name in ("repo_write_bounded", "git_commit", "git_push", "run_tests"):
            result = execute_allowed_tool(
                name,
                {},
                allowed_tools=["repo_read"],
                approved_tools=set(),
                ctx=ctx,
            )
            self.assertTrue(result.denied, name)
            self.assertFalse(result.ok, name)

    def test_path_escape_denied(self) -> None:
        root = Path(tempfile.mkdtemp())
        (root / "ok.txt").write_text("hello", encoding="utf-8")
        ctx = ToolContext(workspace_root=root, artifact_root=root / "artifacts")
        with self.assertRaises(PathEscape):
            repo_read(ctx, path="../secret.txt")
        listed = repo_read(ctx, path="ok.txt")
        self.assertIn("hello", listed)

    def test_search_finds_fixture_bug(self) -> None:
        sample = ROOT / "tests" / "fixtures" / "coding-sample"
        ctx = ToolContext(workspace_root=sample, artifact_root=sample / "artifacts")
        hits = repo_search(ctx, "should add")
        self.assertIn("calc.py", hits)

    def test_git_diff_stays_inside_workspace(self) -> None:
        root = _git_fixture()
        ctx = ToolContext(workspace_root=root, artifact_root=root / "artifacts")
        result = execute_allowed_tool(
            "git_diff",
            {},
            allowed_tools=["git_diff"],
            approved_tools=set(),
            ctx=ctx,
        )
        self.assertTrue(result.ok, result.observation)
        self.assertIn("calc.py", result.observation)
        self.assertIn("+", result.observation)


class IsolatedWriteTests(unittest.TestCase):
    PATCH = """--- a/calc.py
+++ b/calc.py
@@ -1,2 +1,2 @@
 def add(a, b):
-    return a - b
+    return a + b
"""

    def test_patch_refused_on_primary_checkout(self) -> None:
        source = _git_fixture()
        # reset the extra edit so the primary is clean; patch still must not apply there
        subprocess.run(["git", "checkout", "--", "calc.py"], cwd=source, check=True, capture_output=True)
        ctx = ToolContext(workspace_root=source, artifact_root=source / "out")
        result = execute_allowed_tool(
            "apply_patch",
            {"patch": self.PATCH},
            allowed_tools=["apply_patch"],
            approved_tools={"apply_patch"},
            ctx=ctx,
        )
        self.assertFalse(result.ok)
        self.assertIn("isolated", result.observation)
        self.assertIn("return a - b", (source / "calc.py").read_text(encoding="utf-8"))

    def test_patch_and_commit_only_in_worktree_after_approval(self) -> None:
        from ai_lab_platform.workspace_isolation import prepare_worktree

        source = _git_fixture()
        subprocess.run(["git", "checkout", "--", "calc.py"], cwd=source, check=True, capture_output=True)
        dest = Path(tempfile.mkdtemp()) / "wt"
        prepare_worktree(source, dest)
        ctx = ToolContext(workspace_root=dest, artifact_root=dest / "out")
        blocked = execute_allowed_tool(
            "apply_patch",
            {"patch": self.PATCH},
            allowed_tools=["apply_patch"],
            approved_tools=set(),
            ctx=ctx,
        )
        self.assertTrue(blocked.denied)
        applied = execute_allowed_tool(
            "apply_patch",
            {"patch": self.PATCH},
            allowed_tools=["apply_patch"],
            approved_tools={"apply_patch"},
            ctx=ctx,
        )
        self.assertTrue(applied.ok, applied.observation)
        self.assertIn("return a + b", (dest / "calc.py").read_text(encoding="utf-8"))
        self.assertIn("return a - b", (source / "calc.py").read_text(encoding="utf-8"))
        commit = execute_allowed_tool(
            "git_commit",
            {"message": "fix add"},
            allowed_tools=["git_commit"],
            approved_tools={"git_commit"},
            ctx=ctx,
        )
        self.assertTrue(commit.ok, commit.observation)
        pushed = execute_allowed_tool(
            "git_push",
            {},
            allowed_tools=["repo_read"],
            approved_tools=set(),
            ctx=ctx,
        )
        self.assertTrue(pushed.denied)

    def test_create_and_resolve_worktree_id(self) -> None:
        from ai_lab_platform.workspace_isolation import create_isolated_copy, resolve_worktree

        source = _git_fixture()
        subprocess.run(["git", "checkout", "--", "calc.py"], cwd=source, check=True, capture_output=True)
        parent = Path(tempfile.mkdtemp())
        created = create_isolated_copy(source, parent=parent)
        path = resolve_worktree(created["id"], parent=parent)
        self.assertTrue((path / "calc.py").is_file())
        self.assertTrue((path / ".ai-lab-isolated").is_file())
        with self.assertRaises(Exception):
            resolve_worktree("../etc", parent=parent)


if __name__ == "__main__":
    unittest.main()
