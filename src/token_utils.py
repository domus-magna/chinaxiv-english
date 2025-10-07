"""
Token utilities for ChinaXiv English translation.
"""

from __future__ import annotations

from typing import List


def estimate_tokens(text: str) -> int:
    """
    Estimate token count from text length.

    Uses crude approximation: ~4 chars per token.

    Args:
        text: Input text

    Returns:
        Estimated token count
    """
    if not text:
        return 0
    return max(1, int(len(text) / 4))


def chunk_paragraphs(paragraphs: List[str], max_tokens: int = 1500) -> List[List[str]]:
    """
    Chunk paragraphs into groups that fit within token limit.

    Args:
        paragraphs: List of paragraphs
        max_tokens: Maximum tokens per chunk

    Returns:
        List of paragraph chunks
    """
    current: List[str] = []
    current_tokens = 0
    chunks: List[List[str]] = []

    for p in paragraphs:
        t = estimate_tokens(p)
        if current and current_tokens + t > max_tokens:
            chunks.append(current)
            current = [p]
            current_tokens = t
        else:
            current.append(p)
            current_tokens += t

    if current:
        chunks.append(current)

    return chunks
