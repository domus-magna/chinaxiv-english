"""
License data model for ChinaXiv English translation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class License:
    """License information for a paper."""

    raw: Optional[str] = None
    label: Optional[str] = None
    derivatives_allowed: Optional[bool] = None
    badge: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> License:
        """Create License from dictionary."""
        if not data:
            return cls()

        return cls(
            raw=data.get("raw"),
            label=data.get("label"),
            derivatives_allowed=data.get("derivatives_allowed"),
            badge=data.get("badge"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert License to dictionary."""
        result = {}
        if self.raw is not None:
            result["raw"] = self.raw
        if self.label is not None:
            result["label"] = self.label
        if self.derivatives_allowed is not None:
            result["derivatives_allowed"] = self.derivatives_allowed
        if self.badge is not None:
            result["badge"] = self.badge
        return result

    def is_derivatives_allowed(self) -> bool:
        """Check if derivatives are allowed."""
        return bool(self.derivatives_allowed)

    def get_summary(self) -> str:
        """Get a summary of license information."""
        if not self.label and not self.raw:
            return "No license information"

        license_type = self.label or "Unknown"
        derivatives_allowed = self.is_derivatives_allowed()

        status = "Allowed" if derivatives_allowed else "Not allowed"
        return f"{license_type} - Derivatives: {status}"
