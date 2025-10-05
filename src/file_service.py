"""
File service for ChinaXiv English translation.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Dict


def ensure_dir(path: str) -> None:
    """Ensure directory exists."""
    os.makedirs(path, exist_ok=True)


def write_json(path: str, data: Any) -> None:
    """
    Write JSON data atomically to reduce risk of partial files.
    
    Args:
        path: File path
        data: Data to write
    """
    ensure_dir(os.path.dirname(path))
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def read_json(path: str) -> Any:
    """
    Read JSON data from file.
    
    Args:
        path: File path
        
    Returns:
        Parsed JSON data
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def read_text(path: str) -> str:
    """
    Read text from file.
    
    Args:
        path: File path
        
    Returns:
        File contents as string
    """
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_text(path: str, content: str) -> None:
    """
    Write text to file.
    
    Args:
        path: File path
        content: Content to write
    """
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def save_raw_xml(content: str, day: str, part: int) -> str:
    """
    Save raw XML content to file.
    
    Args:
        content: XML content
        day: Day string (YYYY-MM-DD)
        part: Part number
        
    Returns:
        Path to saved file
    """
    path = os.path.join("data", "raw_xml", day, f"part_{part}.xml")
    write_text(path, content)
    return path


def read_seen(path: str = "data/seen.json") -> Dict[str, Any]:
    """
    Read seen.json file.
    
    Args:
        path: Path to seen.json
        
    Returns:
        Seen data dictionary
    """
    if not os.path.exists(path):
        return {"ids": []}
    return read_json(path)


def write_seen(seen: Dict[str, Any], path: str = "data/seen.json") -> None:
    """
    Write seen.json file.
    
    Args:
        seen: Seen data dictionary
        path: Path to seen.json
    """
    write_json(path, seen)


def sanitize_filename(name: str) -> str:
    """
    Sanitize filename by replacing invalid characters.
    
    Args:
        name: Original filename
        
    Returns:
        Sanitized filename
    """
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name)
