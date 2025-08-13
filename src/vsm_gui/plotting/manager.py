from __future__ import annotations

import matplotlib
import numpy as np
import pandas as pd

from ..widgets.plot_pane import PlotPane

from pathlib import Path
from typing import Dict, List, Tuple, Union


class PlotManager:
    """Manage plotting of multiple datasets on a single axes."""

    def __init__(self, pane: PlotPane) -> None:
        self.pane = pane
        # Mapping of label -> dataframe or (df, x_name, y_name)
        self.datasets: Dict[
            str, Union[pd.DataFrame, Tuple[pd.DataFrame, str, str]]
        ] = {}
        # Track which original label has an associated corrected curve
        self.corrected_map: Dict[str, str] = {}

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
        self.corrected_map.clear()
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
        self.set_axis_names(xlabel, ylabel)

    def replot_all(self) -> List[str]:
        """Rebuild the figure using stored datasets and axis names.

        Returns a list of warning messages for datasets that could not be plotted.
        """
        self.pane.clear()
        skipped: List[str] = []

        if self._x_name is None or self._y_name is None:
            return skipped

        for label, data in self.datasets.items():
            if isinstance(data, tuple):
                df, x_col, y_col = data
            else:
                df = data
                x_col = self._x_name
                y_col = self._y_name
            if x_col is None or y_col is None:
                continue
            if x_col not in df.columns or y_col not in df.columns:
                skipped.append(
                    f"{label}: missing column '{x_col}' or '{y_col}'"
                )
                continue

            x = pd.to_numeric(df[x_col], errors="coerce")
            y = pd.to_numeric(df[y_col], errors="coerce")
            clean = (
                pd.DataFrame({x_col: x, y_col: y})
                .replace([np.inf, -np.inf], pd.NA)
                .dropna()
            )
            if len(clean) < 2:
                skipped.append(f"{label}: not enough valid data")
                continue

            color = self._next_color()
            self.pane.plot_dataframe(clean, x_col, y_col, label, color=color)

        self.reset_view()
        return skipped

    def get_axis_names(self) -> tuple[str | None, str | None]:
        """Return currently active axis names."""
        return self._x_name, self._y_name

    # ------------------------------------------------------------------
    # Corrected data handling
    # ------------------------------------------------------------------
    def add_corrected(
        self, label: str, df_corr: pd.DataFrame, x_name: str, y_corr_name: str
    ) -> None:
        """Add a corrected dataset to the plot."""
        corrected_label = f"{label} (corrected)"
        if corrected_label in self.datasets:
            # Replace existing corrected dataset
            self.remove_corrected(label)
        self.datasets[corrected_label] = (df_corr, x_name, y_corr_name)
        self.corrected_map[label] = corrected_label
        color = self._next_color()
        self.pane.plot_dataframe(
            df_corr, x_name, y_corr_name, corrected_label, color=color
        )

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
        for lbl, data in self.datasets.items():
            if isinstance(data, tuple):
                df, x_col, y_col = data
            else:
                df = data
                x_col = self._x_name
                y_col = self._y_name
            if x_col is None or y_col is None:
                continue
            color = self._next_color()
            self.pane.plot_dataframe(df, x_col, y_col, lbl, color=color)

    def get_datasets(self) -> List[dict]:
        """Return list of datasets with labels and dataframes."""
        items: List[dict] = []
        for label, data in self.datasets.items():
            df = data[0] if isinstance(data, tuple) else data
            items.append({"label": label, "df": df})
        return items

    def export_png(self, path: Path) -> None:
        """Export the current figure as a PNG file."""
        self.pane.export_png(path)

    def reset_view(self) -> None:
        """Reset the axes limits."""
        self.pane.reset_view()

