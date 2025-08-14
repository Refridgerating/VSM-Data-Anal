from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..utils.settings import AppSettings
from .plot_pane import PlotPane


@dataclass
class _TraceWidgets:
    width: QDoubleSpinBox
    marker: QComboBox
    msize: QSpinBox
    color_btn: QPushButton


class FormatDialog(QDialog):
    """Dialog to edit matplotlib style options with live preview."""

    def __init__(self, pane: PlotPane, settings: AppSettings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Format Graph")
        self.pane = pane
        self.settings = settings
        self._snapshot = pane.snapshot_style()

        layout = QVBoxLayout(self)
        self.tabs = QTabWidget(self)
        layout.addWidget(self.tabs)

        self._init_axes_tab()
        self._init_traces_tab()
        self._init_legend_tab()
        self._init_layout_tab()

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Apply
            | QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Reset
        )
        buttons.accepted.connect(self._on_ok)
        buttons.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self._on_apply)
        buttons.rejected.connect(self._on_cancel)
        buttons.button(QDialogButtonBox.StandardButton.Reset).clicked.connect(self._on_reset)
        layout.addWidget(buttons)

        self._load_from_settings()

    # ------------------------------------------------------------------
    # Tabs
    # ------------------------------------------------------------------
    def _init_axes_tab(self) -> None:
        tab = QWidget(self)
        grid = QGridLayout(tab)

        self.x_label_edit = QLineEdit(tab)
        self.y_label_edit = QLineEdit(tab)
        grid.addWidget(QLabel("X Label"), 0, 0)
        grid.addWidget(self.x_label_edit, 0, 1)
        grid.addWidget(QLabel("Y Label"), 1, 0)
        grid.addWidget(self.y_label_edit, 1, 1)

        self.xmin_spin = QDoubleSpinBox(tab)
        self.xmax_spin = QDoubleSpinBox(tab)
        self.ymin_spin = QDoubleSpinBox(tab)
        self.ymax_spin = QDoubleSpinBox(tab)
        for sp in (self.xmin_spin, self.xmax_spin, self.ymin_spin, self.ymax_spin):
            sp.setRange(-1e9, 1e9)
            sp.setDecimals(4)
        self.auto_x_chk = QCheckBox("Auto X", tab)
        self.auto_y_chk = QCheckBox("Auto Y", tab)
        grid.addWidget(self.auto_x_chk, 2, 0)
        grid.addWidget(self.xmin_spin, 2, 1)
        grid.addWidget(self.xmax_spin, 2, 2)
        grid.addWidget(self.auto_y_chk, 3, 0)
        grid.addWidget(self.ymin_spin, 3, 1)
        grid.addWidget(self.ymax_spin, 3, 2)

        self.xscale_combo = QComboBox(tab)
        self.xscale_combo.addItems(["linear", "log"])
        self.yscale_combo = QComboBox(tab)
        self.yscale_combo.addItems(["linear", "log"])
        grid.addWidget(QLabel("X Scale"), 4, 0)
        grid.addWidget(self.xscale_combo, 4, 1)
        grid.addWidget(QLabel("Y Scale"), 5, 0)
        grid.addWidget(self.yscale_combo, 5, 1)

        self.grid_chk = QCheckBox("Show Grid", tab)
        self.minor_chk = QCheckBox("Minor Ticks", tab)
        grid.addWidget(self.grid_chk, 6, 0)
        grid.addWidget(self.minor_chk, 6, 1)

        self.label_fs_spin = QSpinBox(tab)
        self.label_fs_spin.setRange(1, 72)
        self.tick_fs_spin = QSpinBox(tab)
        self.tick_fs_spin.setRange(1, 72)
        grid.addWidget(QLabel("Label Font"), 7, 0)
        grid.addWidget(self.label_fs_spin, 7, 1)
        grid.addWidget(QLabel("Tick Font"), 8, 0)
        grid.addWidget(self.tick_fs_spin, 8, 1)

        self.tabs.addTab(tab, "Axes")

    def _init_traces_tab(self) -> None:
        tab = QWidget(self)
        vbox = QVBoxLayout(tab)
        self.trace_table = QTableWidget(0, 5, tab)
        self.trace_table.setHorizontalHeaderLabels([
            "Label",
            "Line Width",
            "Marker",
            "Marker Size",
            "Color",
        ])
        vbox.addWidget(self.trace_table)

        btn_row = QHBoxLayout()
        sel_all = QPushButton("Select All", tab)
        sel_all.clicked.connect(self.trace_table.selectAll)
        reset_sel = QPushButton("Reset Selected", tab)
        reset_sel.clicked.connect(self._reset_selected_traces)
        btn_row.addWidget(sel_all)
        btn_row.addWidget(reset_sel)
        btn_row.addStretch(1)
        vbox.addLayout(btn_row)
        self.tabs.addTab(tab, "Traces")

    def _init_legend_tab(self) -> None:
        tab = QWidget(self)
        grid = QGridLayout(tab)

        self.legend_show_chk = QCheckBox("Show Legend", tab)
        grid.addWidget(self.legend_show_chk, 0, 0, 1, 2)

        grid.addWidget(QLabel("Location"), 1, 0)
        self.legend_loc_combo = QComboBox(tab)
        self.legend_loc_combo.addItems([
            "best",
            "upper right",
            "upper left",
            "lower left",
            "lower right",
            "right",
            "center left",
            "center right",
            "lower center",
            "upper center",
            "center",
        ])
        grid.addWidget(self.legend_loc_combo, 1, 1)

        self.legend_frame_chk = QCheckBox("Frame", tab)
        grid.addWidget(self.legend_frame_chk, 2, 0)

        grid.addWidget(QLabel("Font Size"), 3, 0)
        self.legend_fs_spin = QSpinBox(tab)
        self.legend_fs_spin.setRange(1, 72)
        grid.addWidget(self.legend_fs_spin, 3, 1)

        self.tabs.addTab(tab, "Legend")

    def _init_layout_tab(self) -> None:
        tab = QWidget(self)
        grid = QGridLayout(tab)

        self.title_edit = QLineEdit(tab)
        grid.addWidget(QLabel("Title"), 0, 0)
        grid.addWidget(self.title_edit, 0, 1)

        self.dpi_spin = QSpinBox(tab)
        self.dpi_spin.setRange(50, 600)
        grid.addWidget(QLabel("Figure DPI"), 1, 0)
        grid.addWidget(self.dpi_spin, 1, 1)

        self.tight_chk = QCheckBox("Tight Layout", tab)
        grid.addWidget(self.tight_chk, 2, 0, 1, 2)

        self.style_combo = QComboBox(tab)
        self.style_combo.addItems(["Default", "Presentation", "Print (B/W)", "Dark"])
        grid.addWidget(QLabel("Style"), 3, 0)
        grid.addWidget(self.style_combo, 3, 1)

        self.save_default_btn = QPushButton("Save as default style", tab)
        self.save_default_btn.clicked.connect(self._save_default_style)
        grid.addWidget(self.save_default_btn, 4, 0, 1, 2)

        self.tabs.addTab(tab, "Layout & Export")

    # ------------------------------------------------------------------
    # Settings helpers
    # ------------------------------------------------------------------
    def _load_from_settings(self) -> None:
        ax = self.pane.axes
        self.x_label_edit.setText(self.settings.get_str("axes/xlabel", ax.get_xlabel()))
        self.y_label_edit.setText(self.settings.get_str("axes/ylabel", ax.get_ylabel()))
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        self.xmin_spin.setValue(self.settings.get_float("axes/xmin", xlim[0]))
        self.xmax_spin.setValue(self.settings.get_float("axes/xmax", xlim[1]))
        self.ymin_spin.setValue(self.settings.get_float("axes/ymin", ylim[0]))
        self.ymax_spin.setValue(self.settings.get_float("axes/ymax", ylim[1]))
        self.auto_x_chk.setChecked(self.settings.get_bool("axes/auto_x", True))
        self.auto_y_chk.setChecked(self.settings.get_bool("axes/auto_y", True))
        self.xscale_combo.setCurrentText(self.settings.get_str("axes/xscale", ax.get_xscale()))
        self.yscale_combo.setCurrentText(self.settings.get_str("axes/yscale", ax.get_yscale()))
        self.grid_chk.setChecked(self.settings.get_bool("axes/grid", True))
        self.minor_chk.setChecked(self.settings.get_bool("axes/minor", True))
        self.label_fs_spin.setValue(self.settings.get_int("axes/label_fs", 12))
        self.tick_fs_spin.setValue(self.settings.get_int("axes/tick_fs", 10))

        legend = self.pane.axes.get_legend()
        self.legend_show_chk.setChecked(self.settings.get_bool("legend/show", legend is not None))
        self.legend_loc_combo.setCurrentText(self.settings.get_str("legend/loc", "best"))
        self.legend_frame_chk.setChecked(self.settings.get_bool("legend/frame", False))
        self.legend_fs_spin.setValue(self.settings.get_int("legend/fs", 10))

        self.title_edit.setText(self.settings.get_str("layout/title", self.pane.axes.get_title()))
        self.dpi_spin.setValue(self.settings.get_int("layout/dpi", int(self.pane.figure.get_dpi())))
        self.tight_chk.setChecked(self.settings.get_bool("layout/tight", False))
        self.style_combo.setCurrentText(self.settings.get_str("style/preset", "Default"))

        # Populate trace table
        lines = self.pane.get_lines()
        self.trace_table.setRowCount(len(lines))
        self._trace_widgets: Dict[str, _TraceWidgets] = {}
        for row, line in enumerate(lines):
            label = line.get_label()
            self.trace_table.setItem(row, 0, QTableWidgetItem(label))

            width = QDoubleSpinBox()
            width.setRange(0.1, 10.0)
            width.setValue(float(line.get_linewidth()))
            self.trace_table.setCellWidget(row, 1, width)

            marker = QComboBox()
            marker.addItems(["None", "o", "s", "^", "v", "x", "+", "*"])
            cur_marker = line.get_marker() or "None"
            marker.setCurrentText(cur_marker)
            self.trace_table.setCellWidget(row, 2, marker)

            msize = QSpinBox()
            msize.setRange(1, 50)
            msize.setValue(int(line.get_markersize()))
            self.trace_table.setCellWidget(row, 3, msize)

            btn = QPushButton()
            col = QColor(line.get_color())
            btn.setStyleSheet(f"background-color: {col.name()}")
            btn.clicked.connect(lambda _, b=btn: self._choose_color(b))
            self.trace_table.setCellWidget(row, 4, btn)

            self._trace_widgets[label] = _TraceWidgets(width, marker, msize, btn)

    # ------------------------------------------------------------------
    # Button handlers
    # ------------------------------------------------------------------
    def _choose_color(self, btn: QPushButton) -> None:
        col = QColor(btn.palette().button().color())
        from PyQt6.QtWidgets import QColorDialog

        new = QColorDialog.getColor(col, self, "Select Color")
        if new.isValid():
            btn.setStyleSheet(f"background-color: {new.name()}")

    def _reset_selected_traces(self) -> None:
        for idx in set(i.row() for i in self.trace_table.selectedIndexes()):
            item = self.trace_table.item(idx, 0)
            if not item:
                continue
            label = item.text()
            tw = self._trace_widgets[label]
            tw.width.setValue(1.0)
            tw.marker.setCurrentText("None")
            tw.msize.setValue(6)
            tw.color_btn.setStyleSheet("")

    def _save_default_style(self) -> None:
        self.settings.set("style/preset", self.style_combo.currentText())

    def _apply_axis(self) -> None:
        # Validate limits for log scales
        if self.xscale_combo.currentText() == "log" and self.xmin_spin.value() <= 0:
            QMessageBox.warning(self, "Invalid X Limit", "Log scale requires positive minimum; adjusted.")
            xmin = max(self.xmin_spin.value(), np.finfo(float).tiny)
            self.xmin_spin.setValue(xmin)
        if self.yscale_combo.currentText() == "log" and self.ymin_spin.value() <= 0:
            QMessageBox.warning(self, "Invalid Y Limit", "Log scale requires positive minimum; adjusted.")
            ymin = max(self.ymin_spin.value(), np.finfo(float).tiny)
            self.ymin_spin.setValue(ymin)

        self.pane.set_labels(self.x_label_edit.text(), self.y_label_edit.text())
        self.pane.set_limits(
            self.xmin_spin.value(),
            self.xmax_spin.value(),
            self.ymin_spin.value(),
            self.ymax_spin.value(),
            self.auto_x_chk.isChecked(),
            self.auto_y_chk.isChecked(),
        )
        self.pane.set_scale(self.xscale_combo.currentText(), self.yscale_combo.currentText())
        self.pane.set_grid(self.grid_chk.isChecked(), self.minor_chk.isChecked())
        self.pane.set_label_fontsize(self.label_fs_spin.value())
        self.pane.set_tick_fontsize(self.tick_fs_spin.value())

    def _apply_traces(self) -> None:
        for row in range(self.trace_table.rowCount()):
            label_item = self.trace_table.item(row, 0)
            if not label_item:
                continue
            label = label_item.text()
            tw = self._trace_widgets[label]
            color = tw.color_btn.palette().button().color().name()
            self.pane.apply_trace_style(
                label,
                color=color,
                linewidth=tw.width.value(),
                marker=tw.marker.currentText(),
                markersize=tw.msize.value(),
            )
            self.settings.set(f"traces/{label}/color", color)
            self.settings.set(f"traces/{label}/linewidth", float(tw.width.value()))
            self.settings.set(f"traces/{label}/marker", tw.marker.currentText())
            self.settings.set(f"traces/{label}/markersize", int(tw.msize.value()))

    def _apply_legend(self) -> None:
        self.pane.set_legend(
            self.legend_show_chk.isChecked(),
            self.legend_loc_combo.currentText(),
            self.legend_frame_chk.isChecked(),
            self.legend_fs_spin.value(),
        )

    def _apply_layout(self) -> None:
        self.pane.set_title(self.title_edit.text())
        self.pane.figure.set_dpi(self.dpi_spin.value())
        if self.tight_chk.isChecked():
            self.pane.figure.tight_layout()
        preset = self.style_combo.currentText()
        self.pane.apply_rc_preset(preset)
        self.settings.set("layout/title", self.title_edit.text())
        self.settings.set("layout/dpi", int(self.dpi_spin.value()))
        self.settings.set("layout/tight", bool(self.tight_chk.isChecked()))
        self.settings.set("style/preset", preset)

    def _apply_all(self) -> None:
        self._apply_axis()
        self._apply_traces()
        self._apply_legend()
        self._apply_layout()
        self.pane.draw_idle()

        # Persist axes/legend settings
        self.settings.set("axes/xlabel", self.x_label_edit.text())
        self.settings.set("axes/ylabel", self.y_label_edit.text())
        self.settings.set("axes/xmin", float(self.xmin_spin.value()))
        self.settings.set("axes/xmax", float(self.xmax_spin.value()))
        self.settings.set("axes/ymin", float(self.ymin_spin.value()))
        self.settings.set("axes/ymax", float(self.ymax_spin.value()))
        self.settings.set("axes/auto_x", bool(self.auto_x_chk.isChecked()))
        self.settings.set("axes/auto_y", bool(self.auto_y_chk.isChecked()))
        self.settings.set("axes/xscale", self.xscale_combo.currentText())
        self.settings.set("axes/yscale", self.yscale_combo.currentText())
        self.settings.set("axes/grid", bool(self.grid_chk.isChecked()))
        self.settings.set("axes/minor", bool(self.minor_chk.isChecked()))
        self.settings.set("axes/label_fs", int(self.label_fs_spin.value()))
        self.settings.set("axes/tick_fs", int(self.tick_fs_spin.value()))
        self.settings.set("legend/show", bool(self.legend_show_chk.isChecked()))
        self.settings.set("legend/loc", self.legend_loc_combo.currentText())
        self.settings.set("legend/frame", bool(self.legend_frame_chk.isChecked()))
        self.settings.set("legend/fs", int(self.legend_fs_spin.value()))

    # ------------------------------------------------------------------
    # Dialog button handlers
    # ------------------------------------------------------------------
    def _on_ok(self) -> None:
        self._apply_all()
        self.accept()

    def _on_apply(self) -> None:
        self._apply_all()

    def _on_cancel(self) -> None:
        self.pane.restore_style(self._snapshot)
        self.reject()

    def _on_reset(self) -> None:
        # Reset to matplotlib defaults
        import matplotlib as mpl

        self.x_label_edit.setText("")
        self.y_label_edit.setText("")
        self.auto_x_chk.setChecked(True)
        self.auto_y_chk.setChecked(True)
        self.xscale_combo.setCurrentText("linear")
        self.yscale_combo.setCurrentText("linear")
        self.grid_chk.setChecked(True)
        self.minor_chk.setChecked(True)
        self.label_fs_spin.setValue(int(mpl.rcParams.get("axes.labelsize", 10)))
        self.tick_fs_spin.setValue(int(mpl.rcParams.get("xtick.labelsize", 10)))
        self.legend_show_chk.setChecked(True)
        self.legend_loc_combo.setCurrentText("best")
        self.legend_frame_chk.setChecked(False)
        self.legend_fs_spin.setValue(10)
        self.title_edit.setText("")
        self.dpi_spin.setValue(int(self.pane.figure.get_dpi()))
        self.tight_chk.setChecked(False)
        self.style_combo.setCurrentText("Default")

        # Reset traces
        for label, tw in self._trace_widgets.items():
            tw.width.setValue(1.0)
            tw.marker.setCurrentText("None")
            tw.msize.setValue(6)
            tw.color_btn.setStyleSheet("")

        self.pane.restore_style(self._snapshot)

