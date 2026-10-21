"""Creates one demo user for each role, so you can log in straight away.

    python -m pms.seed            (or:  python -m pms.migrate --seed)

Safe to run again: users that already exist are left alone. These accounts are for
development and the demo only; the password is the same for all of them.
"""
from __future__ import annotations

import sys

from pms.dao import database
from pms.dao.account import user_dao
from pms.model.account.user import Role
from pms.security import audit, passwords

DEMO_PASSWORD = "Pharmacy2026"

DEMO_USERS: list[tuple[str, str, Role]] = [
    ("admin", "Samuel Ojo", Role.SYSTEM_MANAGER),
    ("pharmacist", "Deborah Angomwile", Role.LEAD_PHARMACIST),
    ("stock", "Jennifer Okeke", Role.STOCK_MANAGER),
    ("finance", "Kamil Oladeji", Role.FINANCE_MANAGER),
    ("counter", "Lenny Valentini", Role.COUNTER_ASSISTANT),
]


def seed_demo_users() -> list[str]:
    """Create any missing demo users. Returns the usernames it created."""
    created: list[str] = []
    password_hash = passwords.hash_password(DEMO_PASSWORD)
    with database.transaction() as conn:
        for username, full_name, role in DEMO_USERS:
            exists = conn.execute(
                "SELECT 1 FROM users WHERE username = %s", (username,)
            ).fetchone()
            if exists:
                continue
            row = user_dao.insert(conn, username, full_name, password_hash, role.value)
            audit.log_action(None, "user.seed", entity="user", entity_id=row["id"],
                             details=f"{username} ({role.value})", conn=conn)
            created.append(username)
    return created


def main() -> int:
    problem = database.check_connection()
    if problem:
        print(f"Cannot reach the database: {problem}")
        print("Start it with 'docker compose up -d', then run 'python -m pms.migrate'.")
        return 1
    created = seed_demo_users()
    if created:
        print("Created: " + ", ".join(created))
    else:
        print("Demo users already exist.")
    print(f"Log in with any of {', '.join(u for u, _, _ in DEMO_USERS)} / password: {DEMO_PASSWORD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
