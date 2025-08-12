from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg

plt.style.use("dark_background")


class PlotPane(FigureCanvasQTAgg):
    """Matplotlib canvas for plotting dataframes."""

    def __init__(self, parent: Optional[object] = None) -> None:
        self.figure: Figure = Figure()
        super().__init__(self.figure)
        self.axes = self.figure.add_subplot(111)

    def clear(self) -> None:
        """Remove all plots from the canvas."""
        self.axes.cla()
        self.draw_idle()

    def plot_dataframe(
        self, df: pd.DataFrame, x: str, y: str, label: str, color: str | None = None
    ) -> None:
        """Plot a dataframe on the canvas."""
        self.axes.plot(df[x], df[y], label=label, color=color)
        self.draw_idle()

    def set_labels(self, xlabel: str, ylabel: str) -> None:
        """Set axes labels."""
        self.axes.set_xlabel(xlabel)
        self.axes.set_ylabel(ylabel)
        self.draw_idle()

    def export_png(self, path: Path) -> None:
        """Export the current figure to a PNG file."""
        self.figure.savefig(path, format="png", dpi=150)

    def autoscale(self) -> None:
        """Autoscale the axes and redraw."""
        self.axes.relim()
        self.axes.autoscale()
        self.draw_idle()

    def reset_view(self) -> None:
        """Reset the view to show all data."""
        self.autoscale()

    def toggle_grid(self, enabled: bool) -> None:
        """Toggle the grid visibility."""
        self.axes.grid(enabled)
        self.draw_idle()

    def show_legend(self, visible: bool) -> None:
        """Toggle legend visibility."""
        legend = self.axes.get_legend()
        if visible:
            self.axes.legend()
        elif legend:
            legend.remove()
        self.draw_idle()
