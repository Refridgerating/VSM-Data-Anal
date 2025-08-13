import numpy as np
import pandas as pd
import pytest

from vsm_gui.analysis import paramag


def test_autodetect_window_success():
    rng = np.random.default_rng(0)
    h = np.linspace(-10, 10, 101)
    chi = 0.05
    m = chi * h + rng.normal(scale=1e-3, size=h.size)
    df = pd.DataFrame({"H": h, "M": m})

    res = paramag.autodetect_window(df, "H", "M")

    assert set(res.keys()) == {"hmin", "hmax", "chi", "b", "npoints", "r2"}
    assert res["r2"] > 0.7
    threshold = np.quantile(np.abs(h), 0.8)
    mask = np.abs(h) >= threshold
    assert np.isclose(res["hmin"], h[mask].min())
    assert np.isclose(res["hmax"], h[mask].max())


def test_autodetect_window_poor_fit_raises():
    rng = np.random.default_rng(1)
    h = np.linspace(-10, 10, 100)
    m = rng.normal(size=h.size)
    df = pd.DataFrame({"H": h, "M": m})

    with pytest.raises(ValueError):
        paramag.autodetect_window(df, "H", "M")
