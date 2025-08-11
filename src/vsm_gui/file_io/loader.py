from __future__ import annotations

from pathlib import Path
import pandas as pd


def read_csv(path: Path) -> pd.DataFrame:
    """Read a CSV file into a DataFrame.

    Parameters
    ----------
    path : Path
        Path to the CSV file.

    Returns
    -------
    pandas.DataFrame
        Parsed dataframe.
    """
    return pd.read_csv(path, sep=None, engine="python", encoding="utf-8-sig")
