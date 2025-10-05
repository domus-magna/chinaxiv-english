#!/usr/bin/env python3
"""
PDF Download + Text Extraction Pipeline

Downloads PDFs from archive.org URLs and extracts text using pdfminer.
"""
from __future__ import annotations

import argparse
import os
import time
from pathlib import Path
from typing import Dict, List, Optional

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from .body_extract import extract_from_pdf
from .utils import log, read_json, write_json


@retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(3))
def download_pdf(url: str, output_path: str) -> bool:
    """
    Download a PDF from a URL.

    Args:
        url: PDF URL (e.g., archive.org)
        output_path: Local path to save PDF

    Returns:
        True if successful, False otherwise
    """
    try:
        # Follow redirects, set user agent to avoid blocks
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; ChinaXiv-English-Bot/1.0; +https://github.com/yourusername/chinaxiv-english)'
        }
        resp = requests.get(url, timeout=60, stream=True, allow_redirects=True, headers=headers)
        resp.raise_for_status()

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)

        return True
    except Exception as e:
        log(f"Failed to download {url}: {e}")
        return False


def fix_pdf_url(pdf_url: str, paper_id: str) -> str:
    """
    Fix archive.org PDF URLs which may have incorrect filenames.

    Archive.org stores files as: YYYYMM.NNNNNvV.pdf (lowercase v)
    But IA records may have: ChinaXiv-YYYYMM.NNNNNVV.pdf (with prefix, uppercase V)

    Args:
        pdf_url: Original PDF URL from IA records
        paper_id: Paper ID (e.g., ia-ChinaXiv-201705.00829V5)

    Returns:
        Corrected PDF URL
    """
    # Extract the ChinaXiv ID (e.g., 201705.00829V5)
    if paper_id.startswith('ia-ChinaXiv-'):
        chinaxiv_id = paper_id.replace('ia-ChinaXiv-', '')
        # Convert to lowercase v format: 201705.00829v5
        corrected_id = chinaxiv_id.replace('V', 'v').lower()
        # Reconstruct URL
        item_name = f"ChinaXiv-{chinaxiv_id}"
        corrected_url = f"https://archive.org/download/{item_name}/{corrected_id}.pdf"
        return corrected_url

    return pdf_url


def process_paper(paper_id: str, pdf_url: str, pdf_dir: str = "data/pdfs") -> Optional[Dict]:
    """
    Download PDF and extract text for a single paper.

    Args:
        paper_id: Paper identifier
        pdf_url: URL to PDF
        pdf_dir: Directory to store PDFs

    Returns:
        Dict with pdf_path and paragraphs, or None if failed
    """
    # Fix PDF URL if needed
    pdf_url = fix_pdf_url(pdf_url, paper_id)

    # Download PDF
    pdf_path = os.path.join(pdf_dir, f"{paper_id}.pdf")

    if not os.path.exists(pdf_path):
        log(f"Downloading {paper_id}...")
        success = download_pdf(pdf_url, pdf_path)
        if not success:
            return None
    else:
        log(f"PDF exists: {paper_id}")

    # Extract text
    log(f"Extracting text from {paper_id}...")
    paragraphs = extract_from_pdf(pdf_path)

    if not paragraphs:
        log(f"No text extracted from {paper_id}")
        return None

    log(f"Extracted {len(paragraphs)} paragraphs from {paper_id}")

    return {
        "pdf_path": pdf_path,
        "paragraphs": paragraphs,
        "num_paragraphs": len(paragraphs),
        "total_chars": sum(len(p) for p in paragraphs)
    }


def batch_download_and_extract(
    paper_ids: List[str],
    records_file: str = "data/records/ia_all_20251004_215726.json",
    pdf_dir: str = "data/pdfs",
    output_file: Optional[str] = None
) -> Dict[str, Dict]:
    """
    Download and extract text from multiple papers.

    Args:
        paper_ids: List of paper IDs to process
        records_file: Path to records JSON with pdf_url
        pdf_dir: Directory to store PDFs
        output_file: Optional path to save extraction results

    Returns:
        Dict mapping paper_id to extraction results
    """
    # Load records
    records = read_json(records_file)
    id_to_rec = {r['id']: r for r in records}

    results = {}

    for paper_id in paper_ids:
        if paper_id not in id_to_rec:
            log(f"Paper {paper_id} not found in records")
            continue

        rec = id_to_rec[paper_id]
        pdf_url = rec.get('pdf_url')

        if not pdf_url:
            log(f"No PDF URL for {paper_id}")
            continue

        result = process_paper(paper_id, pdf_url, pdf_dir)
        if result:
            results[paper_id] = result

        # Rate limit to be nice to archive.org
        time.sleep(0.5)

    # Save results
    if output_file:
        write_json(output_file, results)
        log(f"Saved extraction results to {output_file}")

    return results


def run_cli():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Download PDFs and extract text")
    parser.add_argument("--paper-ids", nargs="+", help="Specific paper IDs to process")
    parser.add_argument("--records", default="data/records/ia_all_20251004_215726.json",
                       help="Path to records JSON")
    parser.add_argument("--pdf-dir", default="data/pdfs", help="Directory for PDFs")
    parser.add_argument("--output", help="Output JSON file for extraction results")
    parser.add_argument("--test", action="store_true", help="Test on first 10 papers")

    args = parser.parse_args()

    if args.test:
        # Get first 10 papers from records
        records = read_json(args.records)
        paper_ids = [r['id'] for r in records[:10]]
        log(f"Testing on {len(paper_ids)} papers")
    elif args.paper_ids:
        paper_ids = args.paper_ids
    else:
        parser.error("Must specify --paper-ids or --test")

    results = batch_download_and_extract(
        paper_ids=paper_ids,
        records_file=args.records,
        pdf_dir=args.pdf_dir,
        output_file=args.output
    )

    log(f"\nProcessed {len(results)}/{len(paper_ids)} papers successfully")

    # Show summary
    if results:
        total_paras = sum(r['num_paragraphs'] for r in results.values())
        total_chars = sum(r['total_chars'] for r in results.values())
        log(f"Total paragraphs: {total_paras:,}")
        log(f"Total characters: {total_chars:,}")


if __name__ == "__main__":
    run_cli()
