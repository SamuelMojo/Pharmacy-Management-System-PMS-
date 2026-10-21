"""Record who did what. Every critical action in the system should call this.

    from pms.security import audit

    with database.transaction() as conn:
        medicine_dao.update_price(conn, medicine_id, new_price)
        audit.log_action(actor, "medicine.price_change", entity="medicine",
                         entity_id=medicine_id, details="1.20 -> 1.35", conn=conn)

Pass ``conn`` so the audit row is saved in the same transaction as the change itself:
either both happen or neither does. Without ``conn`` the row is saved on its own.

Use dotted names for actions, "<thing>.<verb>" (for example "user.create", "sale.refund").
"""
from __future__ import annotations

import psycopg

from pms.dao import audit_dao, database
from pms.model.account.user import User


def log_action(
    actor: User | None,
    action: str,
    *,
    entity: str | None = None,
    entity_id: int | str | None = None,
    details: str | None = None,
    username: str | None = None,
    conn: psycopg.Connection | None = None,
) -> None:
    """Add one row to the audit log.

    ``actor`` is the logged-in user, or None for events with no user (a failed login,
    system tasks). For those, pass ``username`` to say who it was (or leave it for "system").
    """
    name = actor.username if actor else (username or "system")
    with database.transaction(conn) as c:
        audit_dao.insert(
            c,
            actor.id if actor else None,
            name,
            action,
            entity,
            None if entity_id is None else str(entity_id),
            details,
        )
