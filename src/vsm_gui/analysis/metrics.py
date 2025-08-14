from __future__ import annotations

"""Numerical helpers for extracting magnetic metrics."""

import numpy as np
import pandas as pd


def _prepare_series(series: pd.Series) -> np.ndarray:
    """Return numeric numpy array dropping non-numeric values."""
    s = pd.to_numeric(series, errors="coerce").dropna()
    return s.to_numpy()


# ---------------------------------------------------------------------------
# Legacy helper retained for backwards compatibility ------------------------
# ---------------------------------------------------------------------------

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

    This is the previous public helper.  New code should prefer
    :func:`fit_ms_linear` with explicit window selection.
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
    coeffs, residuals, _, _ = np.linalg.lstsq(A, y_fit, rcond=None)
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


# ---------------------------------------------------------------------------
# New analysis helpers ------------------------------------------------------
# ---------------------------------------------------------------------------


def fit_ms_linear(
    df: pd.DataFrame,
    x_name: str,
    y_name: str,
    hmin: float,
    hmax: float,
) -> tuple[float, float, float, dict]:
    """Fit ``M = χH + Ms`` on a high-field window.

    Returns ``Ms``, ``χ``, ``R²`` and a details dict containing the window and
    number of points used.
    """
    h = _prepare_series(df[x_name])
    m = _prepare_series(df[y_name])
    mask = (h >= hmin) & (h <= hmax)
    x = h[mask]
    y = m[mask]
    if x.size < 2:
        raise ValueError("Insufficient points in fit window")

    A = np.column_stack([x, np.ones_like(x)])
    coeffs, _, _, _ = np.linalg.lstsq(A, y, rcond=None)
    chi, ms = coeffs[0], coeffs[1]
    yhat = chi * x + ms
    ss_res = float(np.sum((y - yhat) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r2 = float(1 - ss_res / ss_tot) if ss_tot > 0 else float("nan")
    return ms, chi, r2, {"n": int(x.size), "window": (hmin, hmax)}


def coercivity(
    df: pd.DataFrame,
    x_name: str,
    y_name: str,
    hwin: tuple[float, float] | None = None,
) -> tuple[float, dict]:
    """Compute coercive field as mean |H| of ``M=0`` crossings.

    ``hwin`` defines a symmetric window ``(hmin, hmax)`` around zero.  If not
    provided a window of ±2% of the absolute maximum field is used.
    """
    h = _prepare_series(df[x_name])
    m = _prepare_series(df[y_name])
    if h.size < 2 or m.size < 2:
        raise ValueError("Not enough data points")

    if hwin is None:
        max_h = float(np.nanmax(np.abs(h)))
        w = 0.02 * max_h
        hmin, hmax = -w, w
    else:
        hmin, hmax = hwin
    mask = (h >= hmin) & (h <= hmax)
    h_w = h[mask]
    m_w = m[mask]
    if h_w.size < 2:
        raise ValueError("No data in coercivity window")

    def _find_zeros(h_arr: np.ndarray, m_arr: np.ndarray) -> tuple[list[float], list[float]]:
        idxs = np.where(np.diff(np.sign(m_arr)) != 0)[0]
        zeros: list[float] = []
        for i in idxs:
            h1, h2 = h_arr[i], h_arr[i + 1]
            m1, m2 = m_arr[i], m_arr[i + 1]
            hz = h1 + (h2 - h1) * (-m1) / (m2 - m1)
            zeros.append(hz)
        pos = [z for z in zeros if z >= 0]
        neg = [z for z in zeros if z <= 0]
        return pos, neg

    pos, neg = _find_zeros(h_w, m_w)
    if (not pos or not neg) and hwin is not None:
        pos, neg = _find_zeros(h, m)
    if not pos or not neg:
        zeros = pos + neg
        if not zeros:
            raise ValueError("Could not find zero crossings")
        hc = float(np.mean([abs(z) for z in zeros]))
        det = {"window": (hmin, hmax)}
        if pos:
            det["Hc_pos"] = pos[0]
        if neg:
            det["Hc_neg"] = neg[0]
        return hc, det
    hc_pos = min(pos, key=abs)
    hc_neg = max(neg, key=abs)
    hc = 0.5 * (abs(hc_pos) + abs(hc_neg))
    return float(hc), {"Hc_pos": hc_pos, "Hc_neg": hc_neg, "window": (hmin, hmax)}


def remanence(
    df: pd.DataFrame,
    x_name: str,
    y_name: str,
    h0: float = 0.0,
    window_pts: int = 4,
) -> tuple[float, dict]:
    """Interpolate magnetisation at ``H=h0`` using nearest points."""
    h = _prepare_series(df[x_name])
    m = _prepare_series(df[y_name])
    if h.size < 2 or m.size < 2:
        raise ValueError("Not enough data points")
    if not (h.min() <= h0 <= h.max()):
        raise ValueError("Field does not include interpolation point")

    order = np.argsort(np.abs(h - h0))
    n = min(max(window_pts, 2), order.size)
    sel = order[:n]
    x = h[sel]
    y = m[sel]

    A = np.column_stack([x, np.ones_like(x)])
    coeffs, _, _, _ = np.linalg.lstsq(A, y, rcond=None)
    slope, intercept = coeffs[0], coeffs[1]
    return float(intercept), {"slope": float(slope), "n": int(n), "h0": h0}


