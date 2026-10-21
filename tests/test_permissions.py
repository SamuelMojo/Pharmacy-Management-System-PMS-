import pytest

from pms.model.account.user import Role, User
from pms.security.permissions import (
    ROLE_PERMISSIONS,
    Action,
    PermissionDeniedError,
    can,
    require,
)


def _user(role: Role, active: bool = True) -> User:
    return User(1, "u", "U", role, active)


def test_every_role_has_an_entry():
    assert set(ROLE_PERMISSIONS) == set(Role)


def test_system_manager_can_do_everything():
    assert all(can(Role.SYSTEM_MANAGER, action) for action in Action)


@pytest.mark.parametrize(
    "role, action",
    [
        (Role.COUNTER_ASSISTANT, Action.MANAGE_USERS),
        (Role.COUNTER_ASSISTANT, Action.VIEW_AUDIT_LOG),
        (Role.COUNTER_ASSISTANT, Action.SIGN_OFF_RESTRICTED),
        (Role.STOCK_MANAGER, Action.PROCESS_REFUND),
        (Role.FINANCE_MANAGER, Action.MANAGE_STOCK),
        (Role.LEAD_PHARMACIST, Action.MANAGE_USERS),
    ],
)
def test_roles_cannot_do_what_the_brief_does_not_give_them(role, action):
    assert not can(role, action)


@pytest.mark.parametrize(
    "role, action",
    [
        (Role.COUNTER_ASSISTANT, Action.PROCESS_SALE),
        (Role.STOCK_MANAGER, Action.PLACE_ORDERS),
        (Role.FINANCE_MANAGER, Action.PAY_SUPPLIERS),
        (Role.LEAD_PHARMACIST, Action.SIGN_OFF_RESTRICTED),
        (Role.LEAD_PHARMACIST, Action.MANAGE_COMPLAINTS),
    ],
)
def test_roles_can_do_their_own_jobs(role, action):
    assert can(role, action)


def test_only_system_manager_manages_users_and_reads_audit():
    for role in Role:
        expected = role is Role.SYSTEM_MANAGER
        assert can(role, Action.MANAGE_USERS) is expected
        assert can(role, Action.VIEW_AUDIT_LOG) is expected


def test_require_raises_with_a_readable_message():
    with pytest.raises(PermissionDeniedError, match="not allowed"):
        require(_user(Role.COUNTER_ASSISTANT), Action.MANAGE_USERS)


def test_require_rejects_nobody_and_inactive_users():
    with pytest.raises(PermissionDeniedError):
        require(None, Action.VIEW_STOCK)
    with pytest.raises(PermissionDeniedError):
        require(_user(Role.SYSTEM_MANAGER, active=False), Action.VIEW_STOCK)


def test_require_passes_when_allowed():
    require(_user(Role.STOCK_MANAGER), Action.MANAGE_STOCK)
