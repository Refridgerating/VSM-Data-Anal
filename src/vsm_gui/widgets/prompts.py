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
) -> Literal["auto", "manual", "cancel"]:
    """Confirm use of an auto-detected field window with fit statistics."""

    box = QMessageBox(parent)
    box.setWindowTitle("Auto-detected window")
    box.setText(
        "A high-field linear region was detected automatically.\n"
        f"Hmin = {hmin:.3g}\nHmax = {hmax:.3g}\n"
        f"Points = {int(stats.get('npoints', 0))}\n"
        f"χ = {stats.get('chi', 0):.3g}\nR² = {stats.get('r2', 0):.3f}"
    )
    use_btn = box.addButton("Use detected", QMessageBox.ButtonRole.AcceptRole)
    manual_btn = box.addButton(
        "Choose manually...", QMessageBox.ButtonRole.ActionRole
    )
    box.addButton(QMessageBox.StandardButton.Cancel)
    box.exec()
    clicked = box.clickedButton()
    if clicked is use_btn:
        return "auto"
    if clicked is manual_btn:
        return "manual"
    return "cancel"


def confirm_detected_windows(parent: QWidget, label: str, stats: dict) -> str:
    """Confirm auto-detected tail windows with per-branch statistics.

    Returns "auto" if the user accepts the detected windows, "manual" if the
    user wants to choose manually, and "cancel" to skip the dataset.
    """

    lines: list[str] = []
    for branch in ("neg", "pos"):
        br = stats.get(branch)
        if not br:
            continue
        lines.append(
            f"{branch} branch: n={br.get('n', 0)}, R²={br.get('r2', 0):.3f}, "
            f"χ={br.get('chi', 0):.3g}, H=[{br.get('hmin', 0):.3g}, {br.get('hmax', 0):.3g}]"
        )
    if "chi_combined" in stats:
        lines.append(f"χ_combined = {stats['chi_combined']:.3g}")
    if stats.get("notes"):
        lines.append("")
        lines.extend(stats["notes"])

    box = QMessageBox(parent)
    box.setWindowTitle(f"Auto-detected windows - {label}")
    box.setText("\n".join(lines) or "No valid tails detected")
    use_btn = box.addButton("Use detected", QMessageBox.ButtonRole.AcceptRole)
    manual_btn = box.addButton("Choose manually...", QMessageBox.ButtonRole.ActionRole)
    box.addButton(QMessageBox.StandardButton.Cancel)
    box.exec()
    clicked = box.clickedButton()
    if clicked is use_btn:
        return "auto"
    if clicked is manual_btn:
        return "manual"
    return "cancel"


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

