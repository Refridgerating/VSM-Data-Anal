import numpy as np
import pandas as pd

from vsm_gui.analysis.paramag import autodetect_windows


def test_autodetect_windows_branches():
    rng = np.random.default_rng(0)
    h = np.linspace(-10, 10, 1001)
    ms = 1.0
    h0 = 2.0
    chi = 0.05
    m = ms * np.tanh(h / h0) + chi * h + rng.normal(scale=5e-4, size=h.size)
    df = pd.DataFrame({"H": h, "M": m})

    res = autodetect_windows(df, "H", "M")
    hmax = np.max(np.abs(h))
    for branch, mask in (("neg", h < 0), ("pos", h > 0)):
        br = res[branch]
        branch_h = h[mask]
        assert br["r2"] >= 0.995
        assert br["n"] <= 0.4 * branch_h.size + 1
        assert min(abs(br["hmin"]), abs(br["hmax"])) > 0.2 * hmax
        span = abs(branch_h[-1] - branch_h[0])
        assert abs(br["hmax"] - br["hmin"]) >= 0.10 * span
    assert np.isclose(res["chi_combined"], chi, rtol=0.1)
