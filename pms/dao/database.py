"""The one place that opens database connections.

Typical use in a service:

    from pms.dao import database

    with database.transaction() as conn:       # commits at the end, rolls back on error
        medicine_dao.insert(conn, ...)
        audit.log_action(user, "medicine.create", conn=conn)   # same transaction

Pass an existing connection to ``transaction(conn)`` to join the caller's transaction
instead of starting a new one. Rows come back as dictionaries (row["name"]).
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import psycopg
from psycopg.rows import dict_row

from pms.config import DbSettings, load_settings

_settings: DbSettings | None = None


def configure(settings: DbSettings | None) -> None:
    """Use these settings instead of the .env ones (tests do this). None resets."""
    global _settings
    _settings = settings


def current_settings() -> DbSettings:
    return _settings or load_settings()


def connect(settings: DbSettings | None = None, autocommit: bool = False) -> psycopg.Connection:
    chosen = settings or current_settings()
    return psycopg.connect(
        chosen.conninfo(),
        row_factory=dict_row,
        autocommit=autocommit,
        connect_timeout=5,
    )


@contextmanager
def transaction(conn: psycopg.Connection | None = None) -> Iterator[psycopg.Connection]:
    """Yield a connection inside a transaction.

    With no argument: open a connection, commit on success, roll back on any error.
    With ``conn``: join that connection; the code that opened it commits or rolls back.
    """
    if conn is not None:
        yield conn
        return
    own = connect()
    try:
        yield own
        own.commit()
    except BaseException:
        own.rollback()
        raise
    finally:
        own.close()


def check_connection(settings: DbSettings | None = None) -> str | None:
    """Return None if the database answers, otherwise a short reason."""
    try:
        with connect(settings) as conn:
            conn.execute("SELECT 1")
        return None
    except psycopg.Error as exc:
        return str(exc).strip() or exc.__class__.__name__
