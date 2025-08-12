from __future__ import annotations

from pathlib import Path

import pandas as pd
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

from .file_io.loader import read_csv
from .plotting.manager import PlotManager
from .utils import errors
from .utils.logging import LOG_FILE, logger
from .widgets.axis_mapping import AxisMappingDialog
from .widgets.file_picker import pick_csv_files
from .widgets.plot_pane import PlotPane
from .widgets.analysis_panel import AnalysisDock

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
        grid.triggered.connect(self.pane.toggle_grid)
        self.navbar.addAction(grid)

        legend = QAction("Legend", self)
        legend.setCheckable(True)
        legend.setChecked(True)
        legend.triggered.connect(self.pane.show_legend)
        self.navbar.addAction(legend)
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
                    df = read_csv(path)
                except Exception as exc:  # noqa: BLE001
                    errors.show_error(self, f"Failed to read {path.name}: {exc}")
                    continue
                dataframes.append(df)
                valid_paths.append(path)

            if not dataframes:
                return

            headers = list(dataframes[0].columns)
            dialog = AxisMappingDialog(headers, self._last_x, self._last_y, self)
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return
            x_col, y_col = dialog.get_mapping()
            self._last_x, self._last_y = x_col, y_col

            self.manager.clear()
            for df, path in zip(dataframes, valid_paths):
                if x_col not in df.columns or y_col not in df.columns:
                    errors.show_error(
                        self,
                        f"{path.name} missing column '{x_col}' or '{y_col}'",
                        title="Missing Column",
                    )
                    continue
                self.manager.add(path.stem, df, x_col, y_col)

            self.manager.set_labels(x_col, y_col)
            self.pane.show_legend(True)
            self._legend_action.setChecked(True)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to open files")
            QMessageBox.critical(self, "Error", str(exc))

    def export_plot(self) -> None:
        path_str, _ = QFileDialog.getSaveFileName(self, EXPORT_TEXT, "", PNG_FILTER)
        if path_str:
            self.manager.export_png(Path(path_str))

    def show_about(self) -> None:
        errors.show_info(self, ABOUT_MESSAGE, ABOUT_TEXT)

    def show_log_file(self) -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(LOG_FILE)))
