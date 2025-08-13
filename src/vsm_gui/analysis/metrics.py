from __future__ import annotations

import numpy as np
import pandas as pd


def _prepare_series(series: pd.Series) -> np.ndarray:
    """Return numeric numpy array dropping non-numeric values."""
    s = pd.to_numeric(series, errors="coerce").dropna()
    return s.to_numpy()


def saturation_magnetization(
    df: pd.DataFrame,
    x_name: str,
    y_name: str,
    window: tuple[float, float] | None = None,
    convert: bool = False,
    params: dict | None = None,
    q: float = 0.8,
) -> tuple[float, dict]:
    """Estimate saturation magnetisation via high-field linear regression.

    A linear model ``M ≈ Ms + χH`` is fitted on the high-field tails. If a
    ``window`` is not provided the fit uses points where ``|H|`` falls in the
    upper quantile ``q`` (default 0.8).
    """
    h = _prepare_series(df[x_name])
    m = _prepare_series(df[y_name])
    if h.size == 0 or m.size == 0:
        raise ValueError("No numeric data")

    if window is None:
        thresh = np.quantile(np.abs(h), q)
        mask = np.abs(h) >= thresh
        if mask.sum() < 2:
            raise ValueError("Insufficient points in high-field tails")
        hmin, hmax = h[mask].min(), h[mask].max()
    else:
        hmin, hmax = window
        mask = (h >= hmin) & (h <= hmax)
        if mask.sum() < 2:
            raise ValueError("Insufficient points in high-field window")

    x = h[mask]
    y = m[mask]

    x_fit = np.abs(x)
    y_fit = np.sign(x) * y
    A = np.column_stack([np.ones_like(x_fit), x_fit])
    coeffs, residuals, rank, s = np.linalg.lstsq(A, y_fit, rcond=None)
    ms, chi = coeffs[0], coeffs[1]
    if residuals.size > 0 and x.size > 2:
        stderr = float(np.sqrt(residuals[0] / (x.size - 2)))
    else:
        stderr = float("nan")
    unit = "raw"

    if convert and params:
        volume = None
        mass = params.get("mass", 0)
        density = params.get("density", 0)
        thickness = params.get("thickness", 0)
        area = params.get("area", 0)
        if mass and density:
            volume = mass / density
        elif thickness and area:
            volume = thickness * area
        if volume and volume > 0:
            ms = ms / volume
            stderr = stderr / volume if not np.isnan(stderr) else stderr
            unit = "A/m"

    return ms, {"chi": chi, "stderr": stderr, "window": (hmin, hmax), "unit": unit}


def coercivity(df: pd.DataFrame, x_name: str, y_name: str) -> tuple[float, dict]:
    """Determine coercive field by locating ``M=0`` crossings on each branch."""
    h = _prepare_series(df[x_name])
    m = _prepare_series(df[y_name])
    if h.size < 4 or m.size < 4:
        raise ValueError("Not enough data points")

    mid = h.size // 2
    h1, m1 = h[:mid], m[:mid]
    h2, m2 = h[mid:], m[mid:]

    # Determine orientation of branches
    if h1[-1] > h1[0]:
        asc_h, asc_m = h1, m1
        desc_h, desc_m = h2, m2
    else:
        desc_h, desc_m = h1, m1
        asc_h, asc_m = h2, m2

    def _branch_zero(hb: np.ndarray, mb: np.ndarray) -> float:
        idxs = np.where(np.diff(np.sign(mb)) != 0)[0]
        if idxs.size == 0:
            raise ValueError("No zero crossing found on branch")
        zeros = []
        for i in idxs:
            h1, h2 = hb[i], hb[i + 1]
            m1, m2 = mb[i], mb[i + 1]
            hz = h1 + (h2 - h1) * (-m1) / (m2 - m1)
            zeros.append(hz)
        return min(zeros, key=lambda v: abs(v))

    hz_asc = _branch_zero(asc_h, asc_m)
    hz_desc = _branch_zero(desc_h, desc_m)
    hc = float(0.5 * (abs(hz_asc) + abs(hz_desc)))
    return hc, {"ascending": hz_asc, "descending": hz_desc, "unit": "raw"}


def remanence(
    df: pd.DataFrame,
    x_name: str,
    y_name: str,
    fit_points: int = 4,
    smooth: bool = False,
) -> tuple[float, dict]:
    """Interpolate magnetisation at ``H=0`` using local linear fit."""
    h = _prepare_series(df[x_name])
    m = _prepare_series(df[y_name])
    if h.size < 2 or m.size < 2:
        raise ValueError("Not enough data points")
    if not (h.min() <= 0 <= h.max()):
        raise ValueError("Field does not include 0")

    if smooth:
        try:
            from scipy.signal import savgol_filter

            win = min(len(m) // 2 * 2 + 1, 7)
            if win >= 3:
                m = savgol_filter(m, win, 1)
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError("Savitzky–Golay smoothing failed") from exc

    order = np.argsort(np.abs(h))
    n = min(max(fit_points, 2), order.size)
    sel = order[:n]
    x = h[sel]
    y = m[sel]

    A = np.column_stack([x, np.ones_like(x)])
    coeffs, _, _, _ = np.linalg.lstsq(A, y, rcond=None)
    slope, intercept = coeffs[0], coeffs[1]
    mr = float(intercept)
    return mr, {"slope": slope, "n": n, "unit": "raw"}
