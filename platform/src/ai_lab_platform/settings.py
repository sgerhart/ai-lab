"""Process settings. No secrets in defaults."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str = ""
    studio_worker_url: str = "http://127.0.0.1:8090"
    api_token: str = ""
    bind_address: str = "127.0.0.1"
    api_port: int = 8088

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            database_url=os.environ.get("DATABASE_URL", "").strip(),
            studio_worker_url=os.environ.get("STUDIO_WORKER_URL", "http://127.0.0.1:8090").strip(),
            api_token=os.environ.get("AI_LAB_API_TOKEN", "").strip(),
            bind_address=os.environ.get("AI_LAB_BIND_ADDRESS", "127.0.0.1").strip(),
            api_port=int(os.environ.get("AI_LAB_API_PORT", "8088")),
        )
