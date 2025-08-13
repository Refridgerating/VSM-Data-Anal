from __future__ import annotations

from PyQt6.QtCore import QtMsgType, qInstallMessageHandler
from PyQt6.QtWidgets import QApplication, QMessageBox

from .main_window import MainWindow
from .utils.logging import LOG_FILE, logger

import sys


def main() -> None:
    """Entry point for the VSM GUI application."""
    def handle_exception(exc_type, exc, tb) -> None:  # noqa: ANN001
        logger.error("Uncaught exception", exc_info=(exc_type, exc, tb))
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Error")
        msg.setText(
            f"{exc_type.__name__}: {exc}\n\nSee log for details:\n{LOG_FILE}"
        )
        msg.exec()

    def qt_message_handler(msg_type: QtMsgType, context, message: str) -> None:  # noqa: ANN001
        mapping = {
            QtMsgType.QtDebugMsg: logger.debug,
            QtMsgType.QtInfoMsg: logger.info,
            QtMsgType.QtWarningMsg: logger.warning,
            QtMsgType.QtCriticalMsg: logger.error,
            QtMsgType.QtFatalMsg: logger.critical,
        }
        mapping.get(msg_type, logger.info)(message)

    sys.excepthook = handle_exception
    qInstallMessageHandler(qt_message_handler)

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
