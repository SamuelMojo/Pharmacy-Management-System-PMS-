"""Users and their roles."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping


class Role(str, Enum):
    """The five roles in the brief. The value is what is stored in the database."""

    COUNTER_ASSISTANT = "counter_assistant"
    STOCK_MANAGER = "stock_manager"
    FINANCE_MANAGER = "finance_manager"
    LEAD_PHARMACIST = "lead_pharmacist"
    SYSTEM_MANAGER = "system_manager"

    @property
    def label(self) -> str:
        return ROLE_LABELS[self]

    @property
    def summary(self) -> str:
        return ROLE_SUMMARIES[self]


ROLE_LABELS: dict[Role, str] = {
    Role.COUNTER_ASSISTANT: "Medicine counter assistant",
    Role.STOCK_MANAGER: "Stock manager / pharmacist's assistant",
    Role.FINANCE_MANAGER: "Finance manager",
    Role.LEAD_PHARMACIST: "Lead pharmacist",
    Role.SYSTEM_MANAGER: "System manager",
}

ROLE_SUMMARIES: dict[Role, str] = {
    Role.COUNTER_ASSISTANT: (
        "You sell medicines, check prescriptions, log patients and pass patients who want "
        "to discuss a condition to the lead pharmacist."
    ),
    Role.STOCK_MANAGER: (
        "You keep the medicine records up to date, watch for low and expiring stock, and "
        "place and track orders with suppliers."
    ),
    Role.FINANCE_MANAGER: (
        "You look after customer payments and refunds, and pay supplier orders."
    ),
    Role.LEAD_PHARMACIST: (
        "You advise patients, sign off restricted medicines, and handle complaints."
    ),
    Role.SYSTEM_MANAGER: (
        "You have full access: user accounts, stock, payments, reports and the audit log."
    ),
}


@dataclass(frozen=True)
class User:
    """A person who can log in. The password hash is never part of this object."""

    id: int
    username: str
    full_name: str
    role: Role
    is_active: bool = True

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> "User":
        return cls(
            id=row["id"],
            username=row["username"],
            full_name=row["full_name"],
            role=Role(row["role"]),
            is_active=row["is_active"],
        )

    @property
    def first_name(self) -> str:
        parts = self.full_name.split()
        return parts[0] if parts else self.username
