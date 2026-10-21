"""Managing user accounts (system manager only)."""
from __future__ import annotations

import re

from pms.dao import database
from pms.dao.account import user_dao
from pms.errors import ConflictError, NotFoundError, ValidationError
from pms.model.account.user import Role, User
from pms.security import audit, passwords
from pms.security.permissions import Action, require

import psycopg.errors

_USERNAME = re.compile(r"^[a-z0-9._-]{3,50}$")


def _clean_username(username: str) -> str:
    cleaned = username.strip().lower()
    if not _USERNAME.match(cleaned):
        raise ValidationError(
            "The username must be 3 to 50 characters: letters, numbers, dots, dashes or underscores."
        )
    return cleaned


def _clean_name(full_name: str) -> str:
    cleaned = " ".join(full_name.split())
    if not cleaned:
        raise ValidationError("Enter the person's full name.")
    if len(cleaned) > 100:
        raise ValidationError("The full name is too long (100 characters at most).")
    return cleaned


def list_users(actor: User) -> list[User]:
    require(actor, Action.MANAGE_USERS)
    with database.transaction() as conn:
        return [User.from_row(r) for r in user_dao.list_all(conn)]


def get_user(actor: User, user_id: int) -> User:
    require(actor, Action.MANAGE_USERS)
    with database.transaction() as conn:
        row = user_dao.get_by_id(conn, user_id)
    if row is None:
        raise NotFoundError("That user does not exist.")
    return User.from_row(row)


def create_user(actor: User, username: str, full_name: str, password: str, role: Role) -> User:
    require(actor, Action.MANAGE_USERS)
    username = _clean_username(username)
    full_name = _clean_name(full_name)
    password_hash = passwords.hash_password(password)  # validates the password too
    try:
        with database.transaction() as conn:
            row = user_dao.insert(conn, username, full_name, password_hash, Role(role).value)
            audit.log_action(actor, "user.create", entity="user", entity_id=row["id"],
                             details=f"{username} ({Role(role).label})", conn=conn)
    except psycopg.errors.UniqueViolation:
        raise ConflictError(f"The username '{username}' is already taken.") from None
    return User.from_row(row)


def update_user(actor: User, user_id: int, full_name: str, role: Role) -> User:
    require(actor, Action.MANAGE_USERS)
    full_name = _clean_name(full_name)
    role = Role(role)
    error: str | None = None
    updated = None
    with database.transaction() as conn:
        current = user_dao.get_by_id(conn, user_id)
        if current is None:
            raise NotFoundError("That user does not exist.")
        if (
            current["role"] == Role.SYSTEM_MANAGER.value
            and role != Role.SYSTEM_MANAGER
            and current["is_active"]
            and _active_system_managers(conn) <= 1
        ):
            error = "There must always be at least one active system manager."
        else:
            updated = user_dao.update_profile(conn, user_id, full_name, role.value)
            audit.log_action(actor, "user.update", entity="user", entity_id=user_id,
                             details=f"name='{full_name}', role={role.value}", conn=conn)
    if error:
        raise ValidationError(error)
    return User.from_row(updated)


def set_active(actor: User, user_id: int, active: bool) -> User:
    require(actor, Action.MANAGE_USERS)
    error: str | None = None
    updated = None
    with database.transaction() as conn:
        current = user_dao.get_by_id(conn, user_id)
        if current is None:
            raise NotFoundError("That user does not exist.")
        if not active and user_id == actor.id:
            error = "You cannot deactivate your own account."
        elif (
            not active
            and current["role"] == Role.SYSTEM_MANAGER.value
            and current["is_active"]
            and _active_system_managers(conn) <= 1
        ):
            error = "There must always be at least one active system manager."
        else:
            updated = user_dao.set_active(conn, user_id, active)
            audit.log_action(actor, "user.activate" if active else "user.deactivate",
                             entity="user", entity_id=user_id,
                             details=current["username"], conn=conn)
    if error:
        raise ValidationError(error)
    return User.from_row(updated)


def reset_password(actor: User, user_id: int, new_password: str) -> None:
    """Set a new password for someone else (also clears a lockout)."""
    require(actor, Action.MANAGE_USERS)
    new_hash = passwords.hash_password(new_password)
    with database.transaction() as conn:
        target = user_dao.get_by_id(conn, user_id)
        if target is None:
            raise NotFoundError("That user does not exist.")
        user_dao.set_password_hash(conn, user_id, new_hash)
        audit.log_action(actor, "user.password_reset", entity="user", entity_id=user_id,
                         details=target["username"], conn=conn)


def _active_system_managers(conn) -> int:
    return conn.execute(
        "SELECT COUNT(*)::int AS n FROM users WHERE role = %s AND is_active",
        (Role.SYSTEM_MANAGER.value,),
    ).fetchone()["n"]
