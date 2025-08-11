from __future__ import annotations

from PyQt6.QtWidgets import QMessageBox, QWidget

DEFAULT_ERROR_TITLE = "Error"


def show_error(parent: QWidget, message: str, title: str = DEFAULT_ERROR_TITLE) -> None:
    """Display an error message box."""
    QMessageBox.critical(parent, title, message)


def show_info(parent: QWidget, message: str, title: str) -> None:
    """Display an informational message box."""
    QMessageBox.information(parent, title, message)
