from __future__ import annotations

import matplotlib
import numpy as np
import pandas as pd

from ..model import Dataset
from ..widgets.plot_pane import PlotPane

from pathlib import Path
from typing import Dict, List


class PlotManager:
    """Manage plotting of multiple datasets on a single axes."""

    def __init__(self, pane: PlotPane) -> None:
        self.pane = pane
        # Mapping of label -> Dataset
        self.datasets: Dict[str, Dataset] = {}
        # Cache of original datasets for temporary modifications
        self._original_cache: Dict[str, Dataset] = {}

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
        self._original_cache.clear()
        self._index = 0
        self.pane.clear()

    def add(self, label: str, df: pd.DataFrame) -> None:
        """Store a dataframe for plotting."""
        self.datasets[label] = Dataset(label, df)

    def add_dataset(self, dataset: Dataset) -> None:
        """Add a pre-built Dataset object."""
        self.datasets[dataset.label] = dataset

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

        for label, ds in self.datasets.items():
            x_col = ds.x_name or self._x_name
            y_col = ds.y_name or self._y_name
            if x_col is None or y_col is None:
                continue
            try:
                clean = ds.select_xy(x_col, y_col)
            except KeyError:
                skipped.append(
                    f"{label}: missing column '{x_col}' or '{y_col}'"
                )
                continue
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

    def get_dataset_tuple(self, label: str) -> tuple[pd.DataFrame, str, str]:
        """Return ``(df, x_name, y_name)`` for *label* regardless of storage format.

        This accessor handles both the modern :class:`Dataset` objects and the
        legacy ``(df, x, y, ...)`` tuples.  Axis names stored on the Dataset take
        precedence, but fall back to the manager's active axis names.  A
        :class:`ValueError` is raised if the label is unknown or the axis names
        cannot be determined.
        """

        if label not in self.datasets:
            raise ValueError(f"Unknown dataset label: {label}")

        ds = self.datasets[label]

        # Dataset objects -------------------------------------------------
        if isinstance(ds, Dataset):
            x_name = ds.x_name or self._x_name
            y_name = ds.y_name or self._y_name
            if x_name is None or y_name is None:
                raise ValueError(f"Axis names not set for dataset '{label}'")
            return ds.df, x_name, y_name

        # Legacy tuple-based storage --------------------------------------
        if isinstance(ds, (tuple, list)):
            if len(ds) < 1:
                raise ValueError(f"Dataset tuple for '{label}' is empty")
            df = ds[0]
            x_name = ds[1] if len(ds) > 1 else None
            y_name = ds[2] if len(ds) > 2 else None
            x_name = x_name or self._x_name
            y_name = y_name or self._y_name
            if x_name is None or y_name is None:
                raise ValueError(f"Axis names not set for dataset '{label}'")
            if not isinstance(df, pd.DataFrame):
                raise ValueError(
                    f"First element of dataset '{label}' is not a DataFrame"
                )
            return df, x_name, y_name

        # Unknown type ----------------------------------------------------
        raise ValueError(
            f"Unsupported dataset type for '{label}': {type(ds).__name__}"
        )

    # ------------------------------------------------------------------
    # Corrected data handling
    # ------------------------------------------------------------------
    def replace_dataset(
        self, label: str, df_corr: pd.DataFrame, x_name: str, y_corr_name: str
    ) -> None:
        """Replace the dataset *label* with corrected data.

        The original dataset is cached so that it can be restored via
        :meth:`revert_dataset` later in the session.
        """
        if label not in self.datasets:
            raise ValueError(f"Unknown dataset label: {label}")

        # Cache original before replacing
        if label not in self._original_cache:
            self._original_cache[label] = self.datasets[label]

        # Overwrite dataset with corrected version
        self.datasets[label] = Dataset(
            label, df_corr, x_name=x_name, y_name=y_corr_name
        )
        self._replot_all()

    def revert_dataset(self, label: str) -> None:
        """Restore the original dataset for *label* if a corrected one exists."""
        original = self._original_cache.pop(label, None)
        if original is not None:
            self.datasets[label] = original
            self._replot_all()

    def is_corrected(self, label: str) -> bool:
        """Return ``True`` if *label* currently refers to a corrected dataset."""
        return label in self._original_cache

    # Internal utilities -------------------------------------------------
    def _replot_all(self) -> None:
        """Replot all datasets, used after removing a curve."""
        self.pane.clear()
        self._index = 0
        for lbl, ds in self.datasets.items():
            x_col = ds.x_name or self._x_name
            y_col = ds.y_name or self._y_name
            if x_col is None or y_col is None:
                continue
            color = self._next_color()
            self.pane.plot_dataframe(ds.df, x_col, y_col, lbl, color=color)

    def get_datasets(self) -> List[dict]:
        """Return list of datasets with labels and dataframes."""
        items: List[dict] = []
        for label, ds in self.datasets.items():
            if isinstance(ds, Dataset):
                df = ds.df
            elif isinstance(ds, (tuple, list)):
                if not ds:
                    continue
                df = ds[0]
                if not isinstance(df, pd.DataFrame):
                    continue
            else:
                continue
            items.append({"label": label, "df": df})
        return items

    def export_png(self, path: Path) -> None:
        """Export the current figure as a PNG file."""
        self.pane.export_png(path)

    def reset_view(self) -> None:
        """Reset the axes limits."""
        self.pane.reset_view()

    def clear_markers(self) -> None:
        """Remove any marker annotations from the plot."""
        self.pane.clear_markers()

