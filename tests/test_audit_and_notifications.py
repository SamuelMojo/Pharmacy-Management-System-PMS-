import psycopg
import pytest

from pms.dao import database
from pms.model.account.user import Role
from pms.security import audit, notifications
from pms.security.permissions import PermissionDeniedError
from pms.service import audit_service
from pms.service.audit_service import AuditFilter
from pms.errors import ValidationError


# ---- audit log ------------------------------------------------------------------------

def test_log_action_writes_a_row(admin):
    audit.log_action(admin, "medicine.price_change", entity="medicine", entity_id=7, details="1.20 -> 1.35")
    rows, total = audit_service.search(admin, AuditFilter())
    assert total == 1
    row = rows[0]
    assert (row["username"], row["action"], row["entity"], row["entity_id"]) == (
        "admin", "medicine.price_change", "medicine", "7")
    assert row["user_id"] == admin.id and row["occurred_at"] is not None


def test_log_action_without_a_user_uses_the_given_name(db):
    audit.log_action(None, "auth.login_failed", username="ghost")
    with database.transaction() as conn:
        assert conn.execute("SELECT username, user_id FROM audit_log").fetchone() == {
            "username": "ghost", "user_id": None}


def test_audit_row_joins_the_callers_transaction(admin):
    with pytest.raises(RuntimeError):
        with database.transaction() as conn:
            audit.log_action(admin, "thing.done", conn=conn)
            raise RuntimeError("something failed afterwards")
    _, total = audit_service.search(admin, AuditFilter(action="thing.done"))
    assert total == 0   # rolled back together with the change


def test_audit_log_rows_cannot_be_updated_or_deleted(admin):
    audit.log_action(admin, "x.y")
    with database.connect(autocommit=True) as conn:
        with pytest.raises(psycopg.errors.RaiseException, match="cannot be changed"):
            conn.execute("UPDATE audit_log SET action = 'hacked'")
        with pytest.raises(psycopg.errors.RaiseException, match="cannot be changed"):
            conn.execute("DELETE FROM audit_log")


def test_search_filters(admin, make_user):
    other = make_user(Role.STOCK_MANAGER, "stocky")
    audit.log_action(admin, "user.create", details="made someone")
    audit.log_action(other, "stock.adjust", details="count 5")
    audit.log_action(other, "stock.adjust", details="count 9")
    assert audit_service.search(admin, AuditFilter(username="stocky"))[1] == 2
    assert audit_service.search(admin, AuditFilter(action="user.create"))[1] == 1
    assert audit_service.search(admin, AuditFilter(text="count 9"))[1] == 1
    rows, total = audit_service.search(admin, AuditFilter(), limit=1)
    assert total == 3 and len(rows) == 1
    assert rows[0]["details"] == "count 9"          # newest first
    users, actions = audit_service.filter_choices(admin)
    assert users == ["admin", "stocky"] and actions == ["stock.adjust", "user.create"]


def test_only_the_system_manager_may_read_the_audit_log(make_user):
    actor = make_user(Role.LEAD_PHARMACIST)
    with pytest.raises(PermissionDeniedError):
        audit_service.search(actor, AuditFilter())


# ---- notifications --------------------------------------------------------------------

def test_notification_to_a_user(make_user):
    a, b = make_user(Role.COUNTER_ASSISTANT), make_user(Role.COUNTER_ASSISTANT)
    notifications.notify("Hello", "Just for you", user_id=a.id)
    assert notifications.unread_count(a) == 1
    assert notifications.unread_count(b) == 0


def test_notification_to_a_role_is_read_per_person(make_user):
    p1, p2 = make_user(Role.LEAD_PHARMACIST), make_user(Role.LEAD_PHARMACIST)
    other = make_user(Role.STOCK_MANAGER)
    notifications.notify("Restricted item", "Needs sign-off", role=Role.LEAD_PHARMACIST)
    assert notifications.unread_count(p1) == notifications.unread_count(p2) == 1
    assert notifications.unread_count(other) == 0

    note = notifications.list_for(p1)[0]
    assert note["is_read"] is False
    notifications.mark_read(p1, note["id"])
    assert notifications.unread_count(p1) == 0
    assert notifications.unread_count(p2) == 1      # p2 has not read it
    assert notifications.list_for(p1, unread_only=True) == []
    assert notifications.list_for(p1)[0]["is_read"] is True


def test_cannot_mark_someone_elses_notification_read(make_user):
    a, b = make_user(Role.COUNTER_ASSISTANT), make_user(Role.COUNTER_ASSISTANT)
    notifications.notify("Private", "For a", user_id=a.id)
    note_id = notifications.list_for(a)[0]["id"]
    notifications.mark_read(b, note_id)
    assert notifications.unread_count(a) == 1


def test_mark_all_read(make_user):
    user = make_user(Role.STOCK_MANAGER)
    notifications.notify("One", "1", role=Role.STOCK_MANAGER)
    notifications.notify("Two", "2", user_id=user.id)
    notifications.mark_all_read(user)
    assert notifications.unread_count(user) == 0


def test_notification_needs_a_recipient(db):
    with pytest.raises(ValidationError):
        notifications.notify("Nobody", "Nobody gets this")
