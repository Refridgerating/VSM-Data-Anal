import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

MODULES = [
    "vsm_gui",
    "vsm_gui.app",
    "vsm_gui.main_window",
]

BASE = ROOT / "src" / "vsm_gui"
for sub in ["widgets", "plotting", "analysis", "utils"]:
    for path in (BASE / sub).glob("*.py"):
        if path.name == "__init__.py":
            continue
        MODULES.append(f"vsm_gui.{sub}.{path.stem}")


@pytest.mark.parametrize("modname", MODULES)
def test_imports(modname):
    try:
        importlib.import_module(modname)
    except Exception as exc:  # noqa: BLE001
        pytest.fail(f"Failed to import {modname}: {exc}")
