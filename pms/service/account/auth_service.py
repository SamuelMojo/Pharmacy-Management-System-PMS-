"""Logging in, and changing your own password."""
from __future__ import annotations

from datetime import datetime, timezone

from pms.dao import database
from pms.dao.account import user_dao
from pms.errors import UserError, ValidationError
from pms.model.account.user import User
from pms.security import audit, passwords

MAX_FAILED_ATTEMPTS = 5
LOCK_MINUTES = 15

_BAD_LOGIN = "Incorrect username or password."


class AuthError(UserError):
    """The login could not be completed. The message is safe to show on screen."""


def _minutes_left(locked_until: datetime) -> int:
    seconds = (locked_until - datetime.now(timezone.utc)).total_seconds()
    return max(1, int(seconds // 60) + 1)


def login(username: str, password: str) -> User:
    """Check the credentials and return the user, or raise AuthError.

    Every outcome is written to the audit log. The error is raised after the database
    transaction has finished, so the failed-attempt count and audit rows are kept.
    """
    username = username.strip().lower()
    if not username or not password:
        raise AuthError("Enter your username and password.")

    error: str | None = None
    user: User | None = None
    with database.transaction() as conn:
        row = user_dao.get_login_row(conn, username)
        if row is None:
            audit.log_action(None, "auth.login_failed", username=username,
                             details="unknown username", conn=conn)
            error = _BAD_LOGIN
        else:
            candidate = User.from_row(row)
            locked_until = row["locked_until"]
            now = datetime.now(timezone.utc)
            if locked_until is not None and locked_until <= now:
                # The lock has run out: start counting from zero again.
                user_dao.reset_failed_attempts(conn, candidate.id)
                locked_until = None
            if locked_until is not None:
                audit.log_action(candidate, "auth.login_blocked", entity="user",
                                 entity_id=candidate.id, details="account locked", conn=conn)
                error = f"This account is locked. Try again in {_minutes_left(locked_until)} minute(s)."
            elif not passwords.verify_password(password, row["password_hash"]):
                result = user_dao.record_failed_attempt(
                    conn, candidate.id, MAX_FAILED_ATTEMPTS, LOCK_MINUTES
                )
                audit.log_action(candidate, "auth.login_failed", entity="user",
                                 entity_id=candidate.id,
                                 details=f"wrong password (attempt {result['failed_attempts']})",
                                 conn=conn)
                if result["locked_until"] is not None and result["failed_attempts"] >= MAX_FAILED_ATTEMPTS:
                    audit.log_action(candidate, "auth.account_locked", entity="user",
                                     entity_id=candidate.id,
                                     details=f"locked for {LOCK_MINUTES} minutes", conn=conn)
                    error = f"Too many failed attempts. The account is locked for {LOCK_MINUTES} minutes."
                else:
                    error = _BAD_LOGIN
            elif not candidate.is_active:
                audit.log_action(candidate, "auth.login_blocked", entity="user",
                                 entity_id=candidate.id, details="account deactivated", conn=conn)
                error = "This account has been deactivated. Ask the system manager for help."
            else:
                user_dao.reset_failed_attempts(conn, candidate.id)
                audit.log_action(candidate, "auth.login", entity="user",
                                 entity_id=candidate.id, conn=conn)
                user = candidate
    if error is not None or user is None:
        raise AuthError(error or _BAD_LOGIN)
    return user


def log_logout(user: User) -> None:
    audit.log_action(user, "auth.logout", entity="user", entity_id=user.id)


def change_own_password(user: User, current_password: str, new_password: str) -> None:
    """Let a logged-in user choose a new password."""
    error: str | None = None
    with database.transaction() as conn:
        row = user_dao.get_login_row_by_id(conn, user.id)
        if row is None or not passwords.verify_password(current_password, row["password_hash"]):
            audit.log_action(user, "auth.password_change_failed", entity="user",
                             entity_id=user.id, details="wrong current password", conn=conn)
            error = "Your current password is not correct."
        else:
            try:
                new_hash = passwords.hash_password(new_password)  # also validates
            except ValidationError as exc:
                error = str(exc)
            else:
                user_dao.set_password_hash(conn, user.id, new_hash)
                audit.log_action(user, "auth.password_change", entity="user",
                                 entity_id=user.id, conn=conn)
    if error is not None:
        raise ValidationError(error)
