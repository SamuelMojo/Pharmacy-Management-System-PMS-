"""Your own details and changing your own password."""
from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QFrame, QLabel, QLineEdit, QVBoxLayout, QWidget

from pms.service.account import auth_service
from pms.ui import widgets
from pms.ui.registry import AppContext


class MyAccountScreen(QWidget):
    def __init__(self, ctx: AppContext) -> None:
        super().__init__()
        self.ctx = ctx
        user = ctx.user

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)
        layout.addWidget(widgets.PageHeader("My account", "Your details and password."))

        details = QFrame()
        details.setObjectName("card")
        form = QFormLayout(details)
        form.setContentsMargins(16, 14, 16, 14)
        form.addRow("Name", QLabel(user.full_name))
        form.addRow("Username", QLabel(user.username))
        form.addRow("Role", QLabel(user.role.label))
        layout.addWidget(details)

        heading = QLabel("Change password")
        heading.setStyleSheet("font-weight: 600;")
        layout.addWidget(heading)

        pw_card = QFrame()
        pw_card.setObjectName("card")
        pw_form = QFormLayout(pw_card)
        pw_form.setContentsMargins(16, 14, 16, 14)
        self.current = QLineEdit()
        self.new = QLineEdit()
        self.again = QLineEdit()
        for field in (self.current, self.new, self.again):
            field.setEchoMode(QLineEdit.Password)
        pw_form.addRow("Current password", self.current)
        pw_form.addRow("New password", self.new)
        pw_form.addRow("New password again", self.again)
        self.message = QLabel("At least 8 characters, with a letter and a number.")
        self.message.setObjectName("muted")
        pw_form.addRow(self.message)
        self.save = widgets.primary_button("Change password")
        self.save.clicked.connect(self._change)
        pw_form.addRow(self.save)
        layout.addWidget(pw_card)
        layout.addStretch(1)

    def _change(self) -> None:
        if self.new.text() != self.again.text():
            self.message.setStyleSheet("color: #b91c1c;")
            self.message.setText("The two new passwords do not match.")
            return
        try:
            auth_service.change_own_password(self.ctx.user, self.current.text(), self.new.text())
        except Exception as exc:
            self.message.setStyleSheet("color: #b91c1c;")
            self.message.setText(widgets.error_text(exc))
            return
        for field in (self.current, self.new, self.again):
            field.clear()
        self.message.setStyleSheet("color: #0f766e;")
        self.message.setText("Your password has been changed.")
