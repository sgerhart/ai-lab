"""Process settings. No secrets in defaults."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str = ""
    studio_worker_url: str = "http://127.0.0.1:8090"
    studio_jupyter_url: str = ""
    studio_ollama_url: str = ""
    studio_jupyter_token_file: str = ""
    antares_job_url: str = ""
    antares_completions_url: str = ""
    api_token: str = ""
    auth_mode: str = "token"
    bind_address: str = "127.0.0.1"
    api_port: int = 8088
    agent_worker: bool = False
    agent_worker_interval_sec: float = 2.0

    @classmethod
    def from_env(cls) -> Settings:
        home = os.path.expanduser("~")
        default_token_file = os.path.join(home, ".ai-lab", "studio-jupyter.token")
        database_url = os.environ.get("DATABASE_URL", "").strip()
        worker_raw = os.environ.get("AI_LAB_AGENT_WORKER", "").strip().lower()
        if worker_raw in {"1", "true", "yes", "on"}:
            agent_worker = True
        elif worker_raw in {"0", "false", "no", "off"}:
            agent_worker = False
        else:
            # Default on when the mini control plane has Postgres (always-on SoT).
            agent_worker = bool(database_url)
        return cls(
            database_url=database_url,
            studio_worker_url=os.environ.get("STUDIO_WORKER_URL", "http://127.0.0.1:8090").strip(),
            studio_jupyter_url=os.environ.get("STUDIO_JUPYTER_URL", "").strip(),
            studio_ollama_url=os.environ.get("STUDIO_OLLAMA_URL", "").strip(),
            studio_jupyter_token_file=os.environ.get(
                "STUDIO_JUPYTER_TOKEN_FILE", default_token_file
            ).strip(),
            antares_job_url=os.environ.get("ANTARES_JOB_URL", "").strip(),
            antares_completions_url=os.environ.get("ANTARES_COMPLETIONS_URL", "").strip(),
            api_token=os.environ.get("AI_LAB_API_TOKEN", "").strip(),
            auth_mode=os.environ.get("AI_LAB_AUTH_MODE", "token").strip().lower() or "token",
            bind_address=os.environ.get("AI_LAB_BIND_ADDRESS", "127.0.0.1").strip(),
            api_port=int(os.environ.get("AI_LAB_API_PORT", "8088")),
            agent_worker=agent_worker,
            agent_worker_interval_sec=float(
                os.environ.get("AI_LAB_AGENT_WORKER_INTERVAL_SEC", "2") or "2"
            ),
        )
