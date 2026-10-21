import pytest

from pms.errors import ValidationError
from pms.security import passwords


def test_hash_then_verify_round_trip():
    hashed = passwords.hash_password("Secret123")
    assert hashed != "Secret123"
    assert passwords.verify_password("Secret123", hashed)


def test_wrong_password_is_rejected():
    hashed = passwords.hash_password("Secret123")
    assert not passwords.verify_password("Secret124", hashed)


def test_same_password_gives_different_hashes():
    assert passwords.hash_password("Secret123") != passwords.hash_password("Secret123")


@pytest.mark.parametrize("bad", ["short1", "allletters", "12345678", ""])
def test_weak_passwords_are_refused(bad):
    with pytest.raises(ValidationError):
        passwords.hash_password(bad)


def test_over_long_password_is_refused_not_crashed():
    with pytest.raises(ValidationError):
        passwords.hash_password("a1" * 40)


def test_verify_never_raises_on_garbage():
    assert not passwords.verify_password("x" * 100, passwords.hash_password("Secret123"))
    assert not passwords.verify_password("Secret123", "not-a-hash")
