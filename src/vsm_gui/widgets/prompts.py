from __future__ import annotations

from PyQt6.QtWidgets import QInputDialog, QWidget


def sample_parameters(parent: QWidget) -> dict | None:
    """Collect optional sample parameters for unit conversion.

    Returns ``None`` if the user cancels any prompt.
    """
    params: dict[str, float] = {}
    mass, ok = QInputDialog.getDouble(parent, "Sample Mass", "Mass (kg)", 0.0, 0.0, 1e9, 6)
    if not ok:
        return None
    params["mass"] = mass

    density, ok = QInputDialog.getDouble(parent, "Sample Density", "Density (kg/m^3)", 0.0, 0.0, 1e9, 6)
    if not ok:
        return None
    params["density"] = density

    thickness, ok = QInputDialog.getDouble(parent, "Sample Thickness", "Thickness (m)", 0.0, 0.0, 1e9, 6)
    if not ok:
        return None
    params["thickness"] = thickness

    area, ok = QInputDialog.getDouble(parent, "Sample Area", "Area (m^2)", 0.0, 0.0, 1e9, 6)
    if not ok:
        return None
    params["area"] = area

    return params
