"""All notifications for the logged-in user, with read / unread state."""
from __future__ import annotations

from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from pms.security import notifications
from pms.ui import widgets
from pms.ui.registry import AppContext


class NotificationsScreen(QWidget):
    def __init__(self, ctx: AppContext) -> None:
        super().__init__()
        self.ctx = ctx

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)
        layout.addWidget(widgets.PageHeader("Notifications", "Alerts for you and for your role."))

        bar = QHBoxLayout()
        self.unread_only = QCheckBox("Unread only")
        self.unread_only.toggled.connect(lambda _checked: self.refresh())
        self.mark_selected = QPushButton("Mark selected as read")
        self.mark_selected.clicked.connect(self._mark_selected)
        self.mark_all = QPushButton("Mark all as read")
        self.mark_all.clicked.connect(self._mark_all)
        bar.addWidget(self.unread_only)
        bar.addStretch(1)
        bar.addWidget(self.mark_selected)
        bar.addWidget(self.mark_all)
        layout.addLayout(bar)

        self.table = widgets.make_table(["When", "Title", "Message", "Status"])
        layout.addWidget(self.table, 1)
        self._auto = widgets.AutoRefresh(self, self.refresh, seconds=20)

    def refresh(self) -> None:
        rows = notifications.list_for(self.ctx.user, unread_only=self.unread_only.isChecked())
        widgets.fill_table(
            self.table,
            [[r["created_at"], r["title"], r["message"], "Read" if r["is_read"] else "Unread"] for r in rows],
            ids=[r["id"] for r in rows],
        )
        self.ctx.refresh_notifications()

    def _mark_selected(self) -> None:
        notification_id = widgets.selected_id(self.table)
        if notification_id is None:
            return
        try:
            notifications.mark_read(self.ctx.user, notification_id)
            self.refresh()
        except Exception as exc:
            widgets.show_error(self, exc)

    def _mark_all(self) -> None:
        try:
            notifications.mark_all_read(self.ctx.user)
            self.refresh()
        except Exception as exc:
            widgets.show_error(self, exc)
