"""
License service for ChinaXiv English translation.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..config import get_config


class LicenseService:
    """Service for handling license operations."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize license service.
        
        Args:
            config: Configuration dictionary (optional)
        """
        self.config = config or get_config()
        self.license_mapping = self.config.get("license_mapping", {})
    
    def decide_derivatives_allowed(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decide if derivatives are allowed based on license.
        
        Args:
            record: Record to check
            
        Returns:
            Updated record with license information
        """
        from ..licenses import decide_derivatives_allowed
        return decide_derivatives_allowed(record, self.config)
    
    def parse_license_mapping(self) -> Dict[str, Dict[str, Any]]:
        """
        Parse license mapping from configuration.
        
        Returns:
            License mapping dictionary
        """
        from ..licenses import parse_license_mapping
        return parse_license_mapping(self.config)
    
    def is_derivative_allowed(self, license_info: Optional[Dict[str, Any]]) -> bool:
        """
        Check if derivatives are allowed for a license.
        
        Args:
            license_info: License information dictionary
            
        Returns:
            True if derivatives are allowed
        """
        if not license_info:
            return False
        return bool(license_info.get("derivatives_allowed", False))
    
    def get_license_summary(self, record: Dict[str, Any]) -> str:
        """
        Get a summary of license information for a record.
        
        Args:
            record: Record to summarize
            
        Returns:
            License summary string
        """
        license_info = record.get("license", {})
        if not license_info:
            return "No license information"
        
        license_type = license_info.get("type", "Unknown")
        derivatives_allowed = license_info.get("derivatives_allowed", False)
        
        status = "Allowed" if derivatives_allowed else "Not allowed"
        return f"{license_type} - Derivatives: {status}"
