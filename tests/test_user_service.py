import pytest

from pms.dao import database
from pms.errors import ConflictError, NotFoundError, ValidationError
from pms.model.account.user import Role
from pms.security.permissions import PermissionDeniedError
from pms.service.account import auth_service, user_service
from tests.conftest import TEST_PASSWORD


def _actions():
    with database.transaction() as conn:
        return [r["action"] for r in conn.execute("SELECT action FROM audit_log ORDER BY id")]


def test_create_user_can_then_log_in_and_is_audited(admin):
    created = user_service.create_user(admin, " New.Person ", "  New   Person ", "Abcdef123", Role.STOCK_MANAGER)
    assert created.username == "new.person" and created.full_name == "New Person"
    assert auth_service.login("new.person", "Abcdef123").role is Role.STOCK_MANAGER
    assert "user.create" in _actions()


def test_duplicate_username_is_a_friendly_conflict(admin):
    user_service.create_user(admin, "dup", "Dup One", "Abcdef123", Role.COUNTER_ASSISTANT)
    with pytest.raises(ConflictError, match="already taken"):
        user_service.create_user(admin, "dup", "Dup Two", "Abcdef123", Role.COUNTER_ASSISTANT)


@pytest.mark.parametrize("bad", ["ab", "has space", "UPPER!", ""])
def test_bad_usernames_are_refused(admin, bad):
    with pytest.raises(ValidationError):
        user_service.create_user(admin, bad, "Name", "Abcdef123", Role.COUNTER_ASSISTANT)


def test_weak_password_is_refused_and_nothing_is_created(admin):
    with pytest.raises(ValidationError):
        user_service.create_user(admin, "weak", "Weak", "abc", Role.COUNTER_ASSISTANT)
    assert [u.username for u in user_service.list_users(admin)] == ["admin"]


def test_only_the_system_manager_can_manage_users(make_user, admin):
    for role in (Role.COUNTER_ASSISTANT, Role.STOCK_MANAGER, Role.FINANCE_MANAGER, Role.LEAD_PHARMACIST):
        actor = make_user(role)
        with pytest.raises(PermissionDeniedError):
            user_service.list_users(actor)
        with pytest.raises(PermissionDeniedError):
            user_service.create_user(actor, "sneaky", "Sneaky", "Abcdef123", Role.SYSTEM_MANAGER)


def test_update_user(admin, make_user):
    target = make_user(Role.COUNTER_ASSISTANT, "target")
    updated = user_service.update_user(admin, target.id, "Renamed Person", Role.LEAD_PHARMACIST)
    assert updated.full_name == "Renamed Person" and updated.role is Role.LEAD_PHARMACIST
    assert "user.update" in _actions()


def test_update_unknown_user(admin):
    with pytest.raises(NotFoundError):
        user_service.update_user(admin, 9999, "Nobody", Role.COUNTER_ASSISTANT)


def test_deactivate_and_reactivate(admin, make_user):
    target = make_user(Role.COUNTER_ASSISTANT, "target")
    assert user_service.set_active(admin, target.id, False).is_active is False
    with pytest.raises(auth_service.AuthError, match="deactivated"):
        auth_service.login("target", TEST_PASSWORD)
    assert user_service.set_active(admin, target.id, True).is_active is True
    assert auth_service.login("target", TEST_PASSWORD).id == target.id


def test_cannot_deactivate_yourself(admin):
    with pytest.raises(ValidationError, match="your own"):
        user_service.set_active(admin, admin.id, False)


def test_cannot_remove_the_last_system_manager(admin, make_user):
    other = make_user(Role.SYSTEM_MANAGER, "second")
    # Two managers: demoting one is fine.
    user_service.update_user(admin, other.id, "Second", Role.STOCK_MANAGER)
    # Now admin is the only one left, so admin cannot demote themselves.
    with pytest.raises(ValidationError, match="at least one active system manager"):
        user_service.update_user(admin, admin.id, "Admin", Role.STOCK_MANAGER)


def test_reset_password_unlocks_and_works(admin, make_user):
    target = make_user(Role.COUNTER_ASSISTANT, "target")
    for _ in range(auth_service.MAX_FAILED_ATTEMPTS):
        with pytest.raises(auth_service.AuthError):
            auth_service.login("target", "nope12345")
    user_service.reset_password(admin, target.id, "Fresh12345")
    assert auth_service.login("target", "Fresh12345").id == target.id
    assert "user.password_reset" in _actions()
