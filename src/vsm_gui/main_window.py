from __future__ import annotations

from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtGui import QAction, QDesktopServices
from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
import pandas as pd

from .file_io.parsers import load_any
from .plotting.manager import PlotManager
from .utils import errors
from .utils.logging import LOG_FILE, logger
from .widgets.analysis_panel import AnalysisDock
from .widgets.axis_mapping import AxisMappingDialog
from .widgets.file_picker import pick_csv_files
from .widgets.plot_pane import PlotPane

from pathlib import Path

WINDOW_TITLE = "VSM Data Viewer"
OPEN_TEXT = "Open…"
EXPORT_TEXT = "Export Plot…"
RESET_TEXT = "Reset Zoom"
ABOUT_TEXT = "About"
ABOUT_MESSAGE = "VSM Data Viewer\nA simple tool for plotting VSM data."
PNG_FILTER = "PNG Files (*.png)"


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self._last_x: str | None = None
        self._last_y: str | None = None

        self.pane = PlotPane(self)
        self.manager = PlotManager(self.pane)

        central = QWidget(self)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.pane)

        self.navbar = NavigationToolbar(self.pane, self)
        layout.addWidget(self.navbar)
        self.setCentralWidget(central)

        self.analysis_dock = AnalysisDock(self.manager, self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.analysis_dock)

        self._init_toolbar()
        self._init_menu()

    def _init_toolbar(self) -> None:
        grid = QAction("Grid", self)
        grid.setCheckable(True)
        grid.setChecked(True)
        grid.triggered.connect(self.pane.toggle_grid)
        self.navbar.addAction(grid)

        minor = QAction("Minor Ticks", self)
        minor.setCheckable(True)
        minor.setChecked(True)
        minor.triggered.connect(self.pane.toggle_minor_ticks)
        self.navbar.addAction(minor)

        legend = QAction("Legend", self)
        legend.setCheckable(True)
        legend.setChecked(True)
        legend.triggered.connect(self.pane.toggle_legend)
        self.navbar.addAction(legend)

        self._grid_action = grid
        self._minor_action = minor
        self._legend_action = legend

    def _init_menu(self) -> None:
        menu = self.menuBar()

        file_menu = menu.addMenu("File")
        open_act = QAction(OPEN_TEXT, self)
        open_act.triggered.connect(self.open_files)
        file_menu.addAction(open_act)

        export_act = QAction(EXPORT_TEXT, self)
        export_act.triggered.connect(self.export_plot)
        file_menu.addAction(export_act)

        view_menu = menu.addMenu("View")
        reset_act = QAction(RESET_TEXT, self)
        reset_act.triggered.connect(self.manager.reset_view)
        view_menu.addAction(reset_act)
        view_menu.addSeparator()
        view_menu.addAction(self._grid_action)
        view_menu.addAction(self._minor_action)
        view_menu.addAction(self._legend_action)

        change_axes_act = QAction("Change Axes…", self)
        change_axes_act.setShortcut("Ctrl+Shift+X")
        change_axes_act.triggered.connect(self.change_axes)
        view_menu.addAction(change_axes_act)

        help_menu = menu.addMenu("Help")
        about_act = QAction(ABOUT_TEXT, self)
        about_act.triggered.connect(self.show_about)
        help_menu.addAction(about_act)
        show_log_act = QAction("Show Log File", self)
        show_log_act.triggered.connect(self.show_log_file)
        help_menu.addAction(show_log_act)

    def open_files(self) -> None:
        try:
            paths = [Path(p) for p in pick_csv_files(self)]
            if not paths:
                return

            dataframes: list[pd.DataFrame] = []
            valid_paths: list[Path] = []
            for path in paths:
                try:
                    df = load_any(path)
                except Exception as exc:  # noqa: BLE001
                    errors.show_error(self, f"Failed to read {path.name}: {exc}")
                    continue
                dataframes.append(df)
                valid_paths.append(path)

            if not dataframes:
                return

            headers: set[str] = set()
            for df in dataframes:
                headers.update(df.columns)
            dialog = AxisMappingDialog(sorted(headers), self._last_x, self._last_y, self)
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return
            x_col, y_col = dialog.get_mapping()
            self._last_x, self._last_y = x_col, y_col

            self.manager.clear()
            for df, path in zip(dataframes, valid_paths):
                self.manager.add(path.stem, df)

            self.manager.set_axis_names(x_col, y_col)
            skipped = self.manager.replot_all()

            # Ensure legend is visible and UI state matches
            self._legend_action.setChecked(True)
            if hasattr(self.pane, "toggle_legend"):
                self.pane.toggle_legend(True)
            else:
                # Backward-compat if an earlier task created show_legend()
                self.pane.show_legend(True)

            if skipped:
                msg = QMessageBox(self)
                msg.setWindowTitle("Skipped Files")
                msg.setText("Some files were skipped:\n" + "\n".join(skipped))
                msg.setIcon(QMessageBox.Icon.Warning)
                msg.setModal(False)  # non-blocking
                msg.show()

        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to open files")
            QMessageBox.critical(self, "Error", str(exc))

    def change_axes(self) -> None:
        if not self.manager.datasets:
            return
        headers: set[str] = set()
        for ds in self.manager.datasets.values():
            headers.update(ds.df.columns)
        dialog = AxisMappingDialog(sorted(headers), self._last_x, self._last_y, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        x_col, y_col = dialog.get_mapping()
        self._last_x, self._last_y = x_col, y_col
        self.manager.set_axis_names(x_col, y_col)
        skipped = self.manager.replot_all()
        self.pane.show_legend(True)
        self._legend_action.setChecked(True)
        if skipped:
            msg = QMessageBox(self)
            msg.setWindowTitle("Skipped Files")
            msg.setText("Some files were skipped:\n" + "\n".join(skipped))
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setModal(False)
            msg.show()

    def export_plot(self) -> None:
        path_str, _ = QFileDialog.getSaveFileName(self, EXPORT_TEXT, "", PNG_FILTER)
        if path_str:
            self.manager.export_png(Path(path_str))

    def show_about(self) -> None:
        errors.show_info(self, ABOUT_MESSAGE, ABOUT_TEXT)

    def show_log_file(self) -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(LOG_FILE)))
