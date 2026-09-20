"""Load agent policy.json files. Policies constrain work orders; they do not grant extra tools."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AgentPolicy:
    id: str
    allowed_tools: tuple[str, ...]
    privileged_tools: tuple[str, ...]
    read_only: bool
    isolation_tier: int
    network: tuple[str, ...]
    citation_policy: str | None = None


def default_agents_root() -> Path:
    return Path(__file__).resolve().parents[3] / "agents"


def load_policy(agent_id: str, agents_root: Path | None = None) -> AgentPolicy:
    root = agents_root or default_agents_root()
    path = root / agent_id / "policy.json"
    if not path.is_file():
        raise FileNotFoundError(f"unknown agent policy: {agent_id} ({path})")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("id") != agent_id:
        raise ValueError(f"policy id {data.get('id')!r} does not match directory {agent_id}")
    return AgentPolicy(
        id=agent_id,
        allowed_tools=tuple(data.get("allowed_tools") or []),
        privileged_tools=tuple(data.get("privileged_tools") or []),
        read_only=bool(data.get("read_only", False)),
        isolation_tier=int(data.get("isolation_tier", 1)),
        network=tuple(data.get("network") or []),
        citation_policy=data.get("citation_policy"),
    )


def constrain_tools(requested: list[str], policy: AgentPolicy) -> list[str]:
    allowed = set(policy.allowed_tools)
    if policy.read_only:
        return [t for t in requested if t in allowed]
    return [t for t in requested if t in allowed or t in policy.privileged_tools]
