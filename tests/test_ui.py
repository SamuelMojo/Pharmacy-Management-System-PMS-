"""Checks that the screens build and behave, using an invisible (offscreen) Qt."""
import pytest

pytest.importorskip("pytestqt")

from PySide6.QtWidgets import QLabel

from pms.model.account.user import Role
from pms.security import notifications
from pms.security.session import Session
from pms.ui import registry
from pms.ui.login_dialog import LoginDialog
from pms.ui.main_window import MainWindow
from pms.ui.registry import ScreenSpec
from tests.conftest import TEST_PASSWORD


def _keys_for(user):
    return [s.key for s in registry.screens_for(user)]


def test_screens_are_discovered_and_ordered():
    keys = [s.key for s in registry.discover()]
    assert {"home", "notifications", "users", "audit", "my_account"} <= set(keys)
    assert keys.index("home") < keys.index("users")


def test_sidebar_depends_on_role(make_user):
    admin_keys = _keys_for(make_user(Role.SYSTEM_MANAGER))
    counter_keys = _keys_for(make_user(Role.COUNTER_ASSISTANT))
    assert "users" in admin_keys and "audit" in admin_keys
    assert "users" not in counter_keys and "audit" not in counter_keys
    assert "home" in counter_keys and "my_account" in counter_keys


def test_login_dialog_rejects_bad_password_and_accepts_good(qtbot, admin):
    dialog = LoginDialog()
    qtbot.addWidget(dialog)
    dialog.username.setText("admin")
    dialog.password.setText("wrong-password1")
    dialog.attempt_login()
    assert dialog.user is None
    assert "Incorrect" in dialog.error.text()
    assert dialog.login_button.isEnabled()

    dialog.password.setText(TEST_PASSWORD)
    dialog.attempt_login()
    assert dialog.user is not None and dialog.user.username == "admin"


def _window(qtbot, user, specs=None):
    session = Session()
    session.login(user)
    window = MainWindow(session, specs)
    qtbot.addWidget(window)
    window.show()
    return window


def test_every_real_screen_opens_without_errors(qtbot, admin):
    window = _window(qtbot, admin)
    for key in window.screen_keys():
        window.show_screen(key)
        shown = window.stack.currentWidget()
        assert not (isinstance(shown, QLabel) and "could not be opened" in shown.text()), key


def test_a_broken_screen_does_not_break_the_app(qtbot, admin):
    def boom(ctx):
        raise RuntimeError("secret internal detail")

    specs = [
        ScreenSpec("ok", "Fine", lambda ctx: QLabel("fine"), None, order=1),
        ScreenSpec("bad", "Broken", boom, None, order=2),
    ]
    window = _window(qtbot, admin, specs)
    window.show_screen("bad")
    label = window.stack.currentWidget()
    assert isinstance(label, QLabel) and "could not be opened" in label.text()
    assert "secret internal detail" not in label.text()      # no internals shown to users
    window.show_screen("ok")
    assert window.stack.currentWidget().text() == "fine"


def test_bell_shows_unread_count(qtbot, admin):
    notifications.notify("Low stock", "Paracetamol", user_id=admin.id)
    window = _window(qtbot, admin)
    assert "(1)" in window.bell.text()
    notifications.mark_all_read(admin)
    window.update_bell()
    assert "(" not in window.bell.text()


def test_logout_clears_session_and_is_audited(qtbot, admin):
    window = _window(qtbot, admin)
    with qtbot.waitSignal(window.logged_out):
        window.log_out()
    assert window.session.user is None
    from pms.dao import database
    with database.transaction() as conn:
        actions = [r["action"] for r in conn.execute("SELECT action FROM audit_log")]
    assert "auth.logout" in actions
