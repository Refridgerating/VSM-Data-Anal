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
) -> tuple[float, dict]:
    """Estimate saturation magnetization using a high-field linear fit.

    Parameters
    ----------
    df, x_name, y_name:
        Data and column names.
    window:
        Optional ``(Hmin, Hmax)`` selection for high-field region. If not
        provided the top 10\% of the field range is used.
    convert:
        If ``True`` convert moment to magnetisation (A/m) using ``params``.
    params:
        Mapping containing optional ``mass``, ``density``, ``thickness`` and
        ``area`` entries.
    """
    h = _prepare_series(df[x_name])
    m = _prepare_series(df[y_name])
    if h.size == 0 or m.size == 0:
        raise ValueError("No numeric data")

    if window is None:
        hmin = h.min() + 0.9 * (h.max() - h.min())
        hmax = h.max()
    else:
        hmin, hmax = window

    mask = (h >= hmin) & (h <= hmax)
    if mask.sum() < 2:
        raise ValueError("Insufficient points in high-field window")
    x = h[mask]
    y = m[mask]

    coeffs = np.polyfit(x, y, 1)
    chi, ms = coeffs[0], coeffs[1]
    p = np.poly1d(coeffs)
    yhat = p(x)
    ss_res = np.sum((y - yhat) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot != 0 else 1.0
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
            unit = "A/m"

    return ms, {"chi": chi, "r2": r2, "window": (hmin, hmax), "unit": unit}


def coercivity(df: pd.DataFrame, x_name: str, y_name: str) -> tuple[float, dict]:
    """Determine coercive field by locating M=0 crossings."""
    h = _prepare_series(df[x_name])
    m = _prepare_series(df[y_name])
    if h.size < 2 or m.size < 2:
        raise ValueError("Not enough data points")
    idx = np.argsort(h)
    h = h[idx]
    m = m[idx]
    zeros: list[float] = []
    for i in range(len(h) - 1):
        m1, m2 = m[i], m[i + 1]
        if m1 == m2:
            continue
        if m1 == 0:
            zeros.append(h[i])
        elif (m1 < 0 and m2 > 0) or (m1 > 0 and m2 < 0):
            h1, h2 = h[i], h[i + 1]
            hz = h1 + (h2 - h1) * (-m1) / (m2 - m1)
            zeros.append(hz)
    if not zeros:
        raise ValueError("No zero crossing found")
    hc = float(np.mean(np.abs(zeros)))
    return hc, {"zeros": zeros}


def remanence(df: pd.DataFrame, x_name: str, y_name: str) -> tuple[float, dict]:
    """Interpolate magnetisation at H=0."""
    h = _prepare_series(df[x_name])
    m = _prepare_series(df[y_name])
    if h.size < 2 or m.size < 2:
        raise ValueError("Not enough data points")
    idx = np.argsort(h)
    h = h[idx]
    m = m[idx]
    if not (h.min() <= 0 <= h.max()):
        raise ValueError("Field does not include 0")
    mr = float(np.interp(0.0, h, m))
    return mr, {}
