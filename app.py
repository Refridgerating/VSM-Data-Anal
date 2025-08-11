from __future__ import annotations

from pathlib import Path
from typing import List

import pandas as pd
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QAction, QActionGroup
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QInputDialog,
    QMainWindow,
    QMenu,
    QMessageBox,
    QSplitter,
)

from plot_pane import PlotPane


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("VSM Data Analyzer")

        self.settings = QSettings("VSM", "DataAnal")
        self.layout_mode = self.settings.value("layout_mode", "Superimposed")

        self.dataframes: List[pd.DataFrame] = []
        self.paths: List[Path] = []
        self.x_col: str | None = None
        self.y_col: str | None = None

        self._build_menus()
        self.statusBar().showMessage("Ready")

    # ------------------------------------------------------------------
    def _build_menus(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        open_action = QAction("Open Files...", self)
        open_action.triggered.connect(self.open_files)
        file_menu.addAction(open_action)

        view_menu = self.menuBar().addMenu("&View")
        layout_menu = QMenu("Layout", self)
        view_menu.addMenu(layout_menu)

        self.super_action = QAction("Superimposed", self, checkable=True)
        self.side_action = QAction("Side-by-Side", self, checkable=True)
        group = QActionGroup(self)
        group.setExclusive(True)
        group.addAction(self.super_action)
        group.addAction(self.side_action)
        layout_menu.addActions([self.super_action, self.side_action])

        self.super_action.triggered.connect(lambda: self.set_layout("Superimposed"))
        self.side_action.triggered.connect(lambda: self.set_layout("Side-by-Side"))

        # reflect current mode
        if self.layout_mode == "Side-by-Side":
            self.side_action.setChecked(True)
        else:
            self.super_action.setChecked(True)

    # ------------------------------------------------------------------
    def set_layout(self, mode: str) -> None:
        if mode not in {"Superimposed", "Side-by-Side"}:
            return
        self.layout_mode = mode
        self.settings.setValue("layout_mode", mode)
        self.update_plot()

    # ------------------------------------------------------------------
    def open_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, "Open Data Files", "", "CSV Files (*.csv);;All Files (*)")
        if not paths:
            return
        for path in paths:
            try:
                df = pd.read_csv(path)
            except Exception as exc:  # pragma: no cover - for robustness
                self._non_blocking_warning(f"Failed to open {path}: {exc}")
                continue
            self.dataframes.append(df)
            self.paths.append(Path(path))

        if self.x_col is None or self.y_col is None:
            self.choose_columns()
        self.update_plot()

    # ------------------------------------------------------------------
    def choose_columns(self) -> None:
        if not self.dataframes:
            return
        cols = list(self.dataframes[0].columns)
        x, ok = QInputDialog.getItem(self, "Select X axis", "X column:", cols, 0, False)
        if not ok:
            return
        y, ok = QInputDialog.getItem(self, "Select Y axis", "Y column:", cols, 1, False)
        if not ok:
            return
        self.x_col, self.y_col = str(x), str(y)

    # ------------------------------------------------------------------
    def _non_blocking_warning(self, text: str) -> None:
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("Warning")
        msg.setText(text)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.setWindowModality(Qt.WindowModality.NonModal)
        msg.show()
        self.statusBar().showMessage(text, 5000)

    # ------------------------------------------------------------------
    def update_plot(self) -> None:
        if not self.dataframes or not self.x_col or not self.y_col:
            return

        if self.centralWidget():
            self.centralWidget().deleteLater()

        if self.layout_mode == "Superimposed":
            pane = PlotPane(self)
            for df, path in zip(self.dataframes, self.paths):
                if self.x_col in df.columns and self.y_col in df.columns:
                    pane.plot(df, self.x_col, self.y_col)
                else:
                    self._non_blocking_warning(f"{path.name} missing {self.x_col}/{self.y_col}")
            self.setCentralWidget(pane)
        else:  # Side-by-Side
            splitter = QSplitter(Qt.Orientation.Horizontal, self)
            for df, path in zip(self.dataframes, self.paths):
                if self.x_col in df.columns and self.y_col in df.columns:
                    pane = PlotPane(self)
                    pane.plot(df, self.x_col, self.y_col)
                    splitter.addWidget(pane)
                else:
                    self._non_blocking_warning(f"{path.name} missing {self.x_col}/{self.y_col}")
            self.setCentralWidget(splitter)


if __name__ == "__main__":  # pragma: no cover - manual run
    import sys

    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
