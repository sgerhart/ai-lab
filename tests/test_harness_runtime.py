import json
import subprocess
import sys
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.api import App, make_handler, serve
from ai_lab_platform.cli import main as cli_main
from ai_lab_platform.orchestrator import Orchestrator
from ai_lab_platform.policy import constrain_tools, load_policy
from ai_lab_platform.store import SqliteStore
from ai_lab_platform.tools import PathEscape, ToolContext, repo_read
from ai_lab_platform.work_order import Status, WorkOrder
from ai_lab_platform.worker import tick
from http.server import ThreadingHTTPServer


def _store() -> tuple[SqliteStore, str]:
    tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
    tmp.close()
    return SqliteStore(tmp.name), tmp.name


class PolicyTests(unittest.TestCase):
    def test_lab_ops_is_read_only(self) -> None:
        policy = load_policy("lab-operations")
        self.assertTrue(policy.read_only)
        self.assertEqual(constrain_tools(["git_push", "health_read"], policy), ["health_read"])

    def test_path_escape(self) -> None:
        ctx = ToolContext(workspace_root=Path(tempfile.mkdtemp()), artifact_root=Path(tempfile.mkdtemp()), bounded_scope="../")
        with self.assertRaises(PathEscape):
            repo_read(ctx)


class WorkerTests(unittest.TestCase):
    def test_lab_operations_tick(self) -> None:
        store, _ = _store()
        orch = Orchestrator(store)
        policy = load_policy("lab-operations")
        order = WorkOrder.new(
            objective="health snapshot",
            agent="lab-operations",
            allowed_tools=list(policy.allowed_tools),
        )
        orch.submit(order)
        done = tick(orch, workspace_root=ROOT, artifact_root=Path(tempfile.mkdtemp()))
        assert done is not None
        self.assertEqual(done.status, Status.COMPLETED)
        self.assertIn("127.0.0.1:5432", done.final_result or "")

    def test_research_does_not_invent_citations(self) -> None:
        store, _ = _store()
        orch = Orchestrator(store)
        policy = load_policy("research")
        orch.submit(
            WorkOrder.new(objective="summarize X", agent="research", allowed_tools=list(policy.allowed_tools))
        )
        artifacts = Path(tempfile.mkdtemp())
        done = tick(orch, workspace_root=ROOT, artifact_root=artifacts)
        assert done is not None
        self.assertEqual(done.status, Status.COMPLETED)
        self.assertTrue(done.artifacts)
        text = Path(done.artifacts[0]).read_text(encoding="utf-8")
        self.assertIn("citations were not invented", text)

    def test_hydrate_queue_across_processes(self) -> None:
        store, path = _store()
        orch = Orchestrator(store)
        policy = load_policy("lab-operations")
        submitted = orch.submit(
            WorkOrder.new(objective="later", agent="lab-operations", allowed_tools=list(policy.allowed_tools))
        )
        orch2 = Orchestrator(SqliteStore(path))
        self.assertIsNone(orch2.start_next())
        self.assertEqual(orch2.hydrate_queue(), 1)
        started = orch2.start_next()
        assert started is not None
        self.assertEqual(started.id, submitted.id)

    def test_development_git_status(self) -> None:
        git_root = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init"], cwd=git_root, check=True, capture_output=True)
        (git_root / "README").write_text("x\n", encoding="utf-8")
        store, _ = _store()
        orch = Orchestrator(store)
        policy = load_policy("development")
        orch.submit(
            WorkOrder.new(objective="status", agent="development", allowed_tools=list(policy.allowed_tools))
        )
        done = tick(orch, workspace_root=git_root, artifact_root=Path(tempfile.mkdtemp()))
        assert done is not None
        self.assertEqual(done.status, Status.COMPLETED)
        self.assertIn("README", done.final_result or "")


class ApiTests(unittest.TestCase):
    def test_health_submit_tick_loopback(self) -> None:
        store, path = _store()
        orch = Orchestrator(store)
        app = App(orch, workspace_root=ROOT, artifact_root=Path(tempfile.mkdtemp()), token="secret")
        httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(app))
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        host, port = httpd.server_address[0], httpd.server_address[1]
        try:
            conn = HTTPConnection(host, port, timeout=2)
            conn.request("GET", "/health")
            self.assertEqual(conn.getresponse().status, 401)
            conn.close()
            conn = HTTPConnection(host, port, timeout=2)
            conn.request("GET", "/health", headers={"Authorization": "Bearer secret"})
            resp = conn.getresponse()
            self.assertEqual(resp.status, 200)
            self.assertFalse(json.loads(resp.read())["deployed"])
            conn.close()
            conn = HTTPConnection(host, port, timeout=2)
            payload = json.dumps({"agent": "lab-operations", "objective": "api health"}).encode()
            conn.request(
                "POST",
                "/work-orders",
                body=payload,
                headers={"Authorization": "Bearer secret", "Content-Type": "application/json"},
            )
            created = json.loads(conn.getresponse().read())
            self.assertEqual(created["status"], "queued")
            conn.close()
            conn = HTTPConnection(host, port, timeout=2)
            conn.request(
                "POST",
                "/worker/tick",
                body=b"{}",
                headers={"Authorization": "Bearer secret", "Content-Type": "application/json"},
            )
            ticked = json.loads(conn.getresponse().read())
            self.assertEqual(ticked["order"]["status"], "completed")
            conn.close()
        finally:
            httpd.shutdown()
            httpd.server_close()

    def test_serve_rejects_non_loopback(self) -> None:
        store, path = _store()
        with self.assertRaises(ValueError):
            serve(Path(path), host="0.0.0.0", port=0)


class CliTests(unittest.TestCase):
    def test_submit_and_list(self) -> None:
        db = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False).name
        code = cli_main(["--db", db, "submit", "--agent", "lab-operations", "--objective", "cli"])
        self.assertEqual(code, 0)
        code = cli_main(["--db", db, "list"])
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
