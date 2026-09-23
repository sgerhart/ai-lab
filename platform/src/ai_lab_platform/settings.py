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
    api_token: str = ""
    auth_mode: str = "token"
    bind_address: str = "127.0.0.1"
    api_port: int = 8088

    @classmethod
    def from_env(cls) -> Settings:
        home = os.path.expanduser("~")
        default_token_file = os.path.join(home, ".ai-lab", "studio-jupyter.token")
        return cls(
            database_url=os.environ.get("DATABASE_URL", "").strip(),
            studio_worker_url=os.environ.get("STUDIO_WORKER_URL", "http://127.0.0.1:8090").strip(),
            studio_jupyter_url=os.environ.get("STUDIO_JUPYTER_URL", "").strip(),
            studio_ollama_url=os.environ.get("STUDIO_OLLAMA_URL", "").strip(),
            studio_jupyter_token_file=os.environ.get(
                "STUDIO_JUPYTER_TOKEN_FILE", default_token_file
            ).strip(),
            api_token=os.environ.get("AI_LAB_API_TOKEN", "").strip(),
            auth_mode=os.environ.get("AI_LAB_AUTH_MODE", "token").strip().lower() or "token",
            bind_address=os.environ.get("AI_LAB_BIND_ADDRESS", "127.0.0.1").strip(),
            api_port=int(os.environ.get("AI_LAB_API_PORT", "8088")),
        )
