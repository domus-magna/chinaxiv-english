"""
Translation module for ChinaXiv English translation.

This module provides backward compatibility by delegating to the new service layer.
"""
from __future__ import annotations

import argparse
import os
from typing import Any, Dict, List, Optional

from .services.translation_service import TranslationService
from .services.license_service import LicenseService
from .config import get_config
from .file_service import read_json, write_json
from .logging_utils import log


# Backward compatibility functions
def translate_field(text: str, model: str, glossary: List[Dict[str, str]], dry_run: bool = False) -> str:
    """
    Translate a single field with math preservation.
    
    Args:
        text: Text to translate
        model: Model to use
        glossary: Translation glossary
        dry_run: If True, skip actual translation
        
    Returns:
        Translated text
    """
    service = TranslationService()
    return service.translate_field(text, model, dry_run)


def translate_paragraphs(paragraphs: List[str], model: str, glossary: List[Dict[str, str]], dry_run: bool = False) -> List[str]:
    """
    Translate multiple paragraphs.
    
    Args:
        paragraphs: List of paragraphs to translate
        model: Model to use
        glossary: Translation glossary
        dry_run: If True, skip actual translation
        
    Returns:
        List of translated paragraphs
    """
    service = TranslationService()
    return service.translate_paragraphs(paragraphs, model, dry_run)


def translate_record(rec: Dict[str, Any], model: str, glossary: List[Dict[str, str]], dry_run: bool = False, force_full_text: bool = False) -> Dict[str, Any]:
    """
    Translate a complete record.
    
    Args:
        rec: Record to translate
        model: Model to use
        glossary: Translation glossary
        dry_run: If True, skip actual translation
        force_full_text: If True, translate full text regardless of license
        
    Returns:
        Translated record
    """
    service = TranslationService()
    return service.translate_record(rec, dry_run, force_full_text)


def translate_paper(paper_id: str, dry_run: bool = False, with_full_text: bool = True) -> str:
    """
    Translate a single paper by ID.
    
    Args:
        paper_id: Paper identifier
        dry_run: If True, skip actual translation
        with_full_text: If True, download PDF and translate full text
        
    Returns:
        Path to translated JSON file
    """
    service = TranslationService()
    return service.translate_paper(paper_id, dry_run, with_full_text)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Translate ChinaXiv papers")
    parser.add_argument("paper_id", help="Paper ID to translate")
    parser.add_argument("--dry-run", action="store_true", help="Dry run (no actual translation)")
    parser.add_argument("--no-full-text", action="store_true", help="Skip full text translation")
    
    args = parser.parse_args()
    
    try:
        result_path = translate_paper(
            args.paper_id, 
            dry_run=args.dry_run, 
            with_full_text=not args.no_full_text
        )
        print(f"Translation saved to: {result_path}")
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())