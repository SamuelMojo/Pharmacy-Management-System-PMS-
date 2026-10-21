"""Small building blocks every screen can reuse, so the app looks and behaves consistently.

    from pms.ui import widgets

    layout.addWidget(widgets.PageHeader("Stock", "All medicines in the pharmacy"))
    table = widgets.make_table(["Name", "Quantity"])
    widgets.fill_table(table, [["Paracetamol", 40], ["Ibuprofen", 12]])

    try:
        service.do_something(...)
    except Exception as exc:
        widgets.show_error(self, exc)       # friendly message, never a traceback
"""
from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any, Callable, Sequence

import psycopg
from PySide6.QtCore import QObject, Qt, QTimer
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from pms.errors import UserError

log = logging.getLogger("pms.ui")


class PageHeader(QWidget):
    """A title with an optional one-line description, shown at the top of a screen."""

    def __init__(self, title: str, subtitle: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 8)
        layout.setSpacing(2)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("pageTitle")
        layout.addWidget(self.title_label)
        if subtitle:
            sub = QLabel(subtitle)
            sub.setObjectName("pageSubtitle")
            sub.setWordWrap(True)
            layout.addWidget(sub)


def primary_button(text: str) -> QPushButton:
    button = QPushButton(text)
    button.setObjectName("primary")
    return button


def danger_button(text: str) -> QPushButton:
    button = QPushButton(text)
    button.setObjectName("danger")
    return button


# ---- messages -------------------------------------------------------------------------

def error_text(exc: BaseException) -> str:
    """The text to show a user for an exception. Only UserErrors show their own message."""
    if isinstance(exc, UserError):
        return str(exc)
    if isinstance(exc, psycopg.OperationalError):
        return ("Cannot reach the database. Check that it is running "
                "(docker compose up -d) and try again.")
    log.exception("Unexpected error", exc_info=exc)
    return "Something went wrong. Please try again, and tell the team if it keeps happening."


def show_error(parent: QWidget | None, exc: BaseException, title: str = "Cannot do that") -> None:
    QMessageBox.warning(parent, title, error_text(exc))


def show_info(parent: QWidget | None, message: str, title: str = "Done") -> None:
    QMessageBox.information(parent, title, message)


def confirm(parent: QWidget | None, question: str, title: str = "Please confirm") -> bool:
    answer = QMessageBox.question(
        parent, title, question, QMessageBox.Yes | QMessageBox.No, QMessageBox.No
    )
    return answer == QMessageBox.Yes


# ---- tables ---------------------------------------------------------------------------

def make_table(headers: Sequence[str]) -> QTableWidget:
    """A read-only, sortable-looking table with one selected row at a time."""
    table = QTableWidget(0, len(headers))
    table.setHorizontalHeaderLabels(list(headers))
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.setSelectionMode(QAbstractItemView.SingleSelection)
    table.setAlternatingRowColors(True)
    table.verticalHeader().setVisible(False)
    table.horizontalHeader().setStretchLastSection(True)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
    table.setWordWrap(False)
    return table


def format_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.astimezone().strftime("%d %b %Y %H:%M:%S")
    if isinstance(value, date):
        return value.strftime("%d %b %Y")
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value)


def fill_table(table: QTableWidget, rows: Sequence[Sequence[Any]], ids: Sequence[Any] | None = None) -> None:
    """Replace the table's rows. ``ids`` (one per row) are stored so selected_id() can return them."""
    table.setRowCount(len(rows))
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            item = QTableWidgetItem(format_value(value))
            if ids is not None and c == 0:
                item.setData(Qt.UserRole, ids[r])
            table.setItem(r, c, item)


def selected_id(table: QTableWidget) -> Any | None:
    """The id stored for the selected row by fill_table, or None if nothing is selected."""
    row = table.currentRow()
    if row < 0:
        return None
    item = table.item(row, 0)
    return item.data(Qt.UserRole) if item else None


# ---- refreshing -----------------------------------------------------------------------

class AutoRefresh(QObject):
    """Calls ``callback`` every few seconds while ``widget`` is visible.

    This is how a screen shows changes made by another person on another computer:

        self._auto = widgets.AutoRefresh(self, self.refresh, seconds=15)
    """

    def __init__(self, widget: QWidget, callback: Callable[[], None], seconds: int = 15) -> None:
        super().__init__(widget)
        self._widget = widget
        self._callback = callback
        self._timer = QTimer(self)
        self._timer.setInterval(seconds * 1000)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def _tick(self) -> None:
        if self._widget.isVisible():
            try:
                self._callback()
            except Exception:  # a background refresh must never pop up errors
                log.exception("Auto refresh failed")
