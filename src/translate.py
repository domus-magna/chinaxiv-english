from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict, List, Optional

import requests

from .licenses import decide_derivatives_allowed
from .tex_guard import mask_math, unmask_math, verify_token_parity
from .body_extract import extract_body_paragraphs
from .utils import (
    chunk_paragraphs,
    log,
    openrouter_headers,
    read_json,
    write_json,
    estimate_tokens,
    compute_cost,
    append_cost_log,
    get_config,
    get_proxies,
)


SYSTEM_PROMPT = (
    "Translate from Simplified Chinese to English. Preserve all LaTeX commands and ⟪MATH_*⟫ "
    "placeholders exactly. Do not rewrite formulas. Obey glossary strictly."
)


from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import requests


class OpenRouterError(Exception):
    pass


@retry(wait=wait_exponential(min=1, max=20), stop=stop_after_attempt(5), retry=retry_if_exception_type(OpenRouterError))
def openrouter_translate(text: str, model: str, glossary: List[Dict[str, str]]) -> str:
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


def translate_field(text: str, model: str, glossary: List[Dict[str, str]], dry_run: bool = False) -> str:
    if not text:
        return ""
    masked, mappings = mask_math(text)
    if dry_run:
        translated = masked  # identity to preserve placeholders
    else:
        translated = openrouter_translate(masked, model, glossary)
    if not verify_token_parity(mappings, translated):
        raise RuntimeError("Math placeholder parity check failed")
    unmasked = unmask_math(translated, mappings)
    return unmasked


def translate_paragraphs(paragraphs: List[str], model: str, glossary: List[Dict[str, str]], dry_run: bool = False) -> List[str]:
    out: List[str] = []
    for p in paragraphs:
        out.append(translate_field(p, model, glossary, dry_run))
    return out


def translate_record(rec: Dict[str, Any], model: str, glossary: List[Dict[str, str]], dry_run: bool = False, force_full_text: bool = False) -> Dict[str, Any]:
    # Respect license gate (unless forced)
    cfg = get_config()
    rec = decide_derivatives_allowed(rec, cfg)

    # Allow full text if explicitly permitted by license OR if force_full_text is enabled
    allow_full = bool((rec.get("license") or {}).get("derivatives_allowed")) or force_full_text

    out: Dict[str, Any] = {"id": rec["id"], "oai_identifier": rec.get("oai_identifier")}
    title_src = rec.get("title") or ""
    abstract_src = rec.get("abstract") or ""
    out["title_en"] = translate_field(title_src, model, glossary, dry_run)
    out["abstract_en"] = translate_field(abstract_src, model, glossary, dry_run)
    out["license"] = rec.get("license")
    out["source_url"] = rec.get("source_url")
    out["pdf_url"] = rec.get("pdf_url")
    out["creators"] = rec.get("creators")
    out["subjects"] = rec.get("subjects")
    out["date"] = rec.get("date")

    body_en: Optional[List[str]] = None
    if allow_full:
        paras = extract_body_paragraphs(rec)
        if paras:
            body_en = translate_paragraphs(paras, model, glossary, dry_run)
    out["body_en"] = body_en

    # Cost tracking (approximate)
    cfg = get_config()
    in_toks = estimate_tokens(title_src) + estimate_tokens(abstract_src)
    out_toks = estimate_tokens(out.get("title_en") or "") + estimate_tokens(out.get("abstract_en") or "")
    if body_en:
        in_toks += sum(estimate_tokens(p) for p in paras)
        out_toks += sum(estimate_tokens(p) for p in body_en)
    cost = compute_cost(model, in_toks, out_toks, cfg)
    append_cost_log(rec["id"], model, in_toks, out_toks, cost)
    return out


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
    # Load selected records
    selected_path = os.path.join("data", "selected.json")
    selected = read_json(selected_path)

    # Find the record in selected.json first
    rec = next((r for r in selected if r['id'] == paper_id), None)

    # If not found, try harvested IA records
    if not rec:
        import glob
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
        from .pdf_pipeline import process_paper

        pdf_result = process_paper(paper_id, rec['pdf_url'])
        if pdf_result:
            # Add local pdf_path to record so extract_body_paragraphs can use it
            if 'files' not in rec:
                rec['files'] = {}
            rec['files']['pdf_path'] = pdf_result['pdf_path']
            log(f"Downloaded and extracted {pdf_result['num_paragraphs']} paragraphs from PDF")

    # Get config
    cfg = get_config()
    model = cfg.get("models", {}).get("default_slug", "deepseek/deepseek-v3.2-exp")
    glossary = cfg.get("glossary", [])

    # Translate (force full text if with_full_text is enabled)
    tr = translate_record(rec, model, glossary, dry_run=dry_run, force_full_text=with_full_text)

    # Apply formatting/prettification
    from .format_translation import format_translation
    tr = format_translation(tr)

    # Save
    out_dir = os.path.join("data", "translated")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{rec['id']}.json")
    write_json(out_path, tr)

    return out_path


def run_cli() -> None:
    parser = argparse.ArgumentParser(description="Translate selected records via OpenRouter.")
    parser.add_argument("--selected", required=True, help="Path to selected records JSON")
    parser.add_argument("--dry-run", action="store_true", help="Skip API calls and echo masked text")
    parser.add_argument("--model", help="Override model slug")
    args = parser.parse_args()

    cfg = get_config()
    model = args.model or cfg.get("models", {}).get("default_slug", "deepseek/deepseek-v3.2-exp")
    glossary = cfg.get("glossary", [])

    selected = read_json(args.selected)
    out_dir = os.path.join("data", "translated")
    os.makedirs(out_dir, exist_ok=True)
    for rec in selected:
        tr = translate_record(rec, model, glossary, dry_run=args.dry_run)
        out_path = os.path.join(out_dir, f"{rec['id']}.json")
        write_json(out_path, tr)
        log(f"Translated {rec['id']} → {out_path}")


if __name__ == "__main__":
    run_cli()
