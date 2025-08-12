from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QWidget,
)

TITLE = "High-field Window"
LABEL_HMIN = "H min"
LABEL_HMAX = "H max"


class FieldWindowDialog(QDialog):
    """Dialog to input a magnetic-field window."""

    def __init__(
        self, hmin: float | None = None, hmax: float | None = None, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(TITLE)

        self._hmin = QDoubleSpinBox()
        self._hmax = QDoubleSpinBox()
        for box in (self._hmin, self._hmax):
            box.setRange(-1e9, 1e9)
            box.setDecimals(6)
        if hmin is not None:
            self._hmin.setValue(hmin)
        if hmax is not None:
            self._hmax.setValue(hmax)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QFormLayout(self)
        layout.addRow(LABEL_HMIN, self._hmin)
        layout.addRow(LABEL_HMAX, self._hmax)
        layout.addWidget(buttons)

    def values(self) -> tuple[float, float]:
        return self._hmin.value(), self._hmax.value()


def prompt_field_window(
    parent: QWidget | None = None, hmin: float | None = None, hmax: float | None = None
) -> tuple[float, float] | None:
    """Prompt the user to enter a high-field window.

    Returns ``None`` if the dialog is cancelled.
    """
    dialog = FieldWindowDialog(hmin, hmax, parent)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return dialog.values()
    return None
