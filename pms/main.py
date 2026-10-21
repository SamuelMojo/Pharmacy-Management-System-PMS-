import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel


def main() -> int:
    app = QApplication(sys.argv)
    label = QLabel("PMS is running")
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setWindowTitle("Pharmacy Management System")
    label.resize(400, 200)
    label.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())