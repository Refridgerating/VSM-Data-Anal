from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

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


def autodetect_windows(
    df: pd.DataFrame,
    x_name: str,
    y_name: str,
    *,
    core_exclude_frac: float = 0.2,
    slide_frac: float = 0.08,
    r2_min: float = 0.995,
    slope_std_rel_max: float = 0.10,
    q_abs_max: float | None = None,
    max_frac: float = 0.4,
    n_min: int = 20,
    dh_min_frac: float = 0.10,
    smooth_window: int | None = None,
) -> dict:
    """Auto-detect high-field linear tails for negative and positive branches.

    Parameters are tuned for typical VSM loops.  Data are split by the sign of
    ``H`` and analysed separately so that each branch is treated
    independently.  Only the slope ``χ`` of the paramagnetic contribution is
    considered when correcting the data; the intercept is preserved so that no
    vertical shift occurs.

    Returns a dictionary containing per-branch statistics and the combined
    susceptibility (median of available branch values).
    """

    dfc = df[[x_name, y_name]].apply(pd.to_numeric, errors="coerce").replace(
        [np.inf, -np.inf], np.nan
    )
    dfc = dfc.dropna()
    if dfc.empty:
        raise ValueError("No valid data")

    h = dfc[x_name]
    m = dfc[y_name]
    hmax = float(h.abs().max())
    core_limit = core_exclude_frac * hmax

    notes: list[str] = []

    def _process_branch(mask: pd.Series, name: str) -> dict | None:
        branch = dfc[mask]
        if branch.empty:
            notes.append(f"{name} branch: no data")
            return None
        # Sort so that index 0 corresponds to the outermost field value
        if name == "pos":
            branch = branch.sort_values(x_name, ascending=False)
        else:
            branch = branch.sort_values(x_name, ascending=True)

        x = branch[x_name].to_numpy()
        y = branch[y_name].to_numpy()
        n = x.size
        if n < n_min:
            notes.append(f"{name} branch: insufficient points")
            return None

        w = max(n_min, int(slide_frac * n))
        if w > n:
            notes.append(f"{name} branch: window larger than branch")
            return None

        if smooth_window and smooth_window > 1:
            y_diag = (
                pd.Series(y)
                .rolling(smooth_window, center=True, min_periods=1)
                .mean()
                .to_numpy()
            )
        else:
            y_diag = y

        slopes: list[float] = []
        start_idx: int | None = None
        i = 0
        while i <= n - w:
            xs = x[i : i + w]
            ys = y_diag[i : i + w]
            try:
                slope, intercept = np.polyfit(xs, ys, 1)
                y_pred = slope * xs + intercept
                ss_res = np.sum((ys - y_pred) ** 2)
                ss_tot = np.sum((ys - ys.mean()) ** 2)
                r2 = 1 - ss_res / ss_tot if ss_tot != 0 else 0.0
                if q_abs_max is not None:
                    q = np.polyfit(xs, ys, 2)[0]
                    curvature_ok = abs(q) <= q_abs_max
                else:
                    curvature_ok = True
            except np.linalg.LinAlgError:
                break
            if r2 >= r2_min and curvature_ok:
                if start_idx is None:
                    start_idx = i
                slopes.append(float(slope))
                i += 1
            else:
                if start_idx is None:
                    i += 1
                    continue
                else:
                    break

        if start_idx is None or not slopes:
            notes.append(f"{name} branch: no valid window")
            return None
        valid_count = len(slopes)

        # Enforce slope stability by trimming from the inner side
        while valid_count > 1:
            s = np.array(slopes[:valid_count])
            mean_s = float(np.mean(s))
            std_s = float(np.std(s))
            rel = np.inf if mean_s == 0 else std_s / abs(mean_s)
            if rel <= slope_std_rel_max:
                break
            valid_count -= 1

        if valid_count == 0:
            notes.append(f"{name} branch: unstable slope")
            return None

        end = start_idx + valid_count + w - 1
        end = min(end, n - 1)
        region_len = end - start_idx + 1
        max_len = int(max_frac * n)
        if region_len > max_len:
            end = start_idx + max_len - 1
            region_len = end - start_idx + 1
        if region_len < n_min:
            notes.append(f"{name} branch: window too short")
            return None

        xs = x[start_idx : end + 1]
        ys = y[start_idx : end + 1]  # use original data for final fit

        dh = abs(xs[-1] - xs[0])
        span = abs(x[-1] - x[0])
        if dh < dh_min_frac * span:
            notes.append(f"{name} branch: span below threshold")
            return None

        slope, intercept = np.polyfit(xs, ys, 1)
        y_pred = slope * xs + intercept
        ss_res = np.sum((ys - y_pred) ** 2)
        ss_tot = np.sum((ys - ys.mean()) ** 2)
        r2 = 1 - ss_res / ss_tot if ss_tot != 0 else 0.0

        return {
            "hmin": float(xs.min()),
            "hmax": float(xs.max()),
            "idx": (0, int(end)),
            "chi": float(slope),
            "b": float(intercept),
            "r2": float(r2),
            "n": int(xs.size),
        }

    neg_mask = (h < 0) & (h.abs() > core_limit)
    pos_mask = (h > 0) & (h.abs() > core_limit)
    neg = _process_branch(neg_mask, "neg")
    pos = _process_branch(pos_mask, "pos")

    result: dict[str, Any] = {}
    if neg:
        result["neg"] = neg
    if pos:
        result["pos"] = pos
    if not result:
        raise ValueError("No valid high-field tails detected")

    chis = [b["chi"] for b in result.values()]
    result["chi_combined"] = float(np.median(chis))
    result["notes"] = notes
    return result


