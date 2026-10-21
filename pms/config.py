"""Settings, read from the environment or from a local .env file (never committed)."""
from __future__ import annotations

import os
from dataclasses import dataclass, replace
from pathlib import Path

from dotenv import load_dotenv
from psycopg.conninfo import make_conninfo

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS_DIR = PROJECT_ROOT / "migrations"


@dataclass(frozen=True)
class DbSettings:
    host: str
    port: int
    name: str
    user: str
    password: str

    def conninfo(self, dbname: str | None = None) -> str:
        return make_conninfo(
            host=self.host,
            port=self.port,
            dbname=dbname or self.name,
            user=self.user,
            password=self.password or None,
        )


def load_settings() -> DbSettings:
    """Database settings from .env (if present) and environment variables."""
    load_dotenv(PROJECT_ROOT / ".env")
    return DbSettings(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        name=os.getenv("DB_NAME", "pms"),
        user=os.getenv("DB_USER", "pms"),
        password=os.getenv("DB_PASSWORD", ""),
    )


def settings_for_tests() -> DbSettings:
    """Same server, but a separate database so tests never touch real data."""
    return replace(load_settings(), name=os.getenv("DB_TEST_NAME", "pms_test"))
