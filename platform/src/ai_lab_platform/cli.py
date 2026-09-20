"""Local harness CLI. Does not deploy anything."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .orchestrator import Orchestrator
from .policy import load_policy
from .store import SqliteStore
from .work_order import Status, WorkOrder
from .worker import tick

ROOT = Path(__file__).resolve().parents[3]


def _orch(db: Path) -> Orchestrator:
    orch = Orchestrator(SqliteStore(db))
    orch.hydrate_queue()
    return orch


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ai-lab-platform")
    parser.add_argument("--db", default=str(Path.home() / ".ai-lab" / "harness.sqlite"))
    parser.add_argument("--workspace", default=str(ROOT))
    parser.add_argument("--artifacts", default="")
    sub = parser.add_subparsers(dest="cmd", required=True)

    submit = sub.add_parser("submit")
    submit.add_argument("--agent", required=True)
    submit.add_argument("--objective", required=True)
    submit.add_argument("--scope", default="")

    sub.add_parser("list")
    getp = sub.add_parser("get")
    getp.add_argument("id")
    appr = sub.add_parser("approve")
    appr.add_argument("id")
    appr.add_argument("--tools", default="")
    can = sub.add_parser("cancel")
    can.add_argument("id")
    sub.add_parser("tick")
    serve = sub.add_parser("serve")
    serve.add_argument("--port", type=int, default=8088)

    args = parser.parse_args(argv)
    db = Path(args.db)
    db.parent.mkdir(parents=True, exist_ok=True)
    workspace = Path(args.workspace)
    artifacts = Path(args.artifacts) if args.artifacts else db.parent / "artifacts"

    if args.cmd == "serve":
        from .api import serve as serve_api

        httpd = serve_api(db, port=args.port, workspace_root=workspace, artifact_root=artifacts)
        print(f"listening on http://127.0.0.1:{httpd.server_address[1]} (loopback only)", flush=True)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            return 0
        return 0

    orch = _orch(db)
    if args.cmd == "submit":
        policy = load_policy(args.agent)
        order = WorkOrder.new(
            objective=args.objective,
            agent=args.agent,
            allowed_tools=list(policy.allowed_tools),
            bounded_scope=args.scope,
        )
        order = orch.submit(order)
        print(json.dumps(order.to_dict(), indent=2))
        return 0
    if args.cmd == "list":
        print(json.dumps([o.to_dict() for o in orch.store.list()], indent=2))
        return 0
    if args.cmd == "get":
        order = orch.store.get(args.id)
        if order is None:
            print("not found", file=sys.stderr)
            return 1
        print(json.dumps(order.to_dict(), indent=2))
        return 0
    if args.cmd == "approve":
        tools = [t for t in args.tools.split(",") if t]
        print(json.dumps(orch.approve(args.id, tools).to_dict(), indent=2))
        return 0
    if args.cmd == "cancel":
        print(json.dumps(orch.cancel(args.id).to_dict(), indent=2))
        return 0
    if args.cmd == "tick":
        result = tick(orch, workspace_root=workspace, artifact_root=artifacts)
        if result is None:
            print("{}", flush=True)
            return 0
        print(json.dumps(result.to_dict(), indent=2))
        return 0 if result.status != Status.FAILED else 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
