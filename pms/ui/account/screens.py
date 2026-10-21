from pms.security.permissions import Action
from pms.ui.registry import ScreenSpec


def _users(ctx):
    from pms.ui.account.user_management_screen import UserManagementScreen

    return UserManagementScreen(ctx)


def _my_account(ctx):
    from pms.ui.account.my_account_screen import MyAccountScreen

    return MyAccountScreen(ctx)


SCREENS = [
    ScreenSpec("users", "User accounts", _users, Action.MANAGE_USERS, order=900),
    ScreenSpec("my_account", "My account", _my_account, None, order=990),
]
