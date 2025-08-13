import numpy as np
import pandas as pd

from vsm_gui.analysis import paramag


def test_paramag_subtraction_per_file_autodetect():
    rng = np.random.default_rng(0)
    h = np.linspace(-10, 10, 1001)
    ms = 1.0
    h0 = 2.0
    chis = [0.03, -0.06]
    dfs = []
    for chi in chis:
        m = ms * np.tanh(h / h0) + chi * h + rng.normal(scale=5e-4, size=h.size)
        dfs.append(pd.DataFrame({"H": h, "M": m}))

    for df, chi_true in zip(dfs, chis):
        det = paramag.autodetect_windows(df, "H", "M")
        chi = det["chi_combined"]
        assert np.isclose(chi, chi_true, rtol=0.2)
        df_corr = paramag.apply_subtraction(df, "H", "M", chi)
        for branch_mask in (df_corr["H"] > 8, df_corr["H"] < -8):
            xs = df_corr.loc[branch_mask, "H"]
            ys = df_corr.loc[branch_mask, "M_corr"]
            if xs.empty:
                continue
            m_fit, _ = np.polyfit(xs, ys, 1)
            assert abs(m_fit) < 5e-3
        idx0 = np.argmin(np.abs(df["H"]))
        assert np.isclose(df_corr.loc[idx0, "M_corr"], df.loc[idx0, "M"], atol=1e-8)
