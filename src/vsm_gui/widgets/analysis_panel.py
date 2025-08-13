from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDockWidget,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..analysis import anisotropy, metrics, paramag
from ..plotting.manager import PlotManager
from ..utils import errors
from . import prompts

import csv
import numpy as np
from typing import Dict


class AnalysisDock(QDockWidget):
    """Dock panel for computing magnetic parameters and applying corrections."""

    def __init__(self, manager: PlotManager, parent: QWidget | None = None) -> None:
        super().__init__("Analysis", parent)
        self.manager = manager
        self._fit_results: Dict[str, dict] = {}
        self._fit_lines: list = []
        self._analysis_results: Dict[str, dict] = {}
        self._marker_handles: list = []

        widget = QWidget(self)
        layout = QVBoxLayout(widget)

        # ----- Metrics controls -----
        self.chk_ms = QCheckBox("Saturation Magnetization (Ms)")
        self.chk_hc = QCheckBox("Coercivity (Hc)")
        self.chk_mr = QCheckBox("Remanence (Mr)")
        self.chk_ku = QCheckBox("Anisotropy Constant (Ku)")
        for w in (self.chk_ms, self.chk_hc, self.chk_mr, self.chk_ku):
            layout.addWidget(w)

        self.marker_chk = QCheckBox("Show markers on plot")
        self.marker_chk.setChecked(True)
        self.marker_chk.stateChanged.connect(
            lambda s: self._toggle_markers(s == Qt.CheckState.Checked)
        )
        layout.addWidget(self.marker_chk)

        self.convert_chk = QCheckBox("Convert to A/m")
        layout.addWidget(self.convert_chk)

        self.demag_chk = QCheckBox("Apply demag correction")
        self.geometry_combo = QComboBox()
        self.geometry_combo.addItems(["Thin film", "Rod", "Sphere"])
        self.geometry_combo.setEnabled(False)
        self.demag_chk.stateChanged.connect(
            lambda s: self.geometry_combo.setEnabled(s == Qt.CheckState.Checked)
        )
        layout.addWidget(self.demag_chk)
        layout.addWidget(self.geometry_combo)

        btn_compute = QPushButton("Compute")
        btn_compute.clicked.connect(self.compute)
        layout.addWidget(btn_compute)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["File", "Ms", "Hc", "Mr", "Ku", "Notes"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        row = QHBoxLayout()
        btn_copy = QPushButton("Copy Results")
        btn_copy.clicked.connect(self.copy_results)
        btn_export = QPushButton("Export CSV")
        btn_export.clicked.connect(self.export_csv)
        row.addWidget(btn_copy)
        row.addWidget(btn_export)
        layout.addLayout(row)

        # ----- Corrections: Paramagnetic subtraction -----
        corrections = QGroupBox("Corrections", self)
        corr_layout = QVBoxLayout(corrections)

        paramag_group = QGroupBox("Paramagnetic subtraction", corrections)
        form = QFormLayout(paramag_group)

        info = QLabel(
            "Subtract χ·H (slope only). Intercept b is shown for diagnostics."
        )
        info.setWordWrap(True)
        form.addRow(info)

        self.hmin_edit = QLineEdit()
        self.hmax_edit = QLineEdit()
        tip = (
            "High-field window for paramagnetic-tail fit. "
            "Leave blank to auto-detect per dataset (per branch)."
        )
        self.hmin_edit.setToolTip(tip)
        self.hmax_edit.setToolTip(tip)
        form.addRow("H min", self.hmin_edit)
        form.addRow("H max", self.hmax_edit)

        self.preview_check = QCheckBox("Preview on top of data")
        form.addRow(self.preview_check)

        btns = QHBoxLayout()
        self.fit_btn = QPushButton("Fit & Preview")
        self.apply_btn = QPushButton("Apply to Selection")
        self.revert_btn = QPushButton("Revert")
        for b in (self.fit_btn, self.apply_btn, self.revert_btn):
            btns.addWidget(b)
        form.addRow(btns)

        self.chi_label = QLabel("χ: –")
        self.b_label = QLabel("b: –")
        form.addRow(self.chi_label, self.b_label)

        corr_layout.addWidget(paramag_group)
        layout.addWidget(corrections)
        layout.addStretch(1)

        # Wire up correction actions
        self.fit_btn.clicked.connect(self.fit_and_preview)
        self.apply_btn.clicked.connect(self.apply_correction)
        self.revert_btn.clicked.connect(self.revert)

        self.setWidget(widget)

    # ===== Metrics helpers =====
    def _get_window(self) -> tuple[float, float] | None:
        text, ok = QInputDialog.getText(self, "High-field Window", "Hmin,Hmax (leave blank for default)")
        if not ok or not text.strip():
            return None
        try:
            hmin_str, hmax_str = text.split(",")
            return float(hmin_str), float(hmax_str)
        except Exception:  # noqa: BLE001
            QMessageBox.warning(self, "Invalid", "Window must be 'Hmin,Hmax'")
            return None

    def compute(self) -> None:
        datasets = self.manager.get_datasets()
        if not datasets:
            return
        x_name, y_name = self.manager.get_axis_names()
        if x_name is None or y_name is None:
            return

        window = None
        if self.chk_ms.isChecked() or self.chk_ku.isChecked():
            window = self._get_window()

        params = None
        if self.convert_chk.isChecked() and self.chk_ms.isChecked():
            params = prompts.sample_parameters(self)
            if params is None:
                return

        self.manager.pane.clear_markers()
        self._analysis_results.clear()
        self.table.setRowCount(0)
        for item in datasets:
            label = item["label"]; df = item["df"]
            row = self.table.rowCount(); self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(label))
            notes: list[str] = []
            result: dict = {}

            if self.chk_ms.isChecked():
                try:
                    ms, det = metrics.saturation_magnetization(
                        df,
                        x_name,
                        y_name,
                        window=window,
                        convert=self.convert_chk.isChecked(),
                        params=params,
                    )
                    self.table.setItem(row, 1, QTableWidgetItem(f"{ms:.3g}"))
                    result["ms"] = ms
                    result["ms_window"] = det.get("window")
                except Exception as exc:  # noqa: BLE001
                    self.table.setItem(row, 1, QTableWidgetItem("")); notes.append(str(exc))
            else:
                self.table.setItem(row, 1, QTableWidgetItem(""))

            if self.chk_hc.isChecked():
                try:
                    hc, det = metrics.coercivity(df, x_name, y_name)
                    self.table.setItem(row, 2, QTableWidgetItem(f"{hc:.3g}"))
                    result["hc"] = hc
                except Exception as exc:  # noqa: BLE001
                    self.table.setItem(row, 2, QTableWidgetItem("")); notes.append(str(exc))
            else:
                self.table.setItem(row, 2, QTableWidgetItem(""))

            if self.chk_mr.isChecked():
                try:
                    mr, det = metrics.remanence(df, x_name, y_name)
                    self.table.setItem(row, 3, QTableWidgetItem(f"{mr:.3g}"))
                    result["mr"] = mr
                except Exception as exc:  # noqa: BLE001
                    self.table.setItem(row, 3, QTableWidgetItem("")); notes.append(str(exc))
            else:
                self.table.setItem(row, 3, QTableWidgetItem(""))

            if self.chk_ku.isChecked():
                try:
                    ku, det = anisotropy.sucksmith_thompson(
                        df,
                        x_name,
                        y_name,
                        window=window,
                        apply_demag=self.demag_chk.isChecked(),
                        geometry=self.geometry_combo.currentText(),
                    )
                    self.table.setItem(row, 4, QTableWidgetItem(f"{ku:.3g}"))
                    result["ku"] = ku
                    result["ku_window"] = det.get("window")
                    if det.get("note"):
                        notes.append(det["note"])
                except Exception as exc:  # noqa: BLE001
                    self.table.setItem(row, 4, QTableWidgetItem("")); notes.append(str(exc))
            else:
                self.table.setItem(row, 4, QTableWidgetItem(""))

            self.table.setItem(row, 5, QTableWidgetItem("; ".join(notes)))
            self._analysis_results[label] = result

        if self.marker_chk.isChecked():
            self._draw_markers()

    def _draw_markers(self) -> None:
        pane = self.manager.pane
        pane.clear_markers()
        self._marker_handles.clear()
        for res in self._analysis_results.values():
            ms = res.get("ms")
            if ms is not None:
                window = res.get("ms_window")
                if window:
                    hmin, hmax = window
                    self._marker_handles.append(
                        pane.add_vline(0.5 * (hmin + hmax))
                    )
                self._marker_handles.append(
                    pane.add_hline(ms, label="Ms")
                )
            hc = res.get("hc")
            if hc is not None:
                self._marker_handles.extend(
                    pane.add_marker(-hc, 0.0, label="-Hc")
                )
                self._marker_handles.extend(
                    pane.add_marker(hc, 0.0, label="+Hc")
                )
            mr = res.get("mr")
            if mr is not None:
                self._marker_handles.extend(
                    pane.add_marker(0.0, mr, label="Mr")
                )
            ku = res.get("ku")
            if ku is not None:
                x0, x1 = pane.axes.get_xlim()
                y0, y1 = pane.axes.get_ylim()
                x = x0 + 0.05 * (x1 - x0)
                y = y1 - 0.05 * (y1 - y0)
                self._marker_handles.extend(
                    pane.add_marker(x, y, label=f"Ku={ku:.3g}")
                )
        pane.draw_idle()

    def _toggle_markers(self, enabled: bool) -> None:
        if enabled:
            self._draw_markers()
        else:
            self.manager.pane.clear_markers()

    def copy_results(self) -> None:
        rows = []
        for r in range(self.table.rowCount()):
            rows.append("\t".join(
                (self.table.item(r, c).text() if self.table.item(r, c) else "")
                for c in range(self.table.columnCount())
            ))
        QApplication.clipboard().setText("\n".join(rows))

    def export_csv(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "", "CSV Files (*.csv)")
        if not path: return
        with open(path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            headers = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
            writer.writerow(headers)
            for r in range(self.table.rowCount()):
                writer.writerow([
                    self.table.item(r, c).text() if self.table.item(r, c) else ""
                    for c in range(self.table.columnCount())
                ])

    # ===== Corrections helpers =====
    def _parse_window(self) -> tuple[float | None, float | None]:
        def parse(edit: QLineEdit) -> float | None:
            t = edit.text().strip()
            if not t: return None
            try: return float(t)
            except ValueError: return None
        return parse(self.hmin_edit), parse(self.hmax_edit)

    def _selected_labels(self) -> list[str]:
        # Operate on all original datasets (skip already-corrected labels)
        return [
            lbl
            for lbl in self.manager.datasets.keys()
            if lbl not in self.manager.corrected_map.values()
        ]

    def _clear_fit_lines(self) -> None:
        for line in self._fit_lines:
            try: line.remove()
            except Exception: pass
        self._fit_lines.clear()

    def fit_and_preview(self) -> None:
        self._clear_fit_lines()
        if hasattr(self.manager.pane, "clear_regions"):
            self.manager.pane.clear_regions()
        hmin_ui, hmax_ui = self._parse_window()
        if (hmin_ui is None) ^ (hmax_ui is None):
            errors.show_warning(self, "Provide both Hmin and Hmax", title="Fit Warning")
            return

        self._fit_results.clear()

        for label in self._selected_labels():
            try:
                df, x_name, y_name = self.manager.get_dataset_tuple(label)
            except ValueError:
                continue

            windows: dict[str, dict] = {}
            if hmin_ui is None and hmax_ui is None:
                try:
                    det = paramag.autodetect_windows(df, x_name, y_name)
                except Exception as exc:  # noqa: BLE001
                    errors.show_warning(
                        self,
                        f"{label}: auto-detect failed ({exc})",
                        title="Fit Warning",
                    )
                    continue
                choice = prompts.confirm_detected_windows(self, label, det)
                if choice == "cancel":
                    continue
                if choice == "manual":
                    vals = prompts.prompt_field_window(self)
                    if vals is None:
                        continue
                    hmin_use, hmax_use = vals
                    windows = {
                        "neg": {"hmin": -hmax_use, "hmax": -hmin_use},
                        "pos": {"hmin": hmin_use, "hmax": hmax_use},
                    }
                else:
                    windows = {k: det.get(k) for k in ("neg", "pos")}
            else:
                windows = {
                    "neg": {"hmin": -hmax_ui, "hmax": -hmin_ui},
                    "pos": {"hmin": hmin_ui, "hmax": hmax_ui},
                }

            branch_results: dict[str, dict] = {}
            for br, win in windows.items():
                if not win:
                    continue
                try:
                    res = paramag.fit_linear_tail(
                        df, x_name, y_name, win.get("hmin"), win.get("hmax")
                    )
                except Exception as exc:
                    errors.show_warning(
                        self,
                        f"Failed to fit {label} ({br}): {exc}",
                        title="Fit Warning",
                    )
                    continue
                branch_results[br] = res
                line = self.manager.pane.axes.plot(
                    res["x_fit"],
                    res["y_fit"],
                    "--",
                    color="gray",
                    alpha=0.7,
                    linewidth=1,
                    label=f"{label} {br} tail fit",
                )
                self._fit_lines.extend(line)
                if hasattr(self.manager.pane, "shade_xrange"):
                    self.manager.pane.shade_xrange(
                        res["hmin"], res["hmax"], label=None
                    )

            if not branch_results:
                continue

            chi_vals = [r["chi"] for r in branch_results.values()]
            b_vals = [r["b"] for r in branch_results.values()]
            chi_comb = float(np.median(chi_vals))
            b_comb = float(np.median(b_vals))
            self._fit_results[label] = {
                "chi": chi_comb,
                "b": b_comb,
                "branches": branch_results,
            }
            self.chi_label.setText(f"χ: {chi_comb:.3g}")
            self.b_label.setText(f"b: {b_comb:.3g}")

            if self.preview_check.isChecked():
                df_corr = paramag.apply_subtraction(df, x_name, y_name, chi_comb)
                line_corr = self.manager.pane.axes.plot(
                    df_corr[x_name],
                    df_corr[y_name + "_corr"],
                    "--",
                    color="gray",
                    alpha=0.7,
                    linewidth=1,
                    label=f"{label} corrected",
                )
                self._fit_lines.extend(line_corr)

        self.manager.pane.draw_idle()

    def apply_correction(self) -> None:
        if not self._fit_results:
            self.fit_and_preview()
        for label, result in self._fit_results.items():
            try:
                df, x_name, y_name = self.manager.get_dataset_tuple(label)
            except ValueError:
                continue
            df_corr = paramag.apply_subtraction(
                df, x_name, y_name, result["chi"]
            )
            self.manager.add_corrected(label, df_corr, x_name, y_name + "_corr")

    def revert(self) -> None:
        for label in self._selected_labels():
            if label in self.manager.corrected_map:
                self.manager.remove_corrected(label)
        self._clear_fit_lines()
        if hasattr(self.manager.pane, "clear_regions"):
            self.manager.pane.clear_regions()
        self.manager.pane.draw_idle()

