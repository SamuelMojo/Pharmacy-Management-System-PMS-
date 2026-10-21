"""Who is logged in right now. One Session lives for as long as the app is open."""
from __future__ import annotations

from pms.model.account.user import User
from pms.security.permissions import Action, can, require


class Session:
    def __init__(self) -> None:
        self._user: User | None = None

    @property
    def user(self) -> User | None:
        return self._user

    @property
    def is_logged_in(self) -> bool:
        return self._user is not None

    def login(self, user: User) -> None:
        self._user = user

    def logout(self) -> None:
        self._user = None

    def can(self, action: Action) -> bool:
        return self._user is not None and can(self._user.role, action)

    def require(self, action: Action) -> User:
        """Return the user, or raise PermissionDeniedError."""
        require(self._user, action)
        assert self._user is not None
        return self._user
