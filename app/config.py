from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    """Application configuration, read from the environment.

    Config lives in the environment, not in code, so the same artefact runs
    in dev, CI and production; only the environment differs.
    """

    database_url: str | None
    version: str
    log_level: str

    @classmethod
    def from_env(cls) -> Config:
        return cls(
            # Empty string counts as unset, so an empty compose variable does
            # not produce a broken connection string.
            database_url=os.environ.get("DATABASE_URL") or None,
            version=os.environ.get("APP_VERSION", "0.0.0-dev"),
            log_level=os.environ.get("LOG_LEVEL", "INFO").upper(),
        )
