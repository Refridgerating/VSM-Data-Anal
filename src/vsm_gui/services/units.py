from __future__ import annotations

from typing import Iterable, Mapping

import pandas as pd

# Basic unit labels -- extend as needed
MOMENT_UNITS = {
    "emu": "electromagnetic unit",
    "A/m": "ampere per meter",
}


def to_numeric(df: pd.DataFrame, cols: Iterable[str]) -> pd.DataFrame:
    """Coerce selected columns to numeric values."""
    result = df.copy()
    for col in cols:
        result[col] = pd.to_numeric(result[col], errors="coerce")
    return result


def convert_moment(
    df: pd.DataFrame,
    from_unit: str,
    to_unit: str,
    params: Mapping[str, float] | None = None,
) -> pd.DataFrame:
    """Convert magnetic moment units.

    Currently only supports a pass-through when units match.
    """
    if from_unit == to_unit:
        return df
    raise NotImplementedError(
        f"Conversion from {from_unit!r} to {to_unit!r} is not implemented"
    )
