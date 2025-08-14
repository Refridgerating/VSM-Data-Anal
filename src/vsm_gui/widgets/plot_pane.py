from __future__ import annotations

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.artist import Artist
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.lines import Line2D
from matplotlib.axes import Axes

from ..utils.cursors import DraggableRegion, DraggableVLine

from pathlib import Path
from typing import Callable, Optional

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

        # Map of display label -> Line2D instance.  Display label is unique even
        # if the user supplies duplicate labels.  This allows the formatting
        # dialog to target a specific trace reliably.
        self._line_map: dict[str, Line2D] = {}

        self._annotation = None
        self._cursor_line: Line2D | None = None

        self._interactive: dict[str, object | list[Artist]] = {
            "ms_region": None,
            "hc_region": None,
            "mr_line": None,
            "markers": [],
            "regions": [],
        }

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

        for key in ("ms_region", "hc_region", "mr_line"):
            obj = self._interactive.get(key)
            if obj:
                obj.set_axes(self.axes)
                obj.set_visible(False)

        self.clear_markers()
        self.clear_regions()
        self.draw_idle()

    def plot_dataframe(
        self, df: pd.DataFrame, x: str, y: str, label: str, color: str | None = None
    ) -> None:
        """Plot a dataframe on the canvas."""
        # Ensure each line has a unique label for the legend / formatting table.
        base_label = label
        if base_label in self._line_map:
            idx = 2
            while f"{base_label} #{idx}" in self._line_map:
                idx += 1
            label = f"{base_label} #{idx}"
        (line,) = self.axes.plot(df[x], df[y], label=label, color=color)
        self._line_map[label] = line
        line.set_picker(True)
        if self._legend_on:
            self.axes.legend(loc="best")
        self.draw_idle()

    def set_labels(self, xlabel: str, ylabel: str) -> None:
        """Set axes labels."""
        self.axes.set_xlabel(xlabel)
        self.axes.set_ylabel(ylabel)
        self.draw_idle()

    # ------------------------------------------------------------------
    # API for formatting dialog
    # ------------------------------------------------------------------

    def get_axes(self) -> Axes:
        return self.axes

    def get_lines(self) -> list[Line2D]:
        return list(self._line_map.values())

    def set_title(self, title: str) -> None:
        self.axes.set_title(title)
        self.draw_idle()

    def set_limits(
        self,
        xmin: float | None,
        xmax: float | None,
        ymin: float | None,
        ymax: float | None,
        auto_x: bool,
        auto_y: bool,
    ) -> None:
        if auto_x:
            self.axes.autoscale(enable=True, axis="x", tight=False)
        else:
            self.axes.set_xlim(left=xmin, right=xmax)
        if auto_y:
            self.axes.autoscale(enable=True, axis="y", tight=False)
        else:
            self.axes.set_ylim(bottom=ymin, top=ymax)
        self.draw_idle()

    def set_scale(self, xscale: str, yscale: str) -> None:
        self.axes.set_xscale(xscale)
        self.axes.set_yscale(yscale)
        self.draw_idle()

    def set_grid(self, show: bool, minor: bool) -> None:
        self.toggle_grid(show)
        self.toggle_minor_ticks(minor)

    def set_tick_fontsize(self, size: int) -> None:
        for tick in self.axes.xaxis.get_major_ticks() + self.axes.yaxis.get_major_ticks():
            tick.label1.set_fontsize(size)
            tick.label2.set_fontsize(size)
        self.draw_idle()

    def set_label_fontsize(self, size: int) -> None:
        self.axes.xaxis.label.set_fontsize(size)
        self.axes.yaxis.label.set_fontsize(size)
        self.draw_idle()

    def set_legend(self, show: bool, loc: str, frame: bool, fontsize: int) -> None:
        legend = self.axes.get_legend()
        handles, labels = self.axes.get_legend_handles_labels()
        if show and handles:
            legend = self.axes.legend(loc=loc, frameon=frame, fontsize=fontsize)
        elif legend:
            legend.remove()
        self._legend_on = show
        self.draw_idle()

    def apply_trace_style(
        self,
        label: str,
        *,
        color=None,
        linewidth=None,
        marker=None,
        markersize=None,
    ) -> None:
        line = self._line_map.get(label)
        if not line:
            return
        if color is not None:
            line.set_color(color)
        if linewidth is not None:
            line.set_linewidth(float(linewidth))
        if marker is not None:
            line.set_marker(marker if marker != "None" else "")
        if markersize is not None:
            line.set_markersize(int(markersize))
        self.draw_idle()

    _RC_PRESETS: dict[str, dict] = {
        "Default": {},
        "Presentation": {
            "font.size": 14,
            "axes.titlesize": 16,
            "axes.labelsize": 14,
            "legend.fontsize": 12,
            "lines.linewidth": 1.5,
        },
        "Print (B/W)": {
            "lines.linewidth": 1.0,
            "axes.prop_cycle": plt.cycler(color=["black", "dimgray", "gray"]),
        },
        "Dark": {
            "axes.facecolor": "#222222",
            "figure.facecolor": "#222222",
            "axes.grid": True,
            "grid.color": "#888888",
        },
    }

    def apply_rc_preset(self, name: str) -> None:
        preset = self._RC_PRESETS.get(name, {})
        plt.rcParams.update(preset)
        self.draw_idle()

    # ------------------------------------------------------------------
    # Snapshot/restore helpers
    # ------------------------------------------------------------------

    def snapshot_style(self) -> dict:
        lines = {
            lbl: {
                "color": ln.get_color(),
                "linewidth": ln.get_linewidth(),
                "marker": ln.get_marker(),
                "markersize": ln.get_markersize(),
            }
            for lbl, ln in self._line_map.items()
        }
        legend = self.axes.get_legend()
        legend_state = None
        if legend:
            legend_state = {
                "loc": legend._loc,  # noqa: SLF001 - internal but fine
                "frameon": legend.get_frame_on(),
                "fontsize": legend.get_texts()[0].get_fontsize() if legend.get_texts() else 10,
                "visible": True,
            }
        else:
            legend_state = {"visible": False}
        return {
            "xlabel": self.axes.get_xlabel(),
            "ylabel": self.axes.get_ylabel(),
            "title": self.axes.get_title(),
            "xlim": self.axes.get_xlim(),
            "ylim": self.axes.get_ylim(),
            "xscale": self.axes.get_xscale(),
            "yscale": self.axes.get_yscale(),
            "grid": self._grid_on,
            "minor": self._minor_on,
            "tick_fs": self.axes.xaxis.get_ticklabels()[0].get_fontsize() if self.axes.xaxis.get_ticklabels() else 10,
            "label_fs": self.axes.xaxis.label.get_fontsize(),
            "legend": legend_state,
            "lines": lines,
        }

    def restore_style(self, state: dict) -> None:
        self.set_labels(state.get("xlabel", ""), state.get("ylabel", ""))
        self.set_title(state.get("title", ""))
        xlim = state.get("xlim")
        ylim = state.get("ylim")
        if xlim:
            self.axes.set_xlim(xlim)
        if ylim:
            self.axes.set_ylim(ylim)
        self.set_scale(state.get("xscale", "linear"), state.get("yscale", "linear"))
        self.set_grid(state.get("grid", True), state.get("minor", True))
        self.set_tick_fontsize(int(state.get("tick_fs", 10)))
        self.set_label_fontsize(int(state.get("label_fs", 10)))
        legend = state.get("legend", {})
        self.set_legend(
            legend.get("visible", False),
            legend.get("loc", "best"),
            legend.get("frameon", False),
            int(legend.get("fontsize", 10)),
        )
        for lbl, style in state.get("lines", {}).items():
            self.apply_trace_style(lbl, **style)
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

    # ------------------------------------------------------------------
    # Interactive helpers
    # ------------------------------------------------------------------
    def ensure_ms_region(
        self,
        x0: float | None = None,
        x1: float | None = None,
        on_changed: Callable[[float, float], None] | None = None,
        snap: bool = False,
    ) -> DraggableRegion:
        snap_fn = self.snap_to_nearest_x if snap else None
        region: DraggableRegion | None = self._interactive.get("ms_region")  # type: ignore[assignment]
        if region is None:
            region = DraggableRegion(
                self.axes,
                x0 or 0.0,
                x1 or 0.0,
                color="yellow",
                on_changed=on_changed,
                snap_fn=snap_fn,
            )
            self._interactive["ms_region"] = region
        else:
            region.set_axes(self.axes)
            if x0 is not None and x1 is not None:
                region.set_bounds(x0, x1)
            region.on_changed = on_changed  # type: ignore[attr-defined]
        region.set_visible(True)
        return region

    def ensure_hc_region(
        self,
        x0: float | None = None,
        x1: float | None = None,
        on_changed: Callable[[float, float], None] | None = None,
        snap: bool = False,
    ) -> DraggableRegion:
        snap_fn = self.snap_to_nearest_x if snap else None
        region: DraggableRegion | None = self._interactive.get("hc_region")  # type: ignore[assignment]
        if region is None:
            region = DraggableRegion(
                self.axes,
                x0 or -1.0,
                x1 or 1.0,
                color="cyan",
                on_changed=on_changed,
                snap_fn=snap_fn,
            )
            self._interactive["hc_region"] = region
        else:
            region.set_axes(self.axes)
            if x0 is not None and x1 is not None:
                region.set_bounds(x0, x1)
            region.on_changed = on_changed  # type: ignore[attr-defined]
        region.set_visible(True)
        return region

    def ensure_mr_line(
        self,
        x: float = 0.0,
        on_changed: Callable[[float], None] | None = None,
        snap: bool = False,
    ) -> DraggableVLine:
        snap_fn = self.snap_to_nearest_x if snap else None
        line: DraggableVLine | None = self._interactive.get("mr_line")  # type: ignore[assignment]
        if line is None:
            line = DraggableVLine(
                self.axes,
                x,
                color="magenta",
                on_changed=on_changed,
                snap_fn=snap_fn,
            )
            self._interactive["mr_line"] = line
        else:
            line.set_axes(self.axes)
            line.set_x(x)
            line.on_changed = on_changed
        line.set_visible(True)
        return line

    def clear_interactive(self, kind: str | None = None) -> None:
        keys = ["ms_region", "hc_region", "mr_line"] if kind is None else [kind]
        for k in keys:
            obj = self._interactive.get(k)
            if obj:
                obj.remove()
                self._interactive[k] = None
        if kind is None:
            self.clear_markers()
            self.clear_regions()

    def snap_to_nearest_x(self, x: float) -> float:
        best = x
        dist = float("inf")
        for line in self.get_lines():
            xs = line.get_xdata()
            if xs.size == 0:
                continue
            idx = int(np.argmin(np.abs(xs - x)))
            val = float(xs[idx])
            d = abs(val - x)
            if d < dist:
                dist = d
                best = val
        return best

    # ------------------------------------------------------------------
    # Marker helpers
    # ------------------------------------------------------------------
    def add_marker(self, x: float, y: float, label: str) -> list[Artist]:
        """Place a marker with a small text label."""
        (pt,) = self.axes.plot([x], [y], marker="o")
        txt = self.axes.annotate(
            label,
            xy=(x, y),
            xytext=(5, 5),
            textcoords="offset points",
        )
        self._interactive["markers"].extend([pt, txt])
        return [pt, txt]

    def add_vline(self, x: float, label: str | None = None) -> Artist:
        """Draw a vertical reference line."""
        line = self.axes.axvline(x, linestyle="--")
        self._interactive["markers"].append(line)
        if label:
            ylim = self.axes.get_ylim()
            txt = self.axes.text(x, ylim[1], label, va="bottom")
            self._interactive["markers"].append(txt)
        return line

    def add_hline(self, y: float, label: str | None = None) -> Artist:
        """Draw a horizontal reference line."""
        line = self.axes.axhline(y, linestyle="--")
        self._interactive["markers"].append(line)
        if label:
            xlim = self.axes.get_xlim()
            txt = self.axes.text(xlim[1], y, label, ha="left", va="center")
            self._interactive["markers"].append(txt)
        return line

    def clear_markers(self) -> None:
        """Remove any previously added markers/annotations."""
        for art in list(self._interactive["markers"]):
            try:
                art.remove()
            except Exception:  # noqa: BLE001
                pass
        self._interactive["markers"].clear()
        self.draw_idle()

    def shade_xrange(self, x0: float, x1: float, label: str | None = None) -> None:
        """Shade a range on the x-axis for visualising fit windows."""
        region = self.axes.axvspan(x0, x1, color="gray", alpha=0.2)
        self._interactive["regions"].append(region)
        if label:
            ylim = self.axes.get_ylim()
            txt = self.axes.text((x0 + x1) / 2, ylim[1], label, ha="center", va="bottom")
            self._interactive["regions"].append(txt)
        self.draw_idle()

    def clear_regions(self) -> None:
        """Remove previously shaded x-ranges."""
        for art in list(self._interactive["regions"]):
            try:
                art.remove()
            except Exception:  # noqa: BLE001
                pass
        self._interactive["regions"].clear()
        self.draw_idle()

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

    def show_legend(self, visible: bool) -> None:
        """Show or hide the legend."""
        self._legend_on = visible
        legend = self.axes.get_legend()
        handles, labels = self.axes.get_legend_handles_labels()
        if visible and handles:
            self.axes.legend(loc="best")
        elif legend:
            legend.remove()
        self.draw_idle()

    def toggle_legend(self, visible: bool) -> None:
        """Backward-compatible wrapper for :meth:`show_legend`."""
        self.show_legend(visible)

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
