import pytest

from pms.dao import database
from pms.model.account.user import Role
from pms.service.account import auth_service
from pms.service.account.auth_service import AuthError, MAX_FAILED_ATTEMPTS
from pms.errors import ValidationError
from tests.conftest import TEST_PASSWORD


def _audit_actions():
    with database.transaction() as conn:
        return [r["action"] for r in conn.execute("SELECT action FROM audit_log ORDER BY id")]


def test_good_login_returns_the_user_and_is_audited(admin):
    user = auth_service.login("admin", TEST_PASSWORD)
    assert user.id == admin.id and user.role is Role.SYSTEM_MANAGER
    assert _audit_actions() == ["auth.login"]


def test_username_is_not_case_sensitive(admin):
    assert auth_service.login("  ADMIN ", TEST_PASSWORD).id == admin.id


def test_wrong_password_and_unknown_user_give_the_same_message(admin):
    with pytest.raises(AuthError) as wrong:
        auth_service.login("admin", "nope12345")
    with pytest.raises(AuthError) as unknown:
        auth_service.login("ghost", "nope12345")
    assert str(wrong.value) == str(unknown.value) == "Incorrect username or password."


def test_failures_are_audited_even_though_login_raised(admin):
    with pytest.raises(AuthError):
        auth_service.login("admin", "nope12345")
    with pytest.raises(AuthError):
        auth_service.login("ghost", "nope12345")
    assert _audit_actions() == ["auth.login_failed", "auth.login_failed"]


def test_empty_fields_are_refused():
    with pytest.raises(AuthError):
        auth_service.login("", "")


def test_account_locks_after_too_many_failures(admin):
    for _ in range(MAX_FAILED_ATTEMPTS):
        with pytest.raises(AuthError):
            auth_service.login("admin", "nope12345")
    # Even the right password is refused while locked.
    with pytest.raises(AuthError, match="locked"):
        auth_service.login("admin", TEST_PASSWORD)
    assert "auth.account_locked" in _audit_actions()


def test_lock_expires_and_counting_restarts(admin):
    for _ in range(MAX_FAILED_ATTEMPTS):
        with pytest.raises(AuthError):
            auth_service.login("admin", "nope12345")
    with database.connect(autocommit=True) as conn:
        conn.execute("UPDATE users SET locked_until = now() - interval '1 minute'")
    assert auth_service.login("admin", TEST_PASSWORD).id == admin.id
    with database.transaction() as conn:
        row = conn.execute("SELECT failed_attempts, locked_until FROM users").fetchone()
    assert row["failed_attempts"] == 0 and row["locked_until"] is None


def test_successful_login_clears_earlier_failures(admin):
    for _ in range(MAX_FAILED_ATTEMPTS - 1):
        with pytest.raises(AuthError):
            auth_service.login("admin", "nope12345")
    auth_service.login("admin", TEST_PASSWORD)
    with pytest.raises(AuthError, match="Incorrect"):
        auth_service.login("admin", "nope12345")  # one failure, not a lock


def test_deactivated_user_cannot_log_in(make_user):
    make_user(Role.COUNTER_ASSISTANT, "gone", active=False)
    with pytest.raises(AuthError, match="deactivated"):
        auth_service.login("gone", TEST_PASSWORD)


def test_change_own_password(admin):
    auth_service.change_own_password(admin, TEST_PASSWORD, "Brandnew456")
    assert auth_service.login("admin", "Brandnew456").id == admin.id
    with pytest.raises(AuthError):
        auth_service.login("admin", TEST_PASSWORD)
    assert "auth.password_change" in _audit_actions()


def test_change_password_needs_the_current_one(admin):
    with pytest.raises(ValidationError, match="current password"):
        auth_service.change_own_password(admin, "wrongwrong1", "Brandnew456")
    assert "auth.password_change_failed" in _audit_actions()


def test_change_password_enforces_the_rules(admin):
    with pytest.raises(ValidationError, match="at least"):
        auth_service.change_own_password(admin, TEST_PASSWORD, "short1")
