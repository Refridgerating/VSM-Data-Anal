from __future__ import annotations

from pathlib import Path

import pandas as pd

from .base import ParserPlugin, register


class CSVParser:
    name = "csv"
    extensions = (".csv", ".tsv", ".txt")

    def sniff(self, path: Path, head: str) -> bool:
        return "," in head or "\t" in head

    def load(self, path: Path) -> pd.DataFrame:
        return pd.read_csv(path, sep=None, engine="python", encoding="utf-8-sig")


register(CSVParser())
