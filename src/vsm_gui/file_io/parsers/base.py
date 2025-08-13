from __future__ import annotations

from pathlib import Path
from typing import Optional, Protocol

import pandas as pd


class ParserPlugin(Protocol):
    name: str
    extensions: tuple[str, ...]

    def sniff(self, path: Path, head: str) -> bool:
        ...

    def load(self, path: Path) -> pd.DataFrame:
        ...


PARSERS: list[ParserPlugin] = []


def register(parser: ParserPlugin) -> None:
    PARSERS.append(parser)


def load_any(path: Path) -> pd.DataFrame:
    text = Path(path).read_text(errors="ignore")[:4096]
    for parser in PARSERS:
        if any(path.suffix.lower() == ext for ext in parser.extensions) or parser.sniff(path, text):
            return parser.load(path)
    for sep in [",", "\t", ";"]:
        try:
            return pd.read_csv(path, sep=sep)
        except Exception:
            pass
    raise ValueError(f"No parser could read {path}")
