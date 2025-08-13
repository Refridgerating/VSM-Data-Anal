import numpy as np
import pandas as pd

from vsm_gui.analysis import paramag


def test_paramag_subtraction_preserves_intercept_and_remanence():
    rng = np.random.default_rng(0)
    h = np.linspace(-10, 10, 1001)
    ms = 1.23
    chi = 0.05
    noise = rng.normal(scale=1e-3, size=h.size)
    m = ms + chi * h + noise

    df = pd.DataFrame({"H": h, "M": m})

    # Fit the linear tail and subtract only the paramagnetic slope
    res = paramag.fit_linear_tail(df, "H", "M")
    df_corr = paramag.apply_subtraction(df, "H", "M", res["chi"], res["b"])

    # High-field region mean should be close to Ms (intercept retained)
    mask = np.abs(df_corr["H"]) > 8
    mean_high = df_corr.loc[mask, "M_corr"].mean()
    assert np.isclose(mean_high, ms, atol=5e-3)

    # Remanence at H=0 remains unchanged because intercept is not subtracted
    idx0 = np.argmin(np.abs(df["H"]))
    assert np.isclose(
        df_corr.loc[idx0, "M_corr"], df.loc[idx0, "M"], atol=1e-8
    )

