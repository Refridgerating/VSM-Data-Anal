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
        # Mapping of label -> (dataframe, x column, y column)
        self.datasets: Dict[str, Tuple[pd.DataFrame, str, str]] = {}
        # Track which original label has an associated corrected curve
        self.corrected_map: Dict[str, str] = {}
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
        self.corrected_map.clear()
        self._index = 0
        self.pane.clear()

    def add(self, label: str, df: pd.DataFrame, x: str, y: str) -> None:
        """Add a dataframe to the plot."""
        color = self._next_color()
        self.datasets[label] = (df, x, y)
        self.pane.plot_dataframe(df, x, y, label, color=color)

    # ------------------------------------------------------------------
    # Corrected data handling
    # ------------------------------------------------------------------
    def add_corrected(
        self, label: str, df_corr: pd.DataFrame, x_name: str, y_corr_name: str
    ) -> None:
        """Add a corrected dataset to the plot.

        Parameters
        ----------
        label : str
            Base label of the original dataset.
        df_corr : DataFrame
            Corrected dataframe.
        x_name : str
            X column name.
        y_corr_name : str
            Corrected Y column name.
        """
        corrected_label = f"{label} (corrected)"
        if corrected_label in self.datasets:
            # Replace existing corrected dataset
            self.remove_corrected(label)
        self.datasets[corrected_label] = (df_corr, x_name, y_corr_name)
        self.corrected_map[label] = corrected_label
        color = self._next_color()
        self.pane.plot_dataframe(df_corr, x_name, y_corr_name, corrected_label, color=color)

    def remove_corrected(self, label: str) -> None:
        """Remove a corrected dataset associated with ``label``."""
        corrected_label = self.corrected_map.pop(label, None)
        if corrected_label and corrected_label in self.datasets:
            del self.datasets[corrected_label]
            self._replot_all()

    # Internal utilities -------------------------------------------------
    def _replot_all(self) -> None:
        """Replot all datasets, used after removing a curve."""
        self.pane.clear()
        self._index = 0
        for lbl, (df, x, y) in self.datasets.items():
            color = self._next_color()
            self.pane.plot_dataframe(df, x, y, lbl, color=color)

    def set_labels(self, xlabel: str, ylabel: str) -> None:
        """Set axes labels."""
        self.pane.set_labels(xlabel, ylabel)

    def export_png(self, path: Path) -> None:
        """Export the current figure as a PNG file."""
        self.pane.export_png(path)

    def reset_view(self) -> None:
        """Reset the axes limits."""
        self.pane.reset_view()
