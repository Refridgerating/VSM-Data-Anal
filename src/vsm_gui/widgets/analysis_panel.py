from __future__ import annotations

from typing import Dict

from PyQt6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..analysis import paramag
from ..plotting.manager import PlotManager
from ..utils import errors


class AnalysisPanel(QWidget):
    """Dock widget providing data analysis and corrections."""

    def __init__(self, manager: PlotManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.manager = manager
        self._fit_results: Dict[str, dict] = {}
        self._fit_lines: list = []

        layout = QVBoxLayout(self)

        corrections = QGroupBox("Corrections", self)
        corr_layout = QVBoxLayout(corrections)

        paramag_group = QGroupBox("Paramagnetic subtraction", corrections)
        form = QFormLayout(paramag_group)
        self.hmin_edit = QLineEdit()
        self.hmax_edit = QLineEdit()
        form.addRow("H min", self.hmin_edit)
        form.addRow("H max", self.hmax_edit)

        self.preview_check = QCheckBox("Preview on top of data")
        form.addRow(self.preview_check)

        btn_layout = QHBoxLayout()
        self.fit_btn = QPushButton("Fit & Preview")
        self.apply_btn = QPushButton("Apply to Selection")
        self.revert_btn = QPushButton("Revert")
        btn_layout.addWidget(self.fit_btn)
        btn_layout.addWidget(self.apply_btn)
        btn_layout.addWidget(self.revert_btn)
        form.addRow(btn_layout)

        self.chi_label = QLabel("χ: –")
        self.b_label = QLabel("b: –")
        form.addRow(self.chi_label, self.b_label)

        corr_layout.addWidget(paramag_group)
        layout.addWidget(corrections)
        layout.addStretch(1)

        self.fit_btn.clicked.connect(self.fit_and_preview)
        self.apply_btn.clicked.connect(self.apply_correction)
        self.revert_btn.clicked.connect(self.revert)

    # ------------------------------------------------------------------
    def _parse_window(self) -> tuple[float | None, float | None]:
        def parse(edit: QLineEdit) -> float | None:
            text = edit.text().strip()
            if not text:
                return None
            try:
                return float(text)
            except ValueError:
                return None

        return parse(self.hmin_edit), parse(self.hmax_edit)

    def _selected_labels(self) -> list[str]:
        # In this simplified implementation, operate on all original datasets
        return [
            lbl
            for lbl in self.manager.datasets.keys()
            if lbl not in self.manager.corrected_map.values()
        ]

    def _clear_fit_lines(self) -> None:
        for line in self._fit_lines:
            try:
                line.remove()
            except Exception:  # noqa: BLE001
                pass
        self._fit_lines.clear()

    # ------------------------------------------------------------------
    def fit_and_preview(self) -> None:
        self._clear_fit_lines()
        hmin, hmax = self._parse_window()
        self._fit_results.clear()

        for label in self._selected_labels():
            df, x, y = self.manager.datasets[label]
            try:
                result = paramag.fit_linear_tail(df, x, y, hmin, hmax)
            except Exception:  # noqa: BLE001
                errors.show_error(
                    self,
                    f"Failed to fit {label}: not enough high-field points.",
                    title="Fit Error",
                )
                continue
            self._fit_results[label] = result
            self.chi_label.setText(f"χ: {result['chi']:.3g}")
            self.b_label.setText(f"b: {result['b']:.3g}")

            # Plot fitted line on top of data
            line = self.manager.pane.axes.plot(
                result["x_fit"], result["y_fit"], "--", label=f"{label} fit"
            )
            self._fit_lines.extend(line)

            if self.preview_check.isChecked():
                df_corr = paramag.apply_subtraction(df, x, y, result["chi"], result["b"])
                y_corr = y + "_corr"
                self.manager.add_corrected(label, df_corr, x, y_corr)

        self.manager.pane.draw_idle()

    def apply_correction(self) -> None:
        if not self._fit_results:
            # Fit first
            self.fit_and_preview()
        for label, result in self._fit_results.items():
            df, x, y = self.manager.datasets[label]
            df_corr = paramag.apply_subtraction(df, x, y, result["chi"], result["b"])
            y_corr = y + "_corr"
            self.manager.add_corrected(label, df_corr, x, y_corr)

    def revert(self) -> None:
        for label in list(self.manager.corrected_map.keys()):
            self.manager.remove_corrected(label)
        self._clear_fit_lines()
        self.manager.pane.draw_idle()
