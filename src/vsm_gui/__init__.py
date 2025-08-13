"""VSM GUI package."""

__all__ = ["main"]
__version__ = "0.1.0"


def main() -> None:  # pragma: no cover - thin wrapper
    """Entry point wrapper for ``python -m vsm_gui``."""
    from .app import main as _main

    _main()
