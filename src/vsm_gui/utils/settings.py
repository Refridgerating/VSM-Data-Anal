from __future__ import annotations

from PyQt6.QtCore import QSettings


class AppSettings:
    """Thin wrapper around :class:`QSettings` for per-user persistence."""

    def __init__(self) -> None:
        self._s = QSettings("YourLab", "VSM-GUI")

    def get(self, key: str, default=None):  # noqa: ANN001 - Qt types
        """Return the stored value for *key* or *default* if missing."""
        return self._s.value(key, default)

    def set(self, key: str, value) -> None:  # noqa: ANN001 - Qt types
        """Store *value* under *key*."""
        self._s.setValue(key, value)