def autodetect_window(
    df: pd.DataFrame, x_name: str, y_name: str, frac: float = 0.2
) -> Dict[str, Any]:
    """Auto-select a high-field window and fit ``y = a*x + b``.

    Parameters
    ----------
    df : DataFrame
        Input data containing ``x_name`` and ``y_name`` columns.
    x_name, y_name : str
        Column names for the field and magnetization.
    frac : float, optional
        Fraction of data to use, starting from the highest ``|H|`` values.

    Returns
    -------
    dict
        ``{"hmin": float, "hmax": float, "chi": float, ``"b"``: float,
        ``"npoints"``: int, ``"r2"``: float}``

    Raises
    ------
    ValueError
        If there are insufficient points or the fit is ill-conditioned / poor.
    """

    x = df[x_name]
    threshold = x.abs().quantile(1 - frac)
    mask = x.abs() >= threshold
    window = df[mask]
    n = len(window)
    if n < 2:
        raise ValueError("Not enough points for auto-detection")

    xs = window[x_name]
    ys = window[y_name]
    try:
        chi, b = np.polyfit(xs, ys, 1)
    except np.linalg.LinAlgError as exc:  # pragma: no cover - extremely rare
        raise ValueError("Ill-conditioned fit") from exc

    y_pred = chi * xs + b
    ss_res = np.sum((ys - y_pred) ** 2)
    ss_tot = np.sum((ys - ys.mean()) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot != 0 else 0.0
    if r2 < 0.7:
        raise ValueError("Poor linear fit (r² < 0.7)")

    return {
        "hmin": float(xs.min()),
        "hmax": float(xs.max()),
        "chi": float(chi),
        "b": float(b),
        "npoints": int(n),
        "r2": float(r2),
    }


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


def apply_subtraction(df: pd.DataFrame, x_name: str, y_name: str, chi: float) -> pd.DataFrame:
    """Subtract the paramagnetic slope ``chi`` from ``df``.

    Only the linear paramagnetic contribution ``chi*H`` is removed; any
    intercept from the fit is preserved so that the vertical placement of the
    hysteresis loop (e.g. remanent magnetization) is unchanged.
    """

    df_corr = df.copy()
    y_corr = y_name + "_corr"
    df_corr[y_corr] = df_corr[y_name] - chi * df_corr[x_name]
    return df_corr
