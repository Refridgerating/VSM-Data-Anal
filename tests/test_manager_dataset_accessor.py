import sys
import types

import pandas as pd

import vsm_gui  # ensure package is loaded

# Provide stub PlotPane to avoid importing Qt/Matplotlib heavy deps
plot_pane_stub = types.ModuleType("plot_pane")


class PlotPane:  # minimal placeholder
    pass


plot_pane_stub.PlotPane = PlotPane
sys.modules.setdefault("vsm_gui.widgets.plot_pane", plot_pane_stub)

from vsm_gui.plotting.manager import PlotManager
from vsm_gui.model import Dataset


class DummyPane:
    def clear(self):
        pass

    def plot_dataframe(self, *args, **kwargs):
        pass

    def set_labels(self, *args, **kwargs):
        pass

    def export_png(self, *args, **kwargs):
        pass

    def reset_view(self):
        pass

    axes = None


def test_get_dataset_tuple_from_tuple():
    pane = DummyPane()
    mgr = PlotManager(pane)
    df = pd.DataFrame({"x": [1, 2], "y": [3, 4]})
    mgr.datasets["t"] = (df, "x", "y")
    got_df, x, y = mgr.get_dataset_tuple("t")
    assert x == "x" and y == "y"
    assert got_df.equals(df)


def test_get_dataset_tuple_from_dataset():
    pane = DummyPane()
    mgr = PlotManager(pane)
    df = pd.DataFrame({"x": [1, 2], "y": [3, 4]})
    ds = Dataset("d", df, x_name="x", y_name="y")
    mgr.datasets["d"] = ds
    got_df, x, y = mgr.get_dataset_tuple("d")
    assert x == "x" and y == "y"
    assert got_df.equals(df)
