"""
Translation service for ChinaXiv English translation.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..config import get_config, get_proxies
from ..http_client import openrouter_headers, parse_openrouter_error
from ..monitoring import monitoring_service, alert_critical
from ..tex_guard import mask_math, unmask_math, verify_token_parity
from ..body_extract import extract_body_paragraphs
from ..token_utils import chunk_paragraphs
from ..cost_tracker import compute_cost, append_cost_log
from ..logging_utils import log
from ..models import Paper, Translation


SYSTEM_PROMPT = (
    "You are a professional scientific translator specializing in academic papers. "
    "Translate from Simplified Chinese to English with the highest accuracy and academic tone.\n\n"
    "CRITICAL REQUIREMENTS:\n"
    "1. Preserve ALL LaTeX commands and ⟪MATH_*⟫ placeholders exactly - do not modify, translate, or rewrite any mathematical formulas\n"
    "2. Preserve ALL citation commands (\\cite{}, \\ref{}, \\eqref{}, etc.) exactly as they appear\n"
    "3. Maintain academic tone and formal scientific writing style\n"
    "4. Use precise technical terminology - obey the glossary strictly\n"
    "5. Preserve section structure and paragraph organization\n"
    "6. Translate all content completely - do not omit any information\n\n"
    "OUTPUT RULES:\n"
    "- Return ONLY the translated text for the given input (no explanations, no quotes, no headings you invent).\n"
    "- Keep one output paragraph per input paragraph; do not merge or split.\n"
    "- Do NOT add Markdown formatting unless it is present in the source.\n"
    "- Preserve original line breaks within the paragraph when meaningful; otherwise use standard English sentence spacing.\n\n"
    "FORMATTING GUIDELINES:\n"
    "- Keep mathematical expressions in their original LaTeX format\n"
    "- Preserve equation numbers and references\n"
    "- Maintain proper academic paragraph structure\n"
    "- Use formal scientific language appropriate for research papers\n\n"
    "Remember: Mathematical content and citations must remain untouched - only translate the Chinese text."
)


class OpenRouterError(Exception):
    """OpenRouter API error (non-retryable by default)."""
    def __init__(self, message: str, *, code: Optional[str] = None, retryable: bool = False, fallback_ok: bool = True) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable
        self.fallback_ok = fallback_ok


class OpenRouterRetryableError(OpenRouterError):
    """Retryable OpenRouter API error (e.g., 429, 5xx, transient network)."""
    def __init__(self, message: str, *, code: Optional[str] = None, fallback_ok: bool = True) -> None:
        super().__init__(message, code=code, retryable=True, fallback_ok=fallback_ok)


class OpenRouterFatalError(OpenRouterError):
    """Fatal OpenRouter API error (e.g., invalid key, insufficient funds)."""
    def __init__(self, message: str, *, code: Optional[str] = None, fallback_ok: bool = False) -> None:
        super().__init__(message, code=code, retryable=False, fallback_ok=fallback_ok)


class TranslationValidationError(Exception):
    """Translation validation error."""
    pass


class MathPreservationError(Exception):
    """Math preservation error."""
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
        retry=retry_if_exception_type(OpenRouterRetryableError)
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
            # Record network error
            try:
                monitoring_service.record_error(service="openrouter", message=str(e), status=None, code="network_error", metadata={"model": model})
            except Exception:
                pass
            raise OpenRouterRetryableError(f"Network error: {e}", code="network_error")

        if not resp.ok:
            info = parse_openrouter_error(resp)
            status = info["status"]
            code = info["code"]
            message = info["message"] or f"OpenRouter error {status}"
            # Record error for budget tracking
            try:
                monitoring_service.record_error(
                    service="openrouter",
                    message=message,
                    status=status,
                    code=code or None,
                    metadata={"model": model},
                )
            except Exception:
                pass
            if info["retryable"]:
                raise OpenRouterRetryableError(f"{message}", code=code, fallback_ok=info["fallback_ok"])
            # fatal or non-retryable – decide if fallback to alternate models makes sense
            if not info["fallback_ok"]:
                # Immediate critical alert for fatal auth/payment
                try:
                    alert_critical(
                        "OpenRouter Fatal Error",
                        message,
                        source="translation_service",
                        metadata={"status": status, "code": code or "unknown", "model": model}
                    )
                except Exception:
                    pass
                raise OpenRouterFatalError(message, code=code, fallback_ok=False)
            raise OpenRouterError(message, code=code, retryable=False, fallback_ok=True)

        data = resp.json()
        try:
            return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            raise RuntimeError(f"Invalid OpenRouter response: {e}")
    
    def translate_field(
        self,
        text: str,
        model: Optional[str] = None,
        dry_run: bool = False,
        glossary_override: Optional[List[Dict[str, str]]] = None,
    ) -> str:
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
        glossary_eff = glossary_override if glossary_override is not None else self.glossary
        masked, mappings = mask_math(text)
        
        if dry_run:
            translated = masked  # identity to preserve placeholders
        else:
            translated = self._call_openrouter_with_fallback(masked, model, glossary_eff)
        
        if not verify_token_parity(mappings, translated):
            raise MathPreservationError("Math placeholder parity check failed")
        
        unmasked = unmask_math(translated, mappings)
        
        # Additional validation checks
        self._validate_translation(text, unmasked)
        
        return unmasked
    
    def translate_paragraphs(
        self,
        paragraphs: List[str],
        model: Optional[str] = None,
        dry_run: bool = False,
        glossary_override: Optional[List[Dict[str, str]]] = None,
    ) -> List[str]:
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
        glossary_eff = self.glossary if glossary_override is None else glossary_override
        # Optional batching to reduce API calls; disabled by default
        batch_enabled = (
            (self.config.get("translation") or {}).get("batch_paragraphs") is True
        )
        if not batch_enabled:
            out: List[str] = []
            for p in paragraphs:
                out.append(self.translate_field(p, model, dry_run, glossary_override=glossary_eff))
            return out

        # Batch mode: chunk paragraphs into token-limited groups and join/split
        out: List[str] = []
        SENTINEL = "\n\n⟪PARA_BREAK⟫\n\n"
        for group in chunk_paragraphs(paragraphs):
            joined = SENTINEL.join(group)
            translated = self.translate_field(joined, model, dry_run, glossary_override=glossary_eff)
            parts = [s.strip() for s in translated.split(SENTINEL)]
            # Ensure we preserve count; if mismatch, fall back to per-paragraph
            if len(parts) != len(group):
                for p in group:
                    out.append(self.translate_field(p, model, dry_run, glossary_override=glossary_eff))
            else:
                out.extend(parts)
        return out
    
    def translate_record(
        self,
        record: Dict[str, Any],
        dry_run: bool = False,
        force_full_text: bool = False,
        glossary_override: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Translate a complete record.
        
        Args:
            record: Record to translate
            dry_run: If True, skip actual translation
            force_full_text: If True, translate full text regardless of license (always True now)
            
        Returns:
            Translated record
        """
        # DISABLED: We do not care about licenses. All papers translated in full.
        # from ..licenses import decide_derivatives_allowed
        
        # DISABLED: License gate - always translate full text
        # record = decide_derivatives_allowed(record, self.config)
        
        # Convert to Paper model
        paper = Paper.from_dict(record)
        
        # DISABLED: Always allow full text - we don't care about licenses
        allow_full = True
        
        # Create translation from paper
        translation = Translation.from_paper(paper)
        
        # Translate title and abstract
        title_src = paper.title or ""
        abstract_src = paper.abstract or ""
        
        translation.title_en = self.translate_field(title_src, dry_run=dry_run, glossary_override=glossary_override)
        translation.abstract_en = self.translate_field(abstract_src, dry_run=dry_run, glossary_override=glossary_override)
        
        # Translate body if allowed
        if allow_full:
            paras = extract_body_paragraphs(record)
            if paras:
                translation.body_en = self.translate_paragraphs(paras, dry_run=dry_run, glossary_override=glossary_override)
        
        # Cost tracking (approximate)
        from ..token_utils import estimate_tokens
        in_toks = estimate_tokens(title_src) + estimate_tokens(abstract_src)
        out_toks = estimate_tokens(translation.title_en or "") + estimate_tokens(translation.abstract_en or "")
        
        if translation.body_en:
            in_toks += sum(estimate_tokens(p) for p in paras)
            out_toks += sum(estimate_tokens(p) for p in translation.body_en)
        
        cost = compute_cost(self.model, in_toks, out_toks, self.config)
        append_cost_log(paper.id, self.model, in_toks, out_toks, cost)
        
        return translation.to_dict()
    
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
        
        # Translate (always translate full text - we don't care about licenses)
        tr = self.translate_record(rec, dry_run=dry_run, force_full_text=True)
        
        # Apply formatting/prettification (heuristic baseline)
        from ..format_translation import format_translation
        tr = format_translation(tr)

        # Optional: LLM or heuristic Markdown formatting pass
        try:
            from .formatting_service import FormattingService
            fmt_service = FormattingService(self.config)
            tr = fmt_service.format_translation(tr, dry_run=dry_run)
        except Exception as e:
            # Non-fatal: fallback to existing formatted fields
            log(f"Formatting service error (non-fatal): {e}")
        
        # Save
        out_dir = os.path.join("data", "translated")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"{rec['id']}.json")
        write_json(out_path, tr)
        
        return out_path
    
    def _validate_translation(self, original: str, translated: str) -> None:
        """
        Perform additional validation checks on translation quality.
        
        Args:
            original: Original Chinese text
            translated: Translated English text
            
        Raises:
            TranslationValidationError: If validation fails
        """
        # Check for empty translation
        if not translated or translated.strip() == "":
            raise TranslationValidationError("Translation is empty")
        
        # Check for reasonable length (translated should be roughly 1.2-2x original length)
        orig_len = len(original.strip())
        trans_len = len(translated.strip())
        
        if orig_len > 0:
            ratio = trans_len / orig_len
            if ratio < 0.5 or ratio > 3.0:
                log(f"Warning: Unusual translation length ratio: {ratio:.2f} (original: {orig_len}, translated: {trans_len})")
        
        # Check for common translation issues
        if "⟪MATH_" in translated:
            raise TranslationValidationError("Math placeholders found in final translation")
        
        # Check for citation preservation
        import re
        orig_citations = re.findall(r'\\cite\{[^}]*\}', original)
        trans_citations = re.findall(r'\\cite\{[^}]*\}', translated)
        
        if len(orig_citations) != len(trans_citations):
            log(f"Warning: Citation count mismatch (original: {len(orig_citations)}, translated: {len(trans_citations)})")
        
        # Check for LaTeX command preservation
        orig_latex = re.findall(r'\\[a-zA-Z]+\{[^}]*\}', original)
        trans_latex = re.findall(r'\\[a-zA-Z]+\{[^}]*\}', translated)
        
        if len(orig_latex) != len(trans_latex):
            log(f"Warning: LaTeX command count mismatch (original: {len(orig_latex)}, translated: {len(trans_latex)})")
    
    def _call_openrouter_with_fallback(self, text: str, model: str, glossary: List[Dict[str, str]]) -> str:
        """
        Call OpenRouter API with fallback to alternate models on failure.
        
        Args:
            text: Text to translate
            model: Primary model to use
            glossary: Translation glossary
            
        Returns:
            Translated text
            
        Raises:
            OpenRouterError: If all models fail
        """
        models_to_try = [model] + self.config.get("models", {}).get("alternates", [])
        
        last_error = None
        for model_to_try in models_to_try:
            try:
                log(f"Attempting translation with model: {model_to_try}")
                return self._call_openrouter(text, model_to_try, glossary)
            except OpenRouterError as e:
                last_error = e
                log(f"Model {model_to_try} failed: {e}")
                # If the failure cannot be fixed by switching models, stop early
                if isinstance(e, OpenRouterFatalError) and not getattr(e, "fallback_ok", True):
                    break
                continue

        # All models failed
        raise OpenRouterError(f"All translation models failed. Last error: {last_error}")
