import numpy as np
import pandas as pd

from vsm_gui.analysis import metrics


def _make_loop(offset: float = 0.0, noise: float = 0.0, seed: int = 0):
    Ms = 1.0
    H0 = 500.0
    chi = 1e-4
    H_up = np.linspace(-10000, 10000, 1001)
    H_down = np.linspace(10000, -10000, 1001)[1:]
    H = np.concatenate([H_up, H_down])
    M = Ms * np.tanh(H / H0) + chi * H + offset
    if noise:
        rng = np.random.default_rng(seed)
        M = M + noise * rng.standard_normal(M.shape)
    df = pd.DataFrame({"H": H, "M": M})
    return df, Ms, H0, chi


def _solve_hc(Ms: float, H0: float, chi: float, offset: float) -> float:
    def f(H: float) -> float:
        return Ms * np.tanh(H / H0) + chi * H + offset

    a, b = -1000.0, 0.0
    for _ in range(60):
        c = 0.5 * (a + b)
        if f(a) * f(c) <= 0:
            b = c
        else:
            a = c
    return abs(0.5 * (a + b))


def test_metrics_precise_clean():
    df, Ms_true, H0, _ = _make_loop()
    ms, _ = metrics.saturation_magnetization(df, "H", "M")
    assert np.isclose(ms, Ms_true, rtol=0.02)
    hc, _ = metrics.coercivity(df, "H", "M")
    assert abs(hc) < 0.02 * H0
    mr, _ = metrics.remanence(df, "H", "M")
    assert abs(mr) < 0.02 * Ms_true


def test_metrics_precise_noisy_offset():
    offset = 0.05
    df, Ms_true, H0, chi = _make_loop(offset=offset, noise=0.01, seed=1)
    ms, _ = metrics.saturation_magnetization(df, "H", "M")
    assert np.isclose(ms, Ms_true, rtol=0.05)
    hc_true = _solve_hc(Ms_true, H0, chi, offset)
    hc, _ = metrics.coercivity(df, "H", "M")
    assert np.isclose(hc, hc_true, rtol=0.2)
    mr, _ = metrics.remanence(df, "H", "M")
    assert np.isclose(mr, offset, rtol=0.05)
