"""The window shown after login: sidebar of screens, top bar with the user and bell."""
from __future__ import annotations

import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from pms.model.account.user import User
from pms.security import notifications
from pms.security.session import Session
from pms.service.account import auth_service
from pms.ui import registry, widgets
from pms.ui.registry import AppContext, ScreenSpec

log = logging.getLogger("pms.ui")

NOTIFICATION_POLL_SECONDS = 20


class MainWindow(QMainWindow):
    logged_out = Signal()

    def __init__(self, session: Session, specs: list[ScreenSpec] | None = None) -> None:
        super().__init__()
        assert session.user is not None
        self.session = session
        self._logging_out = False
        self.user: User = session.user
        self.setWindowTitle("Crossroads Community Pharmacy")
        self.resize(1180, 760)

        self.ctx = AppContext(
            session=session,
            open_screen=self.show_screen,
            refresh_notifications=self.update_bell,
        )
        self._specs = registry.screens_for(self.user, specs)
        self._index_by_key: dict[str, int] = {}
        self._built: set[str] = set()

        root = QWidget()
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(self._build_sidebar())

        right = QWidget()
        right.setObjectName("content")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        right_layout.addWidget(self._build_topbar())
        self.stack = QStackedWidget()
        right_layout.addWidget(self.stack, 1)
        outer.addWidget(right, 1)
        self.setCentralWidget(root)

        for spec in self._specs:
            placeholder = QWidget()
            self._index_by_key[spec.key] = self.stack.addWidget(placeholder)
            item = QListWidgetItem(spec.title)
            item.setData(Qt.UserRole, spec.key)
            self.nav.addItem(item)

        self.nav.currentItemChanged.connect(self._on_nav_changed)
        if self._specs:
            self.nav.setCurrentRow(0)

        self.update_bell()
        self._poll = widgets.AutoRefresh(self, self.update_bell, NOTIFICATION_POLL_SECONDS)

    # ---- layout pieces ----------------------------------------------------------------

    def _build_sidebar(self) -> QWidget:
        side = QWidget()
        side.setObjectName("sidebar")
        side.setFixedWidth(230)
        layout = QVBoxLayout(side)
        layout.setContentsMargins(0, 0, 0, 12)
        layout.setSpacing(0)
        brand = QLabel("Crossroads\nCommunity Pharmacy")
        brand.setObjectName("brand")
        sub = QLabel("Pharmacy Management System")
        sub.setObjectName("brandSub")
        self.nav = QListWidget()
        layout.addWidget(brand)
        layout.addWidget(sub)
        layout.addWidget(self.nav, 1)
        return side

    def _build_topbar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("topbar")
        bar.setFixedHeight(52)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 0, 16, 0)
        self.page_label = QLabel("")
        self.page_label.setObjectName("pageSubtitle")
        who = QLabel(self.user.full_name)
        who.setObjectName("who")
        role = QLabel(f"· {self.user.role.label}")
        role.setObjectName("role")
        self.bell = QPushButton("Notifications")
        self.bell.setObjectName("bell")
        self.bell.setCursor(Qt.PointingHandCursor)
        self.bell.clicked.connect(lambda: self.show_screen("notifications"))
        logout = QPushButton("Log out")
        logout.clicked.connect(self.log_out)
        layout.addWidget(self.page_label)
        layout.addStretch(1)
        layout.addWidget(who)
        layout.addWidget(role)
        layout.addSpacing(16)
        layout.addWidget(self.bell)
        layout.addWidget(logout)
        return bar

    # ---- screens ----------------------------------------------------------------------

    def screen_keys(self) -> list[str]:
        return [s.key for s in self._specs]

    def show_screen(self, key: str) -> None:
        """Switch to a screen by key (ignored if this user cannot see it)."""
        for row in range(self.nav.count()):
            if self.nav.item(row).data(Qt.UserRole) == key:
                if self.nav.currentRow() == row:
                    self._on_nav_changed(self.nav.item(row), None)
                else:
                    self.nav.setCurrentRow(row)
                return

    def _on_nav_changed(self, current: QListWidgetItem | None, _previous) -> None:
        if current is None:
            return
        key = current.data(Qt.UserRole)
        spec = next(s for s in self._specs if s.key == key)
        index = self._index_by_key[key]
        if key not in self._built:
            self._replace_screen(spec, index)
            self._built.add(key)
        self.stack.setCurrentIndex(index)
        self.page_label.setText(spec.title)
        screen = self.stack.widget(index)
        refresh = getattr(screen, "refresh", None)
        if callable(refresh):
            try:
                refresh()
            except Exception as exc:
                log.exception("Screen '%s' failed to refresh", key)
                widgets.show_error(self, exc, "Could not load this screen")

    def _replace_screen(self, spec: ScreenSpec, index: int) -> None:
        try:
            screen = spec.factory(self.ctx)
        except Exception as exc:
            log.exception("Screen '%s' failed to build", spec.key)
            screen = QLabel(f"This screen could not be opened.\n\n{widgets.error_text(exc)}")
            screen.setAlignment(Qt.AlignCenter)
            screen.setWordWrap(True)
        old = self.stack.widget(index)
        self.stack.removeWidget(old)
        old.deleteLater()
        self.stack.insertWidget(index, screen)

    # ---- notifications and logout -----------------------------------------------------

    def update_bell(self) -> None:
        try:
            count = notifications.unread_count(self.user)
        except Exception:
            self.bell.setText("Notifications")
            return
        self.bell.setText(f"Notifications ({count})" if count else "Notifications")

    def log_out(self) -> None:
        try:
            auth_service.log_logout(self.user)
        except Exception:
            log.exception("Could not record logout")
        self.session.logout()
        self._logging_out = True
        self.close()
        self.logged_out.emit()

    def closeEvent(self, event) -> None:
        # Closing the window with the X button quits the app; logging out does not.
        if not self._logging_out:
            QApplication.quit()
        super().closeEvent(event)
