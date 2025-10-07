"""
Logging utilities for ChinaXiv English translation.
"""

from __future__ import annotations

from datetime import datetime, timezone


def log(msg: str) -> None:
    """
    Log message with timestamp.

    Args:
        msg: Message to log
    """
    print(f"[{now_iso()}] {msg}")


def now_iso() -> str:
    """Get current UTC time as ISO string."""
    return datetime.now(timezone.utc).isoformat()
