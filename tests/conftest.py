"""Shared test setup.

Tests that touch the database use a separate database called pms_test (never your real
data). It is created and migrated automatically. If PostgreSQL is not running, those tests
are skipped with a message rather than failing: start it with `docker compose up -d`.
"""
from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")  # no real windows during tests

import psycopg
import pytest

from pms import migrate
from pms.config import settings_for_tests
from pms.dao import database
from pms.model.account.user import Role, User
from pms.dao.account import user_dao
from pms.security import passwords

TEST_PASSWORD = "Testing123"


@pytest.fixture(scope="session")
def _test_database():
    settings = settings_for_tests()
    try:
        with psycopg.connect(settings.conninfo("postgres"), autocommit=True, connect_timeout=3) as admin:
            exists = admin.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s", (settings.name,)
            ).fetchone()
            if not exists:
                admin.execute(f'CREATE DATABASE "{settings.name}"')
    except psycopg.Error as exc:
        pytest.skip(f"PostgreSQL is not reachable ({exc}). Run: docker compose up -d", allow_module_level=False)
    database.configure(settings)
    migrate.apply_pending()
    yield settings
    database.configure(None)


@pytest.fixture
def db(_test_database):
    """A clean, migrated test database for one test."""
    with database.connect(autocommit=True) as conn:
        conn.execute(
            "TRUNCATE notification_reads, notifications, audit_log, users RESTART IDENTITY CASCADE"
        )
    return _test_database


@pytest.fixture
def make_user(db):
    """make_user(role=Role.SYSTEM_MANAGER, username="admin") -> User (password is TEST_PASSWORD)."""
    counter = {"n": 0}

    def _make(role: Role = Role.SYSTEM_MANAGER, username: str | None = None, active: bool = True) -> User:
        counter["n"] += 1
        name = username or f"{role.value}{counter['n']}"
        with database.transaction() as conn:
            row = user_dao.insert(
                conn, name, name.title(), passwords.hash_password(TEST_PASSWORD), role.value
            )
            if not active:
                row = user_dao.set_active(conn, row["id"], False)
        return User.from_row(row)

    return _make


@pytest.fixture
def admin(make_user) -> User:
    return make_user(Role.SYSTEM_MANAGER, "admin")
