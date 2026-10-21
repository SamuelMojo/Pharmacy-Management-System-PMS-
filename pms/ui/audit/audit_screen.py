"""Read-only view of the audit log with filters."""
from __future__ import annotations

from datetime import datetime, time, timedelta

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from pms.service import audit_service
from pms.service.audit_service import AuditFilter
from pms.ui import widgets
from pms.ui.registry import AppContext

PAGE_SIZE = 200
ANY = "(any)"


class AuditScreen(QWidget):
    def __init__(self, ctx: AppContext) -> None:
        super().__init__()
        self.ctx = ctx
        self._page = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)
        layout.addWidget(widgets.PageHeader("Audit log", "Who did what, and when. Entries cannot be edited or deleted."))

        filters = QHBoxLayout()
        self.user_box = QComboBox()
        self.action_box = QComboBox()
        self.use_dates = QCheckBox("Dates")
        self.since = QDateEdit(QDate.currentDate().addDays(-7))
        self.until = QDateEdit(QDate.currentDate())
        for edit in (self.since, self.until):
            edit.setCalendarPopup(True)
            edit.setDisplayFormat("dd MMM yyyy")
        self.text = QLineEdit()
        self.text.setPlaceholderText("Search details...")
        search = widgets.primary_button("Search")
        search.clicked.connect(self._search)
        self.text.returnPressed.connect(self._search)
        filters.addWidget(QLabel("User"))
        filters.addWidget(self.user_box)
        filters.addWidget(QLabel("Action"))
        filters.addWidget(self.action_box)
        filters.addWidget(self.use_dates)
        filters.addWidget(self.since)
        filters.addWidget(QLabel("to"))
        filters.addWidget(self.until)
        filters.addWidget(self.text, 1)
        filters.addWidget(search)
        layout.addLayout(filters)

        self.table = widgets.make_table(["When", "User", "Action", "Entity", "Entity id", "Details"])
        layout.addWidget(self.table, 1)

        paging = QHBoxLayout()
        self.status = QLabel("")
        self.status.setObjectName("muted")
        self.prev_button = QPushButton("Newer")
        self.next_button = QPushButton("Older")
        self.prev_button.clicked.connect(lambda: self._go(-1))
        self.next_button.clicked.connect(lambda: self._go(1))
        paging.addWidget(self.status, 1)
        paging.addWidget(self.prev_button)
        paging.addWidget(self.next_button)
        layout.addLayout(paging)

    def _current_filter(self) -> AuditFilter:
        since = until = None
        if self.use_dates.isChecked():
            since = datetime.combine(self.since.date().toPython(), time.min).astimezone()
            until = datetime.combine(self.until.date().toPython() + timedelta(days=1), time.min).astimezone()
        return AuditFilter(
            username=None if self.user_box.currentText() == ANY else self.user_box.currentText(),
            action=None if self.action_box.currentText() == ANY else self.action_box.currentText(),
            since=since,
            until=until,
            text=self.text.text(),
        )

    def refresh(self) -> None:
        users, actions = audit_service.filter_choices(self.ctx.user)
        keep_user, keep_action = self.user_box.currentText(), self.action_box.currentText()
        self.user_box.clear()
        self.user_box.addItems([ANY, *users])
        self.action_box.clear()
        self.action_box.addItems([ANY, *actions])
        if keep_user in users:
            self.user_box.setCurrentText(keep_user)
        if keep_action in actions:
            self.action_box.setCurrentText(keep_action)
        self._load()

    def _search(self) -> None:
        self._page = 0
        self._load()

    def _go(self, step: int) -> None:
        self._page = max(0, self._page + step)
        self._load()

    def _load(self) -> None:
        try:
            rows, total = audit_service.search(
                self.ctx.user, self._current_filter(), limit=PAGE_SIZE, offset=self._page * PAGE_SIZE
            )
        except Exception as exc:
            widgets.show_error(self, exc)
            return
        widgets.fill_table(
            self.table,
            [[r["occurred_at"], r["username"], r["action"], r["entity"], r["entity_id"], r["details"]] for r in rows],
        )
        first = self._page * PAGE_SIZE + 1 if rows else 0
        self.status.setText(f"Showing {first}-{self._page * PAGE_SIZE + len(rows)} of {total}")
        self.prev_button.setEnabled(self._page > 0)
        self.next_button.setEnabled((self._page + 1) * PAGE_SIZE < total)
