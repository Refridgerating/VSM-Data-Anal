from .base import PARSERS, ParserPlugin, load_any, register

# Register built-in parsers
from . import csv  # noqa: F401

__all__ = ["PARSERS", "ParserPlugin", "load_any", "register"]
