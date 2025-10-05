"""
Translation data model for ChinaXiv English translation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .paper import Paper


@dataclass
class Translation:
    """Translation data model."""
    
    id: str
    oai_identifier: Optional[str] = None
    title_en: Optional[str] = None
    abstract_en: Optional[str] = None
    body_en: Optional[List[str]] = None
    creators: Optional[List[str]] = None
    subjects: Optional[List[str]] = None
    date: Optional[str] = None
    license: Optional[Dict[str, Any]] = None
    source_url: Optional[str] = None
    pdf_url: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Translation:
        """Create Translation from dictionary."""
        return cls(
            id=data["id"],
            oai_identifier=data.get("oai_identifier"),
            title_en=data.get("title_en"),
            abstract_en=data.get("abstract_en"),
            body_en=data.get("body_en"),
            creators=data.get("creators"),
            subjects=data.get("subjects"),
            date=data.get("date"),
            license=data.get("license"),
            source_url=data.get("source_url"),
            pdf_url=data.get("pdf_url")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Translation to dictionary."""
        result = {
            "id": self.id
        }
        
        if self.oai_identifier is not None:
            result["oai_identifier"] = self.oai_identifier
        if self.title_en is not None:
            result["title_en"] = self.title_en
        if self.abstract_en is not None:
            result["abstract_en"] = self.abstract_en
        result["body_en"] = self.body_en
        result["creators"] = self.creators
        result["subjects"] = self.subjects
        result["date"] = self.date
        result["license"] = self.license
        result["source_url"] = self.source_url
        result["pdf_url"] = self.pdf_url
            
        return result
    
    @classmethod
    def from_paper(cls, paper: Paper) -> Translation:
        """Create Translation from Paper."""
        return cls(
            id=paper.id,
            oai_identifier=paper.oai_identifier,
            creators=paper.creators,
            subjects=paper.subjects,
            date=paper.date,
            license=paper.license.to_dict() if paper.license else None,
            source_url=paper.source_url,
            pdf_url=paper.pdf_url
        )
    
    def has_full_text(self) -> bool:
        """Check if translation includes full text."""
        return bool(self.body_en)
    
    def get_title(self) -> str:
        """Get English title, fallback to empty string."""
        return self.title_en or ""
    
    def get_abstract(self) -> str:
        """Get English abstract, fallback to empty string."""
        return self.abstract_en or ""
    
    def get_body_text(self) -> str:
        """Get body text as a single string."""
        if not self.body_en:
            return ""
        return "\n\n".join(self.body_en)
    
    def get_authors_string(self) -> str:
        """Get authors as a comma-separated string."""
        if not self.creators:
            return ""
        return ", ".join(self.creators)
    
    def get_subjects_string(self) -> str:
        """Get subjects as a comma-separated string."""
        if not self.subjects:
            return ""
        return ", ".join(self.subjects)
    
    def is_derivatives_allowed(self) -> bool:
        """Check if derivatives are allowed based on license."""
        if not self.license:
            return False
        return bool(self.license.get("derivatives_allowed", False))
    
    def get_search_index_entry(self) -> Dict[str, Any]:
        """Get search index entry for this translation."""
        return {
            "id": self.id,
            "title": self.get_title(),
            "authors": self.get_authors_string(),
            "abstract": self.get_abstract(),
            "subjects": self.get_subjects_string(),
            "date": self.date or ""
        }
