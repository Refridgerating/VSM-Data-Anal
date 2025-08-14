import pandas as pd
import os
from PyQt6.QtWidgets import QApplication

from vsm_gui.widgets.plot_pane import PlotPane


def _get_app():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    os.environ.setdefault("DISPLAY", ":0")
    try:
        import matplotlib._c_internal_utils as _u
        _u.display_is_valid = lambda: True  # type: ignore[attr-defined]
    except Exception:  # pragma: no cover - best effort
        pass
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_trace_style_and_axes_updates():
    _get_app()
    pane = PlotPane()
    df = pd.DataFrame({"x": [1, 2, 3, 4], "y": [1, 4, 9, 16]})
    pane.plot_dataframe(df, "x", "y", "trace1")

    pane.apply_trace_style("trace1", linewidth=2.5, color="red", marker="o", markersize=8)
    line = pane.get_lines()[0]
    assert line.get_linewidth() == 2.5
    assert line.get_color() == "red"
    assert line.get_marker() == "o"
    assert line.get_markersize() == 8

    pane.set_limits(0, 5, 0.5, 20, False, False)
    ax = pane.get_axes()
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    assert xlim[0] == 0 and xlim[1] == 5
    assert ylim[0] == 0.5 and ylim[1] == 20

    pane.set_scale("linear", "log")
    assert ax.get_yscale() == "log"

    pane.set_legend(True, "upper left", False, 10)
    assert ax.get_legend() is not None
    pane.set_legend(False, "upper left", False, 10)
    assert ax.get_legend() is None
