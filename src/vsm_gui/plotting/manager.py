from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple, List


import matplotlib
import numpy as np
import pandas as pd

from ..widgets.plot_pane import PlotPane


class PlotManager:
    """Manage plotting of multiple datasets on a single axes."""

    def __init__(self, pane: PlotPane) -> None:
        self.pane = pane
        self.datasets: Dict[str, pd.DataFrame] = {}
        cycle = matplotlib.rcParams["axes.prop_cycle"].by_key()
        self._colors = cycle.get("color", [])
        self._index = 0
        self._x_name: str | None = None
        self._y_name: str | None = None

    def _next_color(self) -> str | None:
        if not self._colors:
            return None
        color = self._colors[self._index % len(self._colors)]
        self._index += 1
        return color

    def clear(self) -> None:
        """Clear all datasets and reset the plot."""
        self.datasets.clear()
        self._index = 0
        self.pane.clear()

    def add(self, label: str, df: pd.DataFrame) -> None:
        """Store a dataframe for plotting."""
        self.datasets[label] = df

def set_axis_names(self, x_name: str, y_name: str) -> None:
    """Record the axis column names to use for plotting and update labels."""
    self._x_name = x_name
    self._y_name = y_name
    self.pane.set_labels(x_name, y_name)

def set_labels(self, xlabel: str, ylabel: str) -> None:
    """Backward-compatible wrapper: updates stored axis names and labels."""
    # Keep legacy callers working, but route to the canonical API
    self.set_axis_names(xlabel, ylabel)

def replot_all(self) -> List[str]:
    """Rebuild the figure using stored datasets and axis names.

    Returns a list of warning messages for datasets that could not be plotted.
    """
    import numpy as np
    import pandas as pd

    self.pane.clear()
    skipped: List[str] = []

    if self._x_name is None or self._y_name is None:
        return skipped

    for label, df in self.datasets.items():
        if self._x_name not in df.columns or self._y_name not in df.columns:
            skipped.append(
                f"{label}: missing column '{self._x_name}' or '{self._y_name}'"
            )
            continue

        x = pd.to_numeric(df[self._x_name], errors="coerce")
        y = pd.to_numeric(df[self._y_name], errors="coerce")
        clean = (
            pd.DataFrame({self._x_name: x, self._y_name: y})
            .replace([np.inf, -np.inf], pd.NA)
            .dropna()
        )
        if len(clean) < 2:
            skipped.append(f"{label}: not enough valid data")
            continue

        color = self._next_color()
        self.pane.plot_dataframe(clean, self._x_name, self._y_name, label, color=color)

    self.reset_view()
    return skipped

    def get_axis_names(self) -> tuple[str | None, str | None]:
        """Return currently active axis names."""
        return self._x_name, self._y_name

    def get_datasets(self) -> List[dict]:
        """Return list of datasets with labels and dataframes."""
        items: List[dict] = []
        for label, (df, _x, _y) in self.datasets.items():
            items.append({"label": label, "df": df})
        return items

    def export_png(self, path: Path) -> None:
        """Export the current figure as a PNG file."""
        self.pane.export_png(path)

    def reset_view(self) -> None:
        """Reset the axes limits."""
        self.pane.reset_view()
