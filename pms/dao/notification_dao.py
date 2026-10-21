"""SQL for notifications. A notification is visible to a user if it is addressed to them
directly or to their role. Read state is stored per user in notification_reads."""
from __future__ import annotations

from typing import Any

import psycopg

Row = dict[str, Any]

_VISIBLE = "(n.recipient_user_id = %(uid)s OR n.recipient_role = %(role)s)"


def insert(
    conn: psycopg.Connection,
    title: str,
    message: str,
    recipient_user_id: int | None,
    recipient_role: str | None,
    entity: str | None,
    entity_id: str | None,
) -> Row:
    return conn.execute(
        """
        INSERT INTO notifications
            (title, message, recipient_user_id, recipient_role, entity, entity_id)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id, created_at, title, message, recipient_user_id, recipient_role, entity, entity_id
        """,
        (title, message, recipient_user_id, recipient_role, entity, entity_id),
    ).fetchone()


def list_for_user(
    conn: psycopg.Connection, user_id: int, role: str, *, unread_only: bool = False, limit: int = 100
) -> list[Row]:
    unread = "AND r.user_id IS NULL" if unread_only else ""
    return conn.execute(
        f"""
        SELECT n.id, n.created_at, n.title, n.message, n.entity, n.entity_id,
               (r.user_id IS NOT NULL) AS is_read
        FROM notifications n
        LEFT JOIN notification_reads r
               ON r.notification_id = n.id AND r.user_id = %(uid)s
        WHERE {_VISIBLE} {unread}
        ORDER BY n.created_at DESC, n.id DESC
        LIMIT %(limit)s
        """,
        {"uid": user_id, "role": role, "limit": limit},
    ).fetchall()


def unread_count(conn: psycopg.Connection, user_id: int, role: str) -> int:
    return conn.execute(
        f"""
        SELECT COUNT(*)::int AS n
        FROM notifications n
        LEFT JOIN notification_reads r
               ON r.notification_id = n.id AND r.user_id = %(uid)s
        WHERE {_VISIBLE} AND r.user_id IS NULL
        """,
        {"uid": user_id, "role": role},
    ).fetchone()["n"]


def mark_read(conn: psycopg.Connection, notification_id: int, user_id: int, role: str) -> None:
    """Mark one notification read, but only if this user is allowed to see it."""
    conn.execute(
        f"""
        INSERT INTO notification_reads (notification_id, user_id)
        SELECT n.id, %(uid)s FROM notifications n
        WHERE n.id = %(nid)s AND {_VISIBLE}
        ON CONFLICT DO NOTHING
        """,
        {"uid": user_id, "role": role, "nid": notification_id},
    )


def mark_all_read(conn: psycopg.Connection, user_id: int, role: str) -> None:
    conn.execute(
        f"""
        INSERT INTO notification_reads (notification_id, user_id)
        SELECT n.id, %(uid)s FROM notifications n
        WHERE {_VISIBLE}
        ON CONFLICT DO NOTHING
        """,
        {"uid": user_id, "role": role},
    )
