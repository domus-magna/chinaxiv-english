"""
Data processing utilities for ChinaXiv English translation.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Tuple


def utc_date_range_str(days_back: int = 1) -> Tuple[str, str]:
    """
    Get UTC date range string.
    
    Args:
        days_back: Number of days back from today
        
    Returns:
        Tuple of (start_date, end_date) in ISO format
    """
    # Yesterday UTC by default
    now = datetime.now(timezone.utc)
    start = (now - timedelta(days=days_back)).date()
    end = start
    return start.isoformat(), end.isoformat()


def stable_id_from_oai(oai_identifier: str) -> str:
    """
    Extract stable ID from OAI identifier.
    
    Args:
        oai_identifier: OAI identifier (e.g., oai:chinaxiv.org:YYYY-XXXXX)
        
    Returns:
        Stable ID (e.g., YYYY-XXXXX)
    """
    # e.g., oai:chinaxiv.org:YYYY-XXXXX -> YYYY-XXXXX
    return oai_identifier.split(":")[-1]
