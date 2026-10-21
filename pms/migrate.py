"""Builds the database tables by running the numbered SQL files in migrations/.

    python -m pms.migrate            apply any files not yet applied
    python -m pms.migrate --seed     also create the demo users (see pms/seed.py)

Each file runs once, in number order, and is recorded in the schema_migrations table.
If a file that was already applied has since been edited, this stops with an error:
add a new numbered file instead of changing an old one.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

import psycopg

from pms.config import MIGRATIONS_DIR
from pms.dao import database

_LOCK_ID = 727_001  # stops two people migrating the same database at once
_NAME = re.compile(r"^(\d{3,})_[a-z0-9_]+\.sql$")


class MigrationError(Exception):
    """A migration file is badly named, duplicated, or was changed after it ran."""


def discover(directory: Path = MIGRATIONS_DIR) -> list[tuple[int, Path]]:
    """All migration files as (number, path), in the order they must run."""
    found: dict[int, Path] = {}
    for path in sorted(directory.glob("*.sql")):
        match = _NAME.match(path.name)
        if not match:
            raise MigrationError(
                f"'{path.name}' is not a valid migration name. Use 003_short_name.sql (lowercase)."
            )
        number = int(match.group(1))
        if number in found:
            raise MigrationError(
                f"{found[number].name} and {path.name} share the number {number}. "
                "Agree the next free number in the group chat."
            )
        found[number] = path
    return sorted(found.items())


def _checksum(sql: str) -> str:
    # Normalise line endings so Windows and Mac checkouts give the same value.
    return hashlib.sha256(sql.replace("\r\n", "\n").encode("utf-8")).hexdigest()


def apply_pending(
    conn: psycopg.Connection | None = None, directory: Path = MIGRATIONS_DIR
) -> list[str]:
    """Run every migration that has not run yet. Returns the file names it applied."""
    migrations = discover(directory)
    applied_now: list[str] = []
    with database.transaction(conn) as c:
        c.execute("SELECT pg_advisory_xact_lock(%s)", (_LOCK_ID,))
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version    INTEGER     PRIMARY KEY,
                filename   TEXT        NOT NULL,
                checksum   TEXT        NOT NULL,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        done = {
            row["version"]: row
            for row in c.execute("SELECT version, filename, checksum FROM schema_migrations")
        }
        for number, path in migrations:
            sql = path.read_text(encoding="utf-8")
            checksum = _checksum(sql)
            if number in done:
                if done[number]["checksum"] != checksum:
                    raise MigrationError(
                        f"{path.name} was already applied but has been edited since. "
                        "Put your change in a new numbered migration instead."
                    )
                continue
            c.execute(sql)
            c.execute(
                "INSERT INTO schema_migrations (version, filename, checksum) VALUES (%s, %s, %s)",
                (number, path.name, checksum),
            )
            applied_now.append(path.name)
    return applied_now


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Apply database migrations.")
    parser.add_argument("--seed", action="store_true", help="also create the demo users")
    args = parser.parse_args(argv)

    problem = database.check_connection()
    if problem:
        print(f"Cannot reach the database: {problem}")
        print("Is it running? Start it with: docker compose up -d")
        return 1
    try:
        applied = apply_pending()
    except MigrationError as exc:
        print(f"Migration problem: {exc}")
        return 1
    print("Applied: " + ", ".join(applied) if applied else "Database is already up to date.")

    if args.seed:
        from pms import seed

        created = seed.seed_demo_users()
        print("Demo users created: " + ", ".join(created) if created else "Demo users already exist.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
