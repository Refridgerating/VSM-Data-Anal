from __future__ import annotations

import csv

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDockWidget,
    QFileDialog,
    QHeaderView,
    QHBoxLayout,
    QInputDialog,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QApplication,
)

from ..analysis import anisotropy, metrics
from . import prompts
from ..plotting.manager import PlotManager


class AnalysisDock(QDockWidget):
    """Dock panel for computing magnetic parameters."""

    def __init__(self, manager: PlotManager, parent: QWidget | None = None) -> None:
        super().__init__("Analysis", parent)
        self.manager = manager

        widget = QWidget(self)
        layout = QVBoxLayout(widget)

        self.chk_ms = QCheckBox("Saturation Magnetization (Ms)")
        self.chk_hc = QCheckBox("Coercivity (Hc)")
        self.chk_mr = QCheckBox("Remanence (Mr)")
        self.chk_ku = QCheckBox("Anisotropy Constant (Ku)")
        layout.addWidget(self.chk_ms)
        layout.addWidget(self.chk_hc)
        layout.addWidget(self.chk_mr)
        layout.addWidget(self.chk_ku)

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

        btn_copy = QPushButton("Copy Results")
        btn_copy.clicked.connect(self.copy_results)
        btn_export = QPushButton("Export CSV")
        btn_export.clicked.connect(self.export_csv)
        row = QHBoxLayout()
        row.addWidget(btn_copy)
        row.addWidget(btn_export)
        layout.addLayout(row)

        self.setWidget(widget)

    # ------------------------------------------------------------------
    def _get_window(self) -> tuple[float, float] | None:
        text, ok = QInputDialog.getText(
            self, "High-field Window", "Hmin,Hmax (leave blank for default)"
        )
        if not ok:
            return None
        if not text.strip():
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
            if window is None and not self.chk_ms.isChecked() and not self.chk_ku.isChecked():
                return

        params = None
        if self.convert_chk.isChecked() and self.chk_ms.isChecked():
            params = prompts.sample_parameters(self)
            if params is None:
                return

        self.table.setRowCount(0)
        for item in datasets:
            label = item["label"]
            df = item["df"]
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(label))
            notes: list[str] = []

            if self.chk_ms.isChecked():
                try:
                    ms, _ = metrics.saturation_magnetization(
                        df, x_name, y_name, window=window, convert=self.convert_chk.isChecked(), params=params
                    )
                    self.table.setItem(row, 1, QTableWidgetItem(f"{ms:.3g}"))
                except Exception as exc:  # noqa: BLE001
                    self.table.setItem(row, 1, QTableWidgetItem(""))
                    notes.append(str(exc))
            else:
                self.table.setItem(row, 1, QTableWidgetItem(""))

            if self.chk_hc.isChecked():
                try:
                    hc, _ = metrics.coercivity(df, x_name, y_name)
                    self.table.setItem(row, 2, QTableWidgetItem(f"{hc:.3g}"))
                except Exception as exc:  # noqa: BLE001
                    self.table.setItem(row, 2, QTableWidgetItem(""))
                    notes.append(str(exc))
            else:
                self.table.setItem(row, 2, QTableWidgetItem(""))

            if self.chk_mr.isChecked():
                try:
                    mr, _ = metrics.remanence(df, x_name, y_name)
                    self.table.setItem(row, 3, QTableWidgetItem(f"{mr:.3g}"))
                except Exception as exc:  # noqa: BLE001
                    self.table.setItem(row, 3, QTableWidgetItem(""))
                    notes.append(str(exc))
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
                    if det.get("note"):
                        notes.append(det["note"])
                except Exception as exc:  # noqa: BLE001
                    self.table.setItem(row, 4, QTableWidgetItem(""))
                    notes.append(str(exc))
            else:
                self.table.setItem(row, 4, QTableWidgetItem(""))

            self.table.setItem(row, 5, QTableWidgetItem("; ".join(notes)))

    # ------------------------------------------------------------------
    def copy_results(self) -> None:
        rows = []
        for r in range(self.table.rowCount()):
            cols = []
            for c in range(self.table.columnCount()):
                item = self.table.item(r, c)
                cols.append(item.text() if item else "")
            rows.append("\t".join(cols))
        QApplication.clipboard().setText("\n".join(rows))

    def export_csv(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "", "CSV Files (*.csv)")
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            headers = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
            writer.writerow(headers)
            for r in range(self.table.rowCount()):
                row = []
                for c in range(self.table.columnCount()):
                    item = self.table.item(r, c)
                    row.append(item.text() if item else "")
                writer.writerow(row)
