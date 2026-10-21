"""Starts the Pharmacy Management System.

    python -m pms.main
"""
from __future__ import annotations

import logging
import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox

from pms.dao import database
from pms.security.session import Session
from pms.ui import styles
from pms.ui.login_dialog import LoginDialog
from pms.ui.main_window import MainWindow


class PharmacyApp:
    """Shows the login window, then the main window; logging out goes back to the login."""

    def __init__(self, app: QApplication) -> None:
        self.app = app
        self.session = Session()
        self.window: MainWindow | None = None

    def show_login(self) -> bool:
        dialog = LoginDialog()
        if dialog.exec() != QDialog.Accepted or dialog.user is None:
            return False
        self.session.login(dialog.user)
        self.window = MainWindow(self.session)
        self.window.logged_out.connect(self._after_logout)
        self.window.show()
        return True

    def _after_logout(self) -> None:
        # Wait for the old window to finish closing before showing the login again.
        QTimer.singleShot(0, self._relogin)

    def _relogin(self) -> None:
        self.window = None
        if not self.show_login():
            self.app.quit()


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    app = QApplication(sys.argv)
    app.setApplicationName("Crossroads Community Pharmacy")
    app.setQuitOnLastWindowClosed(False)  # the main window decides when to quit
    styles.apply(app)

    problem = database.check_connection()
    if problem:
        QMessageBox.critical(
            None,
            "Database not available",
            "The app cannot reach the database.\n\n"
            "Start it with:  docker compose up -d\n"
            "Then set up the tables with:  python -m pms.migrate --seed\n\n"
            f"Details: {problem}",
        )
        return 1

    pharmacy = PharmacyApp(app)
    if not pharmacy.show_login():
        return 0
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
