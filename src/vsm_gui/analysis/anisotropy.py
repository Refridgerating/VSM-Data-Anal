from __future__ import annotations

import numpy as np
import pandas as pd


def sucksmith_thompson(
    df: pd.DataFrame,
    x_name: str,
    y_name: str,
    window: tuple[float, float] | None = None,
    apply_demag: bool = False,
    geometry: str | None = None,
) -> tuple[float, dict]:
    """Estimate uniaxial anisotropy constant using the Sucksmith–Thompson method."""
    h = pd.to_numeric(df[x_name], errors="coerce").dropna()
    m = pd.to_numeric(df[y_name], errors="coerce").dropna()
    if h.empty or m.empty:
        raise ValueError("No numeric data")

    if window is None:
        hmin = h.min() + 0.9 * (h.max() - h.min())
        hmax = h.max()
    else:
        hmin, hmax = window

    mask = (h >= hmin) & (h <= hmax)
    if mask.sum() < 2:
        raise ValueError("Insufficient high-field points")

    x = (m[mask] ** 2).to_numpy()
    y = (m[mask] / h[mask]).to_numpy()
    coeffs = np.polyfit(x, y, 1)
    slope, intercept = coeffs[0], coeffs[1]
    if intercept == 0:
        raise ValueError("Cannot determine Ku (zero intercept)")

    ku = 0.5 / intercept
    note = ""
    if not apply_demag:
        note = "No demag correction"
    return ku, {"slope": slope, "intercept": intercept, "window": (hmin, hmax), "note": note}
