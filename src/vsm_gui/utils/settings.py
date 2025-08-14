from __future__ import annotations

from PyQt6.QtCore import QSettings


class AppSettings:
    """Thin wrapper around :class:`QSettings` for per-user persistence."""

    def __init__(self) -> None:
        self._settings = QSettings("YourLab", "VSM-GUI")

    def get(self, key: str, default=None):  # noqa: ANN001 - Qt types
        """Return the stored value for *key* or *default* if missing."""
        return self._settings.value(key, default)

    # Typed getters -----------------------------------------------------
    def get_str(self, key: str, default: str = "") -> str:
        val = self._settings.value(key, default)
        if val is None:
            return default
        return str(val)

    def get_bool(self, key: str, default: bool = False) -> bool:
        val = self._settings.value(key, default)
        if isinstance(val, bool):
            return val
        if isinstance(val, (int, float)):
            return bool(val)
        if isinstance(val, str):
            return val.strip().lower() in ("1", "true", "yes", "on")
        return default

    def get_int(self, key: str, default: int = 0) -> int:
        val = self._settings.value(key, default)
        try:
            return int(float(val))
        except Exception:
            return default

    def get_float(self, key: str, default: float = 0.0) -> float:
        val = self._settings.value(key, default)
        try:
            return float(val)
        except Exception:
            return default

    def set(self, key: str, value) -> None:  # noqa: ANN001 - Qt types
        """Store *value* under *key*."""
        self._settings.setValue(key, value)
