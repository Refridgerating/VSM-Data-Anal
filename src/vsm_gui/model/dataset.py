from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

from ..services import units


@dataclass
class Dataset:
    """Container for a loaded dataset."""

    label: str
    df: pd.DataFrame
    x_name: str | None = None
    y_name: str | None = None
    units: Dict[str, str] = field(default_factory=dict)
    meta: Dict[str, Any] = field(default_factory=dict)

    def select_xy(self, x: str, y: str) -> pd.DataFrame:
        """Return a cleaned numeric frame with the requested columns."""
        if x not in self.df.columns or y not in self.df.columns:
            raise KeyError(f"Missing column '{x}' or '{y}'")
        data = self.df[[x, y]].copy()
        data = units.to_numeric(data, [x, y])
        return data.replace([np.inf, -np.inf], pd.NA).dropna()

    def clone(self, label: Optional[str] = None) -> Dataset:
        """Return a shallow copy optionally with a new label."""
        return Dataset(
            label=label or self.label,
            df=self.df.copy(),
            x_name=self.x_name,
            y_name=self.y_name,
            units=self.units.copy(),
            meta=self.meta.copy(),
        )
