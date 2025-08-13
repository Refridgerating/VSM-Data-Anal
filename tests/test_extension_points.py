from __future__ import annotations

from pathlib import Path

import pandas as pd

from vsm_gui.file_io.parsers import load_any, register, ParserPlugin
from vsm_gui.model import Dataset


class DummyParser:
    name = "dummy"
    extensions = (".dum",)

    def sniff(self, path: Path, head: str) -> bool:  # noqa: D401
        return head.startswith("dummy")

    def load(self, path: Path) -> pd.DataFrame:
        return pd.DataFrame({"x": [1, 2], "y": [3, 4]})


def test_parser_registration(tmp_path: Path) -> None:
    parser: ParserPlugin = DummyParser()
    register(parser)
    path = tmp_path / "file.dum"
    path.write_text("dummy")
    df = load_any(path)
    assert list(df.columns) == ["x", "y"]


def test_dataset_model() -> None:
    df = pd.DataFrame({"a": [1, 2, "bad"], "b": [4.0, float("inf"), 6.0]})
    ds = Dataset("test", df)
    clean = ds.select_xy("a", "b")
    assert list(clean.columns) == ["a", "b"]
    assert len(clean) == 1
    clone = ds.clone(label="copy")
    assert clone.label == "copy" and clone.df.equals(df)
