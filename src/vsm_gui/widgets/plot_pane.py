from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.lines import Line2D

plt.style.use("dark_background")
plt.rcParams.update({"font.size": 10, "grid.alpha": 0.3})


class PlotPane(FigureCanvasQTAgg):
    """Matplotlib canvas for plotting dataframes."""

    def __init__(self, parent: Optional[object] = None) -> None:
        self.figure: Figure = Figure()
        super().__init__(self.figure)
        self.axes = self.figure.add_subplot(111)

        self._grid_on = True
        self._minor_on = True
        self._legend_on = True

        self._annotation = None
        self._cursor_line: Line2D | None = None

        self.toggle_grid(True)
        self.toggle_minor_ticks(True)
        self.enable_data_cursor()

    def clear(self) -> None:
        """Remove all plots from the canvas."""
        self.axes.cla()
        self.toggle_grid(self._grid_on)
        self.toggle_minor_ticks(self._minor_on)
        self._annotation = None
        self._cursor_line = None
        self.draw_idle()

    def plot_dataframe(
        self, df: pd.DataFrame, x: str, y: str, label: str, color: str | None = None
    ) -> None:
        """Plot a dataframe on the canvas."""
        (line,) = self.axes.plot(df[x], df[y], label=label, color=color)
        line.set_picker(True)
        if self._legend_on:
            self.axes.legend(loc="best")
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
        self._grid_on = enabled
        self.axes.grid(enabled, which="both")
        self.draw_idle()

    def toggle_minor_ticks(self, enabled: bool) -> None:
        """Toggle minor ticks on both axes."""
        self._minor_on = enabled
        if enabled:
            self.axes.minorticks_on()
        else:
            self.axes.minorticks_off()
        if self._grid_on:
            self.axes.grid(self._grid_on, which="both")
        self.draw_idle()

    def toggle_legend(self, visible: bool) -> None:
        """Toggle legend visibility."""
        self._legend_on = visible
        legend = self.axes.get_legend()
        handles, labels = self.axes.get_legend_handles_labels()
        if visible and handles:
            self.axes.legend(loc="best")
        elif legend:
            legend.remove()
        self.draw_idle()

    def enable_data_cursor(self) -> None:
        """Enable a simple data cursor."""
        self.mpl_connect("pick_event", self._on_pick)
        self.mpl_connect("motion_notify_event", self._on_motion)

    def _on_pick(self, event) -> None:
        if event.mouseevent.button != 1 or not isinstance(event.artist, Line2D):
            return
        line: Line2D = event.artist
        if self._annotation and line is self._cursor_line:
            self._annotation.remove()
            self._annotation = None
            self._cursor_line = None
            self.draw_idle()
            return
        xdata, ydata = line.get_data()
        ind = event.ind[0]
        x, y = xdata[ind], ydata[ind]
        if self._annotation:
            self._annotation.remove()
        self._cursor_line = line
        self._annotation = self.axes.annotate(
            f"({x:.2f}, {y:.2f})",
            xy=(x, y),
            xytext=(10, 10),
            textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.3", fc=plt.rcParams["axes.facecolor"], alpha=0.8),
        )
        self.draw_idle()

    def _on_motion(self, event) -> None:
        if not self._annotation or not self._cursor_line or event.inaxes != self.axes:
            return
        x = event.xdata
        if x is None:
            return
        xdata, ydata = self._cursor_line.get_data()
        idx = int(np.argmin(np.abs(xdata - x)))
        x0, y0 = xdata[idx], ydata[idx]
        self._annotation.xy = (x0, y0)
        self._annotation.set_text(f"({x0:.2f}, {y0:.2f})")
        self.draw_idle()
