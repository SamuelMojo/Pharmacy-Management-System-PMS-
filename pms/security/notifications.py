"""In-app notifications (low stock, a prescription needs checking, ...).

Sending (any developer, from a service):

    from pms.security import notifications
    notifications.notify("Low stock", "Paracetamol 500mg is below its reorder level.",
                         role=Role.STOCK_MANAGER, entity="medicine", entity_id=12, conn=conn)

Reading (used by the bell in the app's top bar):

    notifications.unread_count(user)
    notifications.list_for(user)
    notifications.mark_read(user, notification_id)
"""
from __future__ import annotations

import psycopg

from pms.dao import database, notification_dao
from pms.errors import ValidationError
from pms.model.account.user import Role, User


def notify(
    title: str,
    message: str,
    *,
    user_id: int | None = None,
    role: Role | None = None,
    entity: str | None = None,
    entity_id: int | str | None = None,
    conn: psycopg.Connection | None = None,
) -> None:
    """Send to one user (``user_id``), to everyone with a role (``role``), or both."""
    if user_id is None and role is None:
        raise ValidationError("A notification needs a recipient user or role.")
    with database.transaction(conn) as c:
        notification_dao.insert(
            c,
            title,
            message,
            user_id,
            role.value if role else None,
            entity,
            None if entity_id is None else str(entity_id),
        )


def list_for(user: User, *, unread_only: bool = False, limit: int = 100) -> list[dict]:
    with database.transaction() as c:
        return notification_dao.list_for_user(
            c, user.id, user.role.value, unread_only=unread_only, limit=limit
        )


def unread_count(user: User) -> int:
    with database.transaction() as c:
        return notification_dao.unread_count(c, user.id, user.role.value)


def mark_read(user: User, notification_id: int) -> None:
    with database.transaction() as c:
        notification_dao.mark_read(c, notification_id, user.id, user.role.value)


def mark_all_read(user: User) -> None:
    with database.transaction() as c:
        notification_dao.mark_all_read(c, user.id, user.role.value)
