from pms.ui.registry import ScreenSpec


def _home(ctx):
    from pms.ui.home.home_screen import HomeScreen

    return HomeScreen(ctx)


def _notifications(ctx):
    from pms.ui.home.notifications_screen import NotificationsScreen

    return NotificationsScreen(ctx)


SCREENS = [
    ScreenSpec("home", "Home", _home, None, order=0),
    ScreenSpec("notifications", "Notifications", _notifications, None, order=1),
]
