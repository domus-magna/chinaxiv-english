"""
Data models for ChinaXiv English translation.
"""

from .paper import Paper
from .translation import Translation
from .license import License

__all__ = ["Paper", "Translation", "License"]
