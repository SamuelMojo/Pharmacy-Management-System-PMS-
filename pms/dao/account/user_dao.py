"""SQL for the users table. No business rules here: see pms/service/account."""
from __future__ import annotations

from typing import Any

import psycopg

Row = dict[str, Any]

_PUBLIC = "id, username, full_name, role, is_active"


def insert(conn: psycopg.Connection, username: str, full_name: str, password_hash: str, role: str) -> Row:
    return conn.execute(
        f"""
        INSERT INTO users (username, full_name, password_hash, role)
        VALUES (%s, %s, %s, %s)
        RETURNING {_PUBLIC}
        """,
        (username, full_name, password_hash, role),
    ).fetchone()


def get_by_id(conn: psycopg.Connection, user_id: int) -> Row | None:
    return conn.execute(f"SELECT {_PUBLIC} FROM users WHERE id = %s", (user_id,)).fetchone()


def get_login_row(conn: psycopg.Connection, username: str) -> Row | None:
    """The row used to check a login, including the password hash and lock state."""
    return conn.execute(
        f"SELECT {_PUBLIC}, password_hash, failed_attempts, locked_until FROM users WHERE username = %s",
        (username,),
    ).fetchone()


def get_login_row_by_id(conn: psycopg.Connection, user_id: int) -> Row | None:
    return conn.execute(
        f"SELECT {_PUBLIC}, password_hash, failed_attempts, locked_until FROM users WHERE id = %s",
        (user_id,),
    ).fetchone()


def list_all(conn: psycopg.Connection) -> list[Row]:
    return conn.execute(f"SELECT {_PUBLIC} FROM users ORDER BY username").fetchall()


def count(conn: psycopg.Connection) -> int:
    return conn.execute("SELECT COUNT(*)::int AS n FROM users").fetchone()["n"]


def update_profile(conn: psycopg.Connection, user_id: int, full_name: str, role: str) -> Row | None:
    return conn.execute(
        f"UPDATE users SET full_name = %s, role = %s WHERE id = %s RETURNING {_PUBLIC}",
        (full_name, role, user_id),
    ).fetchone()


def set_active(conn: psycopg.Connection, user_id: int, active: bool) -> Row | None:
    return conn.execute(
        f"UPDATE users SET is_active = %s WHERE id = %s RETURNING {_PUBLIC}",
        (active, user_id),
    ).fetchone()


def set_password_hash(conn: psycopg.Connection, user_id: int, password_hash: str) -> None:
    """Store a new password and clear any failed-attempt count and lock."""
    conn.execute(
        "UPDATE users SET password_hash = %s, failed_attempts = 0, locked_until = NULL WHERE id = %s",
        (password_hash, user_id),
    )


def record_failed_attempt(conn: psycopg.Connection, user_id: int, max_attempts: int, lock_minutes: int) -> Row:
    """Count a wrong password; lock the account once max_attempts is reached."""
    return conn.execute(
        """
        UPDATE users
        SET failed_attempts = failed_attempts + 1,
            locked_until = CASE WHEN failed_attempts + 1 >= %s
                                THEN now() + make_interval(mins => %s)
                                ELSE locked_until END
        WHERE id = %s
        RETURNING failed_attempts, locked_until
        """,
        (max_attempts, lock_minutes, user_id),
    ).fetchone()


def reset_failed_attempts(conn: psycopg.Connection, user_id: int) -> None:
    conn.execute(
        "UPDATE users SET failed_attempts = 0, locked_until = NULL WHERE id = %s", (user_id,)
    )
