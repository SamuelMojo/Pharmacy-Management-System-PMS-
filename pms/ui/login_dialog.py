"""The login window."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from pms.model.account.user import User
from pms.service.account import auth_service
from pms.ui import widgets


class LoginDialog(QDialog):
    """Ask for a username and password. ``self.user`` is set after a successful login."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.user: User | None = None
        self.setWindowTitle("Log in - Crossroads Community Pharmacy")
        self.setMinimumWidth(380)

        title = QLabel("Crossroads Community Pharmacy")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Log in to the Pharmacy Management System")
        subtitle.setObjectName("pageSubtitle")

        self.username = QLineEdit()
        self.username.setPlaceholderText("Username")
        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.Password)
        self.error = QLabel("")
        self.error.setObjectName("error")
        self.error.setWordWrap(True)

        form = QFormLayout()
        form.addRow("Username", self.username)
        form.addRow("Password", self.password)

        self.login_button = widgets.primary_button("Log in")
        self.login_button.setDefault(True)
        self.login_button.clicked.connect(self.attempt_login)
        quit_button = QPushButton("Quit")
        quit_button.clicked.connect(self.reject)
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(quit_button)
        buttons.addWidget(self.login_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(10)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(8)
        layout.addLayout(form)
        layout.addWidget(self.error)
        layout.addLayout(buttons)
        self.username.setFocus()

    def attempt_login(self) -> None:
        self.error.setText("")
        self.login_button.setEnabled(False)
        try:
            self.user = auth_service.login(self.username.text(), self.password.text())
        except Exception as exc:
            self.error.setText(widgets.error_text(exc))
            self.password.clear()
            self.password.setFocus()
            self.login_button.setEnabled(True)
            return
        self.accept()
