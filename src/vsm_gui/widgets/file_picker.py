from __future__ import annotations

from PyQt6.QtWidgets import QFileDialog, QWidget

TITLE = "Open CSV Files"
FILTER = "CSV Files (*.csv)"


def pick_csv_files(parent: QWidget) -> list[str]:
    """Prompt the user to select CSV files.

    Parameters
    ----------
    parent : QWidget
        Parent widget.

    Returns
    -------
    list[str]
        Selected file paths.
    """
    files, _ = QFileDialog.getOpenFileNames(parent, TITLE, "", FILTER)
    return files
