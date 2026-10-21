"""SQL for the audit_log table. Rows can only be added, never changed or removed."""
from __future__ import annotations

from datetime import datetime
from typing import Any

import psycopg

Row = dict[str, Any]


def insert(
    conn: psycopg.Connection,
    user_id: int | None,
    username: str,
    action: str,
    entity: str | None,
    entity_id: str | None,
    details: str | None,
) -> Row:
    return conn.execute(
        """
        INSERT INTO audit_log (user_id, username, action, entity, entity_id, details)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id, occurred_at, user_id, username, action, entity, entity_id, details
        """,
        (user_id, username, action, entity, entity_id, details),
    ).fetchone()


def _where(
    username: str | None,
    action: str | None,
    since: datetime | None,
    until: datetime | None,
    text: str | None,
) -> tuple[str, list[Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if username:
        clauses.append("username = %s")
        params.append(username)
    if action:
        clauses.append("action = %s")
        params.append(action)
    if since:
        clauses.append("occurred_at >= %s")
        params.append(since)
    if until:
        clauses.append("occurred_at < %s")
        params.append(until)
    if text:
        clauses.append("(details ILIKE %s OR entity_id ILIKE %s OR entity ILIKE %s)")
        like = f"%{text}%"
        params.extend([like, like, like])
    return (" WHERE " + " AND ".join(clauses)) if clauses else "", params


def search(
    conn: psycopg.Connection,
    *,
    username: str | None = None,
    action: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    text: str | None = None,
    limit: int = 200,
    offset: int = 0,
) -> list[Row]:
    where, params = _where(username, action, since, until, text)
    return conn.execute(
        "SELECT id, occurred_at, user_id, username, action, entity, entity_id, details "
        f"FROM audit_log{where} ORDER BY occurred_at DESC, id DESC LIMIT %s OFFSET %s",
        [*params, limit, offset],
    ).fetchall()


def count(
    conn: psycopg.Connection,
    *,
    username: str | None = None,
    action: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    text: str | None = None,
) -> int:
    where, params = _where(username, action, since, until, text)
    return conn.execute(f"SELECT COUNT(*)::int AS n FROM audit_log{where}", params).fetchone()["n"]


def distinct_actions(conn: psycopg.Connection) -> list[str]:
    return [r["action"] for r in conn.execute("SELECT DISTINCT action FROM audit_log ORDER BY action")]


def distinct_usernames(conn: psycopg.Connection) -> list[str]:
    return [r["username"] for r in conn.execute("SELECT DISTINCT username FROM audit_log ORDER BY username")]
