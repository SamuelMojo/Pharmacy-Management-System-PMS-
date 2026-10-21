"""The look of the whole app. Change colours here, not in individual screens."""
from __future__ import annotations

from PySide6.QtWidgets import QApplication

PRIMARY = "#0f766e"
PRIMARY_DARK = "#115e59"
SIDEBAR = "#10231f"
BG = "#f4f7f6"
TEXT = "#1f2937"
MUTED = "#6b7280"
DANGER = "#b91c1c"
BORDER = "#d1d9d6"

STYLESHEET = f"""
QWidget {{ color: {TEXT}; font-size: 14px; }}
QMainWindow, QDialog, #content {{ background: {BG}; }}

#sidebar {{ background: {SIDEBAR}; }}
#sidebar QLabel#brand {{ color: white; font-size: 17px; font-weight: 700; padding: 18px 16px 4px 16px; }}
#sidebar QLabel#brandSub {{ color: #9db5af; padding: 0 16px 14px 16px; }}
#sidebar QListWidget {{ background: transparent; border: none; outline: none; }}
#sidebar QListWidget::item {{ color: #d5e3df; padding: 10px 16px; border-left: 3px solid transparent; }}
#sidebar QListWidget::item:selected {{ background: #1a3a34; color: white; border-left: 3px solid #2dd4bf; }}
#sidebar QListWidget::item:hover {{ background: #16302b; }}

#topbar {{ background: white; border-bottom: 1px solid {BORDER}; }}
#topbar QLabel#who {{ font-weight: 600; }}
#topbar QLabel#role {{ color: {MUTED}; }}

QLabel#pageTitle {{ font-size: 22px; font-weight: 700; }}
QLabel#pageSubtitle {{ color: {MUTED}; }}
QLabel#error {{ color: {DANGER}; }}
QLabel#muted {{ color: {MUTED}; }}
QFrame#card {{ background: white; border: 1px solid {BORDER}; border-radius: 8px; }}

QPushButton {{ background: white; border: 1px solid {BORDER}; border-radius: 6px; padding: 7px 14px; }}
QPushButton:hover {{ background: #eef3f1; }}
QPushButton:disabled {{ color: #9ca3af; background: #f3f4f6; }}
QPushButton#primary {{ background: {PRIMARY}; color: white; border: 1px solid {PRIMARY}; font-weight: 600; }}
QPushButton#primary:hover {{ background: {PRIMARY_DARK}; }}
QPushButton#primary:disabled {{ background: #99c4c0; border-color: #99c4c0; }}
QPushButton#danger {{ color: {DANGER}; }}
QPushButton#bell {{ border: none; background: transparent; font-weight: 600; }}

QLineEdit, QComboBox, QDateEdit, QTextEdit, QSpinBox, QDoubleSpinBox {{
    background: white; border: 1px solid {BORDER}; border-radius: 6px; padding: 6px 8px;
}}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTextEdit:focus {{ border: 1px solid {PRIMARY}; }}

QTableWidget {{ background: white; border: 1px solid {BORDER}; border-radius: 6px;
    gridline-color: #e5ebe9; alternate-background-color: #f8faf9; selection-background-color: #c9ece7;
    selection-color: {TEXT}; }}
QHeaderView::section {{ background: #e8efed; border: none; border-bottom: 1px solid {BORDER};
    padding: 7px 8px; font-weight: 600; }}
QListWidget#notes {{ background: white; border: 1px solid {BORDER}; border-radius: 6px; }}
QListWidget#notes::item {{ padding: 8px; border-bottom: 1px solid #edf1f0; }}
"""


def apply(app: QApplication) -> None:
    app.setStyle("Fusion")
    app.setStyleSheet(STYLESHEET)
