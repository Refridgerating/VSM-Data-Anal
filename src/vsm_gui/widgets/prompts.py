# widgets/prompts.py

from __future__ import annotations

# Imports merged from both sides
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QInputDialog,
    QMessageBox,
    QWidget,
)
from typing import Literal, Mapping

# ---- High-field window prompt ----
TITLE = "High-field Window"
LABEL_HMIN = "H min"
LABEL_HMAX = "H max"


class FieldWindowDialog(QDialog):
    """Dialog to input a magnetic-field window."""

    def __init__(
        self,
        hmin: float | None = None,
        hmax: float | None = None,
        parent: QWidget | None = None,
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
    parent: QWidget | None = None,
    hmin: float | None = None,
    hmax: float | None = None,
) -> tuple[float, float] | None:
    """Prompt the user to enter a high-field window.

    Returns None if the dialog is cancelled.
    """
    dialog = FieldWindowDialog(hmin, hmax, parent)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return dialog.values()
    return None


def confirm_detected_window(parent: QWidget, hmin: float, hmax: float) -> bool:
    """Confirm use of an auto-detected field window.

    Returns ``True`` if the user chooses the detected window, ``False`` if the
    user wants to pick values manually.
    """
    box = QMessageBox(parent)
    box.setWindowTitle("Auto-detected window")
    box.setText(
        "A high-field linear region was detected automatically.\n"
        f"Hmin = {hmin:.3g}\nHmax = {hmax:.3g}"
    )
    use_btn = box.addButton("Use detected", QMessageBox.ButtonRole.AcceptRole)
    manual_btn = box.addButton("Choose manually...", QMessageBox.ButtonRole.ActionRole)
    box.exec()
    return box.clickedButton() is use_btn


def confirm_fit_window(
    parent: QWidget,
    hmin: float,
    hmax: float,
    stats: Mapping[str, float],
) -> tuple[Literal["auto", "manual", "cancel"], tuple[float, float] | None]:
    """Confirm use of an auto-detected field window with fit statistics."""

    box = QMessageBox(parent)
    box.setWindowTitle("Auto-detected window")
    box.setText(
        "A high-field linear region was detected automatically.\n"
        f"Hmin = {hmin:.3g}\nHmax = {hmax:.3g}\n"
        f"Points = {int(stats.get('npoints', 0))}\nR² = {stats.get('r2', 0):.3f}"
    )
    use_btn = box.addButton("Use detected", QMessageBox.ButtonRole.AcceptRole)
    manual_btn = box.addButton("Choose manually...", QMessageBox.ButtonRole.ActionRole)
    box.addButton(QMessageBox.StandardButton.Cancel)
    box.exec()
    clicked = box.clickedButton()
    if clicked is use_btn:
        return "auto", (hmin, hmax)
    if clicked is manual_btn:
        vals = prompt_field_window(parent, hmin, hmax)
        if vals is None:
            return "cancel", None
        return "manual", vals
    return "cancel", None


# ---- Sample parameters prompt (unit conversion helpers) ----
def sample_parameters(parent: QWidget) -> dict | None:
    """Collect optional sample parameters for unit conversion.

    Returns None if the user cancels any prompt.
    """
    params: dict[str, float] = {}

    mass, ok = QInputDialog.getDouble(
        parent, "Sample Mass", "Mass (kg)", 0.0, 0.0, 1e9, 6
    )
    if not ok:
        return None
    params["mass"] = mass

    density, ok = QInputDialog.getDouble(
        parent, "Sample Density", "Density (kg/m^3)", 0.0, 0.0, 1e9, 6
    )
    if not ok:
        return None
    params["density"] = density

    thickness, ok = QInputDialog.getDouble(
        parent, "Sample Thickness", "Thickness (m)", 0.0, 0.0, 1e9, 6
    )
    if not ok:
        return None
    params["thickness"] = thickness

    area, ok = QInputDialog.getDouble(
        parent, "Sample Area", "Area (m^2)", 0.0, 0.0, 1e9, 6
    )
    if not ok:
        return None
    params["area"] = area

    return params

