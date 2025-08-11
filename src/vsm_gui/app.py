from __future__ import annotations

import sys
from PyQt6.QtWidgets import QApplication

from .main_window import MainWindow


def main() -> None:
    """Entry point for the VSM GUI application."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
