"""System manager: create users, change roles, deactivate, reset passwords."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from pms.model.account.user import Role, User
from pms.service.account import user_service
from pms.ui import widgets
from pms.ui.registry import AppContext


class UserDialog(QDialog):
    """Add a user (user=None) or edit one's name and role."""

    def __init__(self, parent: QWidget, user: User | None = None) -> None:
        super().__init__(parent)
        self.editing = user
        self.setWindowTitle("Edit user" if user else "Add user")
        self.setMinimumWidth(380)

        self.username = QLineEdit(user.username if user else "")
        self.username.setEnabled(user is None)
        self.full_name = QLineEdit(user.full_name if user else "")
        self.role = QComboBox()
        for role in Role:
            self.role.addItem(role.label, role)
        if user:
            self.role.setCurrentIndex(list(Role).index(user.role))
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)

        form = QFormLayout()
        form.addRow("Username", self.username)
        form.addRow("Full name", self.full_name)
        form.addRow("Role", self.role)
        if user is None:
            form.addRow("Password", self.password)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def values(self) -> tuple[str, str, str, Role]:
        return (self.username.text(), self.full_name.text(), self.password.text(), self.role.currentData())


class PasswordDialog(QDialog):
    def __init__(self, parent: QWidget, username: str) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Reset password for {username}")
        self.setMinimumWidth(360)
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        form = QFormLayout()
        form.addRow("New password", self.password)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)


class UserManagementScreen(QWidget):
    def __init__(self, ctx: AppContext) -> None:
        super().__init__()
        self.ctx = ctx
        self._users: dict[int, User] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)
        layout.addWidget(widgets.PageHeader("User accounts", "Create staff accounts and control who can log in."))

        bar = QHBoxLayout()
        self.add_button = widgets.primary_button("Add user")
        self.edit_button = QPushButton("Edit")
        self.toggle_button = QPushButton("Deactivate / activate")
        self.reset_button = QPushButton("Reset password")
        self.add_button.clicked.connect(self._add)
        self.edit_button.clicked.connect(self._edit)
        self.toggle_button.clicked.connect(self._toggle)
        self.reset_button.clicked.connect(self._reset)
        bar.addWidget(self.add_button)
        bar.addStretch(1)
        for button in (self.edit_button, self.toggle_button, self.reset_button):
            bar.addWidget(button)
        layout.addLayout(bar)

        self.table = widgets.make_table(["Username", "Full name", "Role", "Active"])
        layout.addWidget(self.table, 1)

    def refresh(self) -> None:
        users = user_service.list_users(self.ctx.user)
        self._users = {u.id: u for u in users}
        widgets.fill_table(
            self.table,
            [[u.username, u.full_name, u.role.label, u.is_active] for u in users],
            ids=[u.id for u in users],
        )

    def _selected(self) -> User | None:
        user_id = widgets.selected_id(self.table)
        if user_id is None:
            widgets.show_info(self, "Select a user in the table first.", "No user selected")
            return None
        return self._users.get(user_id)

    def _add(self) -> None:
        dialog = UserDialog(self)
        while dialog.exec() == QDialog.Accepted:
            username, full_name, password, role = dialog.values()
            try:
                user_service.create_user(self.ctx.user, username, full_name, password, role)
            except Exception as exc:
                widgets.show_error(self, exc)
                continue  # keep the dialog open so nothing typed is lost
            self.refresh()
            return

    def _edit(self) -> None:
        user = self._selected()
        if user is None:
            return
        dialog = UserDialog(self, user)
        while dialog.exec() == QDialog.Accepted:
            _, full_name, _, role = dialog.values()
            try:
                user_service.update_user(self.ctx.user, user.id, full_name, role)
            except Exception as exc:
                widgets.show_error(self, exc)
                continue
            self.refresh()
            return

    def _toggle(self) -> None:
        user = self._selected()
        if user is None:
            return
        verb = "Deactivate" if user.is_active else "Activate"
        if not widgets.confirm(self, f"{verb} {user.username}?"):
            return
        try:
            user_service.set_active(self.ctx.user, user.id, not user.is_active)
        except Exception as exc:
            widgets.show_error(self, exc)
        self.refresh()

    def _reset(self) -> None:
        user = self._selected()
        if user is None:
            return
        dialog = PasswordDialog(self, user.username)
        while dialog.exec() == QDialog.Accepted:
            try:
                user_service.reset_password(self.ctx.user, user.id, dialog.password.text())
            except Exception as exc:
                widgets.show_error(self, exc)
                continue
            widgets.show_info(self, f"The password for {user.username} has been reset.")
            return
