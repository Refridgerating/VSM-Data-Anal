from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple

import matplotlib
import pandas as pd

from ..widgets.plot_pane import PlotPane


class PlotManager:
    """Manage plotting of multiple datasets on a single axes."""

    def __init__(self, pane: PlotPane) -> None:
        self.pane = pane
        self.datasets: Dict[str, Tuple[pd.DataFrame, str, str]] = {}
        cycle = matplotlib.rcParams["axes.prop_cycle"].by_key()
        self._colors = cycle.get("color", [])
        self._index = 0

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

    def add(self, label: str, df: pd.DataFrame, x: str, y: str) -> None:
        """Add a dataframe to the plot."""
        color = self._next_color()
        self.datasets[label] = (df, x, y)
        self.pane.plot_dataframe(df, x, y, label, color=color)

    def set_labels(self, xlabel: str, ylabel: str) -> None:
        """Set axes labels."""
        self.pane.set_labels(xlabel, ylabel)

    def export_png(self, path: Path) -> None:
        """Export the current figure as a PNG file."""
        self.pane.export_png(path)

    def reset_view(self) -> None:
        """Reset the axes limits."""
        self.pane.reset_view()
