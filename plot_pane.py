from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class PlotPane(QWidget):
    """Simple wrapper around a matplotlib canvas."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)

    def plot(self, df, x: str, y: str) -> None:
        """Plot a DataFrame using the provided column names."""
        self.ax.plot(df[x], df[y])
        self.ax.set_xlabel(x)
        self.ax.set_ylabel(y)
        self.figure.tight_layout()
        self.canvas.draw_idle()
