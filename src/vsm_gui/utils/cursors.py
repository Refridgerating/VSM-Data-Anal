from __future__ import annotations

"""Interactive matplotlib helpers for draggable lines and regions."""

from typing import Callable

from matplotlib.axes import Axes
from matplotlib.lines import Line2D


class DraggableVLine:
    """A draggable vertical line with an optional top handle."""

    def __init__(
        self,
        ax: Axes,
        x: float,
        label: str | None = None,
        color: str | None = None,
        on_changed: Callable[[float], None] | None = None,
        snap_fn: Callable[[float], float] | None = None,
    ) -> None:
        self.ax = ax
        self.canvas = ax.figure.canvas
        self.color = color or "orange"
        self.on_changed = on_changed
        self.snap_fn = snap_fn
        self._press = False
        self._visible = True
        self.x = x
        self.line: Line2D = ax.axvline(x, color=self.color, linestyle="--")
        ymax = ax.get_ylim()[1]
        (self.handle,) = ax.plot([x], [ymax], marker="s", color=self.color, zorder=5)
        self._cid_press = self.canvas.mpl_connect("button_press_event", self._on_press)
        self._cid_move = self.canvas.mpl_connect("motion_notify_event", self._on_move)
        self._cid_release = self.canvas.mpl_connect("button_release_event", self._on_release)

    # ------------------------------------------------------------------
    def detach(self) -> None:
        self.canvas.mpl_disconnect(self._cid_press)
        self.canvas.mpl_disconnect(self._cid_move)
        self.canvas.mpl_disconnect(self._cid_release)

    # ------------------------------------------------------------------
    def remove(self) -> None:
        try:
            self.line.remove()
            self.handle.remove()
        except Exception:  # noqa: BLE001
            pass
        self.detach()

    # ------------------------------------------------------------------
    def set_axes(self, ax: Axes) -> None:
        """Reattach to a new Axes after replot."""
        self.detach()
        self.ax = ax
        self.canvas = ax.figure.canvas
        self.line = ax.axvline(self.x, color=self.color, linestyle="--", visible=self._visible)
        ymax = ax.get_ylim()[1]
        (self.handle,) = ax.plot([self.x], [ymax], marker="s", color=self.color, zorder=5, visible=self._visible)
        self._cid_press = self.canvas.mpl_connect("button_press_event", self._on_press)
        self._cid_move = self.canvas.mpl_connect("motion_notify_event", self._on_move)
        self._cid_release = self.canvas.mpl_connect("button_release_event", self._on_release)

    # ------------------------------------------------------------------
    def set_visible(self, visible: bool) -> None:
        self._visible = visible
        self.line.set_visible(visible)
        self.handle.set_visible(visible)
        self.canvas.draw_idle()

    # ------------------------------------------------------------------
    def set_x(self, x: float) -> None:
        self.x = x
        self.line.set_xdata([x, x])
        ymax = self.ax.get_ylim()[1]
        self.handle.set_data([x], [ymax])
        self.canvas.draw_idle()

    def get_x(self) -> float:
        return float(self.x)

    # event handlers ----------------------------------------------------
    def _on_press(self, event) -> None:  # type: ignore[override]
        if event.inaxes != self.ax or event.button != 1:
            return
        self._press = True

    def _on_move(self, event) -> None:  # type: ignore[override]
        if not self._press or event.inaxes != self.ax or event.xdata is None:
            return
        x = float(event.xdata)
        if self.snap_fn:
            x = float(self.snap_fn(x))
        xmin, xmax = self.ax.get_xlim()
        x = max(min(x, xmax), xmin)
        self.set_x(x)

    def _on_release(self, event) -> None:  # type: ignore[override]
        if not self._press:
            return
        self._press = False
        if self.on_changed:
            self.on_changed(self.get_x())
        self.canvas.draw_idle()


class DraggableRegion:
    """Two draggable vertical lines with a shaded span between them."""

    def __init__(
        self,
        ax: Axes,
        x0: float,
        x1: float,
        color: str | None = None,
        on_changed: Callable[[float, float], None] | None = None,
        snap_fn: Callable[[float], float] | None = None,
    ) -> None:
        self.ax = ax
        self.color = color or "cyan"
        self.on_changed = on_changed
        self.snap_fn = snap_fn
        self.left = DraggableVLine(ax, x0, color=self.color, on_changed=self._callback, snap_fn=snap_fn)
        self.right = DraggableVLine(ax, x1, color=self.color, on_changed=self._callback, snap_fn=snap_fn)
        xlo, xhi = sorted([x0, x1])
        self.span = ax.axvspan(xlo, xhi, color=self.color, alpha=0.2)
        self._visible = True

    # ------------------------------------------------------------------
    def _callback(self, _x: float) -> None:
        self._update_span()
        if self.on_changed:
            x0, x1 = self.get_bounds()
            self.on_changed(x0, x1)

    # ------------------------------------------------------------------
    def detach(self) -> None:
        self.left.detach()
        self.right.detach()

    def remove(self) -> None:
        try:
            self.span.remove()
        except Exception:  # noqa: BLE001
            pass
        self.left.remove()
        self.right.remove()

    # ------------------------------------------------------------------
    def set_axes(self, ax: Axes) -> None:
        self.ax = ax
        self.left.set_axes(ax)
        self.right.set_axes(ax)
        x0, x1 = self.get_bounds()
        self.span = ax.axvspan(x0, x1, color=self.color, alpha=0.2, visible=self._visible)

    # ------------------------------------------------------------------
    def set_visible(self, visible: bool) -> None:
        self._visible = visible
        self.left.set_visible(visible)
        self.right.set_visible(visible)
        self.span.set_visible(visible)
        self.ax.figure.canvas.draw_idle()

    # ------------------------------------------------------------------
    def get_bounds(self) -> tuple[float, float]:
        x0 = self.left.get_x()
        x1 = self.right.get_x()
        if x0 > x1:
            x0, x1 = x1, x0
        return x0, x1

    def set_bounds(self, x0: float, x1: float) -> None:
        self.left.set_x(x0)
        self.right.set_x(x1)
        self._update_span()

    # ------------------------------------------------------------------
    def _update_span(self) -> None:
        x0, x1 = self.get_bounds()
        self.span.remove()
        self.span = self.ax.axvspan(x0, x1, color=self.color, alpha=0.2, visible=self._visible)


