"""Reading the audit log (writing is done with pms.security.audit)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from pms.dao import audit_dao, database
from pms.model.account.user import User
from pms.security.permissions import Action, require


@dataclass(frozen=True)
class AuditFilter:
    username: str | None = None
    action: str | None = None
    since: datetime | None = None
    until: datetime | None = None
    text: str | None = None

    def as_kwargs(self) -> dict:
        return {
            "username": self.username or None,
            "action": self.action or None,
            "since": self.since,
            "until": self.until,
            "text": (self.text or "").strip() or None,
        }


def search(actor: User, flt: AuditFilter, *, limit: int = 200, offset: int = 0) -> tuple[list[dict], int]:
    """Return (rows, total matching rows)."""
    require(actor, Action.VIEW_AUDIT_LOG)
    with database.transaction() as conn:
        rows = audit_dao.search(conn, **flt.as_kwargs(), limit=limit, offset=offset)
        total = audit_dao.count(conn, **flt.as_kwargs())
    return rows, total


def filter_choices(actor: User) -> tuple[list[str], list[str]]:
    """The usernames and action names that exist, for the filter drop-downs."""
    require(actor, Action.VIEW_AUDIT_LOG)
    with database.transaction() as conn:
        return audit_dao.distinct_usernames(conn), audit_dao.distinct_actions(conn)
