"""Who is allowed to do what.

Every developer uses this instead of writing their own role checks:

    from pms.security.permissions import Action, require

    def create_medicine(actor, ...):
        require(actor, Action.MANAGE_STOCK)      # raises PermissionDeniedError if not allowed

To add a new action: add a constant to ``Action``, then list it under each role that
may use it in ``ROLE_PERMISSIONS``. The system manager is allowed everything.
"""
from __future__ import annotations

from enum import Enum

from pms.errors import UserError
from pms.model.account.user import Role, User


class PermissionDeniedError(UserError):
    """The user's role does not allow this action."""


class Action(str, Enum):
    # Accounts and oversight
    MANAGE_USERS = "manage_users"
    VIEW_AUDIT_LOG = "view_audit_log"
    VIEW_REPORTS = "view_reports"
    # Stock and orders
    VIEW_STOCK = "view_stock"
    MANAGE_STOCK = "manage_stock"
    PLACE_ORDERS = "place_orders"
    # Sales and money
    PROCESS_SALE = "process_sale"
    PROCESS_REFUND = "process_refund"
    PAY_SUPPLIERS = "pay_suppliers"
    VIEW_PAYMENTS = "view_payments"
    # Patients and prescriptions
    LOG_PATIENT = "log_patient"
    VERIFY_PRESCRIPTION = "verify_prescription"
    SIGN_OFF_RESTRICTED = "sign_off_restricted"
    MANAGE_COMPLAINTS = "manage_complaints"
    LOG_COMPLAINT = "log_complaint"


_ALL = frozenset(Action)

ROLE_PERMISSIONS: dict[Role, frozenset[Action]] = {
    Role.COUNTER_ASSISTANT: frozenset({
        Action.VIEW_STOCK,
        Action.PROCESS_SALE,
        Action.LOG_PATIENT,
        Action.VERIFY_PRESCRIPTION,
        Action.LOG_COMPLAINT,
    }),
    Role.STOCK_MANAGER: frozenset({
        Action.VIEW_STOCK,
        Action.MANAGE_STOCK,
        Action.PLACE_ORDERS,
        Action.VIEW_REPORTS,
    }),
    Role.FINANCE_MANAGER: frozenset({
        Action.VIEW_STOCK,
        Action.VIEW_PAYMENTS,
        Action.PROCESS_REFUND,
        Action.PAY_SUPPLIERS,
        Action.VIEW_REPORTS,
    }),
    Role.LEAD_PHARMACIST: frozenset({
        Action.VIEW_STOCK,
        Action.LOG_PATIENT,
        Action.VERIFY_PRESCRIPTION,
        Action.SIGN_OFF_RESTRICTED,
        Action.MANAGE_COMPLAINTS,
        Action.LOG_COMPLAINT,
        Action.VIEW_REPORTS,
    }),
    Role.SYSTEM_MANAGER: _ALL,
}


def can(role: Role, action: Action) -> bool:
    return action in ROLE_PERMISSIONS.get(role, frozenset())


def permissions_for(role: Role) -> frozenset[Action]:
    return ROLE_PERMISSIONS.get(role, frozenset())


def require(user: User | None, action: Action) -> None:
    """Raise PermissionDeniedError unless this user may perform the action."""
    if user is None or not user.is_active:
        raise PermissionDeniedError("You need to log in to do that.")
    if not can(user.role, action):
        raise PermissionDeniedError(
            f"Your role ({user.role.label}) is not allowed to do that."
        )
