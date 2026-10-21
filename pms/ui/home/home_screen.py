"""The first screen after login: a welcome, what the role does, and latest notifications."""
from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel, QListWidget, QListWidgetItem, QVBoxLayout, QWidget

from pms.security import notifications
from pms.ui import widgets
from pms.ui.registry import AppContext


class HomeScreen(QWidget):
    def __init__(self, ctx: AppContext) -> None:
        super().__init__()
        self.ctx = ctx
        user = ctx.user

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)
        layout.addWidget(widgets.PageHeader(f"Welcome, {user.first_name}", user.role.label))

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 14, 16, 14)
        summary = QLabel(user.role.summary)
        summary.setWordWrap(True)
        card_layout.addWidget(summary)
        layout.addWidget(card)

        heading = QLabel("Latest unread notifications")
        heading.setStyleSheet("font-weight: 600;")
        layout.addWidget(heading)
        self.list = QListWidget()
        self.list.setObjectName("notes")
        self.list.itemDoubleClicked.connect(lambda _item: ctx.open_screen("notifications"))
        layout.addWidget(self.list, 1)
        hint = QLabel("Double-click a notification to open your notifications.")
        hint.setObjectName("muted")
        layout.addWidget(hint)

        self._auto = widgets.AutoRefresh(self, self.refresh, seconds=20)

    def refresh(self) -> None:
        rows = notifications.list_for(self.ctx.user, unread_only=True, limit=8)
        self.list.clear()
        if not rows:
            self.list.addItem("You're all caught up.")
            return
        for row in rows:
            self.list.addItem(QListWidgetItem(f"{row['title']}: {row['message']}"))
