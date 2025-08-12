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

    def as_dict(self) -> Dict[str, Any]:
        return {
            "chi": self.chi,
            "b": self.b,
            "x_fit": self.x_fit,
            "y_fit": self.y_fit,
            "r2": self.r2,
            "npoints": self.npoints,
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

    A = np.vstack([x.to_numpy(), np.ones(n)]).T
    chi, b = np.linalg.lstsq(A, y.to_numpy(), rcond=None)[0]
    y_pred = chi * x + b
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot != 0 else 0.0

    result = FitResult(chi, b, x, y_pred, r2, n)
    return result.as_dict()


def apply_subtraction(
    df: pd.DataFrame, x_name: str, y_name: str, chi: float, b: float
) -> pd.DataFrame:
    """Subtract chi*H + b from the dataset.

    Returns a copy of ``df`` with a new column ``y_name + '_corr'``.
    """
    df_corr = df.copy()
    y_corr = y_name + "_corr"
    df_corr[y_corr] = df_corr[y_name] - (chi * df_corr[x_name] + b)
    return df_corr
