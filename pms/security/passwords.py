"""Password hashing (bcrypt) and the rules for choosing a password."""
from __future__ import annotations

import bcrypt

from pms.errors import ValidationError

MIN_LENGTH = 8
_BCRYPT_MAX_BYTES = 72  # bcrypt ignores (or rejects) anything beyond this


def validate_new_password(password: str) -> None:
    """Raise ValidationError (with a message safe to show the user) if the password is weak."""
    if len(password) < MIN_LENGTH:
        raise ValidationError(f"The password must be at least {MIN_LENGTH} characters long.")
    if len(password.encode("utf-8")) > _BCRYPT_MAX_BYTES:
        raise ValidationError("The password is too long (72 bytes at most).")
    if not any(ch.isalpha() for ch in password) or not any(ch.isdigit() for ch in password):
        raise ValidationError("The password must contain at least one letter and one number.")


def hash_password(password: str) -> str:
    validate_new_password(password)
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("ascii")


def verify_password(password: str, password_hash: str) -> bool:
    """True if the password matches. Never raises for bad input; just returns False."""
    raw = password.encode("utf-8")
    if len(raw) > _BCRYPT_MAX_BYTES:
        return False
    try:
        return bcrypt.checkpw(raw, password_hash.encode("ascii"))
    except ValueError:
        return False
