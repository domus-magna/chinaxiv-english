"""
Translation service for ChinaXiv English translation.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..config import get_config, get_proxies
from ..http_client import openrouter_headers
from ..tex_guard import mask_math, unmask_math, verify_token_parity
from ..body_extract import extract_body_paragraphs
from ..token_utils import chunk_paragraphs
from ..cost_tracker import compute_cost, append_cost_log
from ..logging import log


SYSTEM_PROMPT = (
    "Translate from Simplified Chinese to English. Preserve all LaTeX commands and ⟪MATH_*⟫ "
    "placeholders exactly. Do not rewrite formulas. Obey glossary strictly."
)


class OpenRouterError(Exception):
    """OpenRouter API error."""
    pass


class TranslationService:
    """Service for handling translation operations."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize translation service.
        
        Args:
            config: Configuration dictionary (optional)
        """
        self.config = config or get_config()
        self.model = self.config.get("models", {}).get("default_slug", "deepseek/deepseek-v3.2-exp")
        self.glossary = self.config.get("glossary", [])
    
    @retry(
        wait=wait_exponential(min=1, max=20), 
        stop=stop_after_attempt(5), 
        retry=retry_if_exception_type(OpenRouterError)
    )
    def _call_openrouter(self, text: str, model: str, glossary: List[Dict[str, str]]) -> str:
        """
        Call OpenRouter API for translation.
        
        Args:
            text: Text to translate
            model: Model to use
            glossary: Translation glossary
            
        Returns:
            Translated text
            
        Raises:
            OpenRouterError: On API failure
        """
        # prepend glossary as instructions
        glossary_str = "\n".join(f"{g['zh']} => {g['en']}" for g in glossary)
        system = SYSTEM_PROMPT + ("\nGlossary (zh => en):\n" + glossary_str if glossary_str else "")
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": text},
            ],
            "temperature": 0.2,
        }
        
        proxies, source = get_proxies()
        try:
            kwargs = {
                "headers": openrouter_headers(),
                "data": json.dumps(payload),
                "timeout": (15, 90) if source != "none" else (10, 60),
            }
            if source == "config" and proxies:
                kwargs["proxies"] = proxies
            resp = requests.post("https://openrouter.ai/api/v1/chat/completions", **kwargs)
        except requests.RequestException as e:
            raise OpenRouterError(str(e))
        
        if not resp.ok:
            raise OpenRouterError(f"OpenRouter error {resp.status_code}: {resp.text[:200]}")
        
        data = resp.json()
        try:
            return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            raise RuntimeError(f"Invalid OpenRouter response: {e}")
    
    def translate_field(self, text: str, model: Optional[str] = None, dry_run: bool = False) -> str:
        """
        Translate a single field with math preservation.
        
        Args:
            text: Text to translate
            model: Model to use (defaults to service model)
            dry_run: If True, skip actual translation
            
        Returns:
            Translated text
            
        Raises:
            RuntimeError: On math parity check failure
        """
        if not text:
            return ""
        
        model = model or self.model
        masked, mappings = mask_math(text)
        
        if dry_run:
            translated = masked  # identity to preserve placeholders
        else:
            translated = self._call_openrouter(masked, model, self.glossary)
        
        if not verify_token_parity(mappings, translated):
            raise RuntimeError("Math placeholder parity check failed")
        
        unmasked = unmask_math(translated, mappings)
        return unmasked
    
    def translate_paragraphs(self, paragraphs: List[str], model: Optional[str] = None, dry_run: bool = False) -> List[str]:
        """
        Translate multiple paragraphs.
        
        Args:
            paragraphs: List of paragraphs to translate
            model: Model to use (defaults to service model)
            dry_run: If True, skip actual translation
            
        Returns:
            List of translated paragraphs
        """
        model = model or self.model
        out: List[str] = []
        for p in paragraphs:
            out.append(self.translate_field(p, model, dry_run))
        return out
    
    def translate_record(self, record: Dict[str, Any], dry_run: bool = False, force_full_text: bool = False) -> Dict[str, Any]:
        """
        Translate a complete record.
        
        Args:
            record: Record to translate
            dry_run: If True, skip actual translation
            force_full_text: If True, translate full text regardless of license
            
        Returns:
            Translated record
        """
        from ..licenses import decide_derivatives_allowed
        
        # Respect license gate (unless forced)
        record = decide_derivatives_allowed(record, self.config)
        
        # Allow full text if explicitly permitted by license OR if force_full_text is enabled
        allow_full = bool((record.get("license") or {}).get("derivatives_allowed")) or force_full_text
        
        out: Dict[str, Any] = {
            "id": record["id"], 
            "oai_identifier": record.get("oai_identifier")
        }
        
        title_src = record.get("title") or ""
        abstract_src = record.get("abstract") or ""
        
        out["title_en"] = self.translate_field(title_src, dry_run=dry_run)
        out["abstract_en"] = self.translate_field(abstract_src, dry_run=dry_run)
        out["license"] = record.get("license")
        out["source_url"] = record.get("source_url")
        out["pdf_url"] = record.get("pdf_url")
        out["creators"] = record.get("creators")
        out["subjects"] = record.get("subjects")
        out["date"] = record.get("date")
        
        body_en: Optional[List[str]] = None
        if allow_full:
            paras = extract_body_paragraphs(record)
            if paras:
                body_en = self.translate_paragraphs(paras, dry_run=dry_run)
        
        out["body_en"] = body_en
        
        # Cost tracking (approximate)
        from ..token_utils import estimate_tokens
        in_toks = estimate_tokens(title_src) + estimate_tokens(abstract_src)
        out_toks = estimate_tokens(out.get("title_en") or "") + estimate_tokens(out.get("abstract_en") or "")
        
        if body_en:
            in_toks += sum(estimate_tokens(p) for p in paras)
            out_toks += sum(estimate_tokens(p) for p in body_en)
        
        cost = compute_cost(self.model, in_toks, out_toks, self.config)
        append_cost_log(record["id"], self.model, in_toks, out_toks, cost)
        
        return out
    
    def translate_paper(self, paper_id: str, dry_run: bool = False, with_full_text: bool = True) -> str:
        """
        Translate a single paper by ID.
        
        Args:
            paper_id: Paper identifier
            dry_run: If True, skip actual translation
            with_full_text: If True, download PDF and translate full text
            
        Returns:
            Path to translated JSON file
            
        Raises:
            ValueError: If paper not found
        """
        from ..file_service import read_json, write_json
        import glob
        import os
        
        # Load selected records
        selected_path = os.path.join("data", "selected.json")
        selected = read_json(selected_path)
        
        # Find the record in selected.json first
        rec = next((r for r in selected if r['id'] == paper_id), None)
        
        # If not found, try harvested IA records
        if not rec:
            records_dir = os.path.join("data", "records")
            ia_files = sorted(glob.glob(os.path.join(records_dir, "ia_*.json")), reverse=True)
            
            for ia_file in ia_files:
                ia_records = read_json(ia_file)
                rec = next((r for r in ia_records if r['id'] == paper_id), None)
                if rec:
                    break
        
        if not rec:
            raise ValueError(f"Paper {paper_id} not found in selected.json or harvested IA records")
        
        # Download PDF and extract text if requested
        if with_full_text and rec.get('pdf_url'):
            from ..pdf_pipeline import process_paper
            
            pdf_result = process_paper(paper_id, rec['pdf_url'])
            if pdf_result:
                # Add local pdf_path to record so extract_body_paragraphs can use it
                if 'files' not in rec:
                    rec['files'] = {}
                rec['files']['pdf_path'] = pdf_result['pdf_path']
                log(f"Downloaded and extracted {pdf_result['num_paragraphs']} paragraphs from PDF")
        
        # Translate (force full text if with_full_text is enabled)
        tr = self.translate_record(rec, dry_run=dry_run, force_full_text=with_full_text)
        
        # Apply formatting/prettification
        from ..format_translation import format_translation
        tr = format_translation(tr)
        
        # Save
        out_dir = os.path.join("data", "translated")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"{rec['id']}.json")
        write_json(out_path, tr)
        
        return out_path
