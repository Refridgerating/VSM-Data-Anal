from __future__ import annotations

from typing import Sequence
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QWidget,
)

TITLE = "Select Columns"
LABEL_X = "X axis"
LABEL_Y = "Y axis"


class AxisMappingDialog(QDialog):
    """Dialog to choose X and Y columns."""

    def __init__(
        self,
        headers: Sequence[str],
        last_x: str | None = None,
        last_y: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(TITLE)

        self._x_combo = QComboBox()
        self._y_combo = QComboBox()
        self._x_combo.addItems(headers)
        self._y_combo.addItems(headers)
        if last_x in headers:
            self._x_combo.setCurrentText(last_x)
        if last_y in headers:
            self._y_combo.setCurrentText(last_y)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        note = QLabel("Files missing the selected columns will be skipped.")
        note.setWordWrap(True)

        layout = QFormLayout(self)
        layout.addRow(LABEL_X, self._x_combo)
        layout.addRow(LABEL_Y, self._y_combo)
        layout.addRow(note)
        layout.addWidget(buttons)

    def get_mapping(self) -> tuple[str, str]:
        """Return the selected X and Y columns."""
        return self._x_combo.currentText(), self._y_combo.currentText()
