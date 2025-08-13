from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any

import numpy as np
import pandas as pd


@dataclass
class FitResult:
    chi: float
    b: float
    x_fit: pd.Series
    y_fit: pd.Series
    r2: float
    npoints: int
    hmin: float
    hmax: float

    def as_dict(self) -> Dict[str, Any]:
        return {
            "chi": self.chi,
            "b": self.b,
            "x_fit": self.x_fit,
            "y_fit": self.y_fit,
            "r2": self.r2,
            "npoints": self.npoints,
            "hmin": self.hmin,
            "hmax": self.hmax,
        }


def _select_window(
    df: pd.DataFrame, x_name: str, hmin: float | None, hmax: float | None
) -> pd.DataFrame:
    x = df[x_name]
    if hmin is None and hmax is None:
        # Default to top 20% by |H|
        threshold = x.abs().quantile(0.8)
        mask = x.abs() >= threshold
    else:
        mask = pd.Series(True, index=df.index)
        if hmin is not None:
            mask &= x >= hmin
        if hmax is not None:
            mask &= x <= hmax
    return df[mask]


def fit_linear_tail(
    df: pd.DataFrame,
    x_name: str,
    y_name: str,
    hmin: float | None = None,
    hmax: float | None = None,
) -> Dict[str, Any]:
    """Fit M(H) = chi*H + b on the selected window.

    Parameters
    ----------
    df : DataFrame
        Input dataframe containing columns `x_name` and `y_name`.
    x_name, y_name : str
        Column names for field and magnetization.
    hmin, hmax : float | None
        Field window to use. If both are None, the top 20% by |H| is used.
    """
    window = _select_window(df, x_name, hmin, hmax)
    x = window[x_name]
    y = window[y_name]
    n = len(window)
    if n < 2:
        raise ValueError("Not enough points in selected window")

    chi, b = np.polyfit(x, y, 1)
    y_pred = chi * x + b
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot != 0 else 0.0

    result = FitResult(chi, b, x, y_pred, r2, n, x.min(), x.max())
    return result.as_dict()


def detect_linear_tail(
    df: pd.DataFrame,
    x_name: str,
    y_name: str,
    quantiles: tuple[float, float] = (0.8, 0.9),
    min_points: int = 20,
    min_r2: float = 0.7,
) -> Dict[str, Any]:
    """Auto-detect a high-field linear region and fit it.

    The algorithm selects points where ``|H|`` is above the given quantiles,
    fits a line ``M = chi*H + b`` and checks that enough points are used and
    that the fit quality is acceptable. If the first quantile fails the
    requirements the next one is attempted.  On failure a ``ValueError`` is
    raised so the caller may fall back to manual selection.
    """

    x = df[x_name]
    y = df[y_name]
    for q in quantiles:
        threshold = x.abs().quantile(q)
        mask = x.abs() >= threshold
        window = df[mask]
        n = len(window)
        if n < 2:
            continue
        xs = window[x_name]
        ys = window[y_name]
        chi, b = np.polyfit(xs, ys, 1)
        y_pred = chi * xs + b
        ss_res = np.sum((ys - y_pred) ** 2)
        ss_tot = np.sum((ys - ys.mean()) ** 2)
        r2 = 1 - ss_res / ss_tot if ss_tot != 0 else 0.0
        if n >= min_points and r2 >= min_r2:
            result = FitResult(chi, b, xs, y_pred, r2, n, xs.min(), xs.max())
            return result.as_dict()

    raise ValueError("Auto-detection failed")


def apply_subtraction(
    df: pd.DataFrame, x_name: str, y_name: str, chi: float, b: float
) -> pd.DataFrame:
    """Subtract ``chi*H`` from the dataset, preserving the intercept ``b``.

    The linear fit ``M ≈ chi*H + b`` is still reported to the caller, but only
    the slope term is removed from the data so that any ferromagnetic content
    (e.g. remanent magnetization) remains unchanged.  A copy of ``df`` is
    returned with a new column ``y_name + '_corr'`` holding the corrected
    values.

    Parameters
    ----------
    df : DataFrame
        Input data containing ``x_name`` and ``y_name`` columns.
    x_name, y_name : str
        Column names for the field ``H`` and magnetization ``M``.
    chi : float
        Fitted paramagnetic susceptibility.
    b : float
        Intercept from the fit.  Kept for diagnostic purposes and not used in
        the subtraction.
    """

    df_corr = df.copy()
    y_corr = y_name + "_corr"
    # Subtract only the slope term; leave the intercept untouched so that
    # vertical positioning (e.g. Mr, Ms) is preserved.
    df_corr[y_corr] = df_corr[y_name] - chi * df_corr[x_name]
    return df_corr
