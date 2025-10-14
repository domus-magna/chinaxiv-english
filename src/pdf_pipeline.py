#!/usr/bin/env python3
"""
PDF Download + Text Extraction Pipeline

Downloads PDFs from provided URLs and extracts text using pdfminer.
"""
from __future__ import annotations

import argparse
import os
import json
import shutil
import subprocess
import time
from typing import Dict, List, Optional

from tenacity import retry, stop_after_attempt, wait_exponential
from .http_client import get_session
from .config import get_proxies
from .body_extract import extract_from_pdf
from .utils import log, read_json, write_json


@retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(3))
def download_pdf(url: str, output_path: str) -> bool:
    """
    Download a PDF from a URL.

    Args:
        url: PDF URL
        output_path: Local path to save PDF

    Returns:
        True if successful, False otherwise
    """
    try:
        session = get_session()
        proxies, source = get_proxies()
        kwargs = {
            "timeout": 60,
            "stream": True,
            "allow_redirects": True,
        }
        if source == "config" and proxies:
            kwargs["proxies"] = proxies

        resp = session.get(url, **kwargs)
        resp.raise_for_status()

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if not chunk:
                    continue
                f.write(chunk)

        return True
    except Exception as e:
        log(f"Failed to download {url}: {e}")
        return False


def fix_pdf_url(pdf_url: str, paper_id: str) -> str:
    """Return PDF URL unchanged (no IA-specific rewriting)."""
    return pdf_url


def process_paper(
    paper_id: str, pdf_url: str, pdf_dir: str = "data/pdfs"
) -> Optional[Dict]:
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
    total_chars = sum(len(p) for p in paragraphs) if paragraphs else 0

    # OCR detection thresholds (simple heuristic)
    need_ocr = False
    DETECT_CHAR_THRESHOLD = 1500  # if less than this many characters, likely scanned
    if not paragraphs or total_chars < DETECT_CHAR_THRESHOLD:
        need_ocr = True

    # Record detection report
    try:
        report_dir = os.path.join("reports")
        os.makedirs(report_dir, exist_ok=True)
        detect_path = os.path.join(report_dir, "ocr_detection_report.json")
        data = {}
        if os.path.exists(detect_path):
            with open(detect_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        data[paper_id] = {
            "pdf_path": pdf_path,
            "pre_ocr_chars": total_chars,
            "need_ocr": bool(need_ocr),
        }
        with open(detect_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

    # Run OCR if needed and possible
    if need_ocr and shutil.which("ocrmypdf") and shutil.which("tesseract"):
        try:
            ocr_dir = os.path.join(pdf_dir, "ocr")
            os.makedirs(ocr_dir, exist_ok=True)
            ocr_out = os.path.join(ocr_dir, f"{paper_id}.pdf")
            # Use chi_sim+eng to cover Chinese and English; skip pages with text
            cmd = [
                "ocrmypdf",
                "--skip-text",
                "--optimize", "0",
                "--language", "chi_sim+eng",
                pdf_path,
                ocr_out,
            ]
            log(f"Running OCR for {paper_id}…")
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # Re-extract
            paragraphs = extract_from_pdf(ocr_out)
            post_chars = sum(len(p) for p in paragraphs) if paragraphs else 0
            # Record execution report
            try:
                exec_path = os.path.join(report_dir, "ocr_execution_report.json")
                exec_data = {}
                if os.path.exists(exec_path):
                    with open(exec_path, "r", encoding="utf-8") as f:
                        exec_data = json.load(f)
                exec_data[paper_id] = {
                    "ran_ocr": True,
                    "ocr_pdf_path": ocr_out,
                    "pre_ocr_chars": total_chars,
                    "post_ocr_chars": post_chars,
                    "improved": post_chars > total_chars,
                    "improvement": post_chars - total_chars,
                }
                with open(exec_path, "w", encoding="utf-8") as f:
                    json.dump(exec_data, f, indent=2, ensure_ascii=False)
            except Exception:
                pass

            # Prefer OCR output if improved
            if post_chars > total_chars:
                pdf_path = ocr_out
                total_chars = post_chars
            else:
                log(f"OCR did not improve text extraction for {paper_id}")
        except Exception as e:
            log(f"OCR failed for {paper_id}: {e}")

    if not paragraphs:
        log(f"No text extracted from {paper_id}")
        return None

    log(f"Extracted {len(paragraphs)} paragraphs from {paper_id}")

    result = {
        "pdf_path": pdf_path,
        "paragraphs": paragraphs,
        "num_paragraphs": len(paragraphs),
        "total_chars": sum(len(p) for p in paragraphs),
    }

    # Mirror minimal detection/execution outcome under site/stats for monitoring
    try:
        os.makedirs(os.path.join("site", "stats", "validation"), exist_ok=True)
        # Append/update single-paper info into aggregate files already written above
        # (no-op here; aggregate reports are maintained earlier)
        pass
    except Exception:
        pass

    return result


def batch_download_and_extract(
    paper_ids: List[str],
    records_file: str = "data/records/ia_all_20251004_215726.json",
    pdf_dir: str = "data/pdfs",
    output_file: Optional[str] = None,
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
    id_to_rec = {r["id"]: r for r in records}

    results = {}

    for paper_id in paper_ids:
        if paper_id not in id_to_rec:
            log(f"Paper {paper_id} not found in records")
            continue

        rec = id_to_rec[paper_id]
        pdf_url = rec.get("pdf_url")

        if not pdf_url:
            log(f"No PDF URL for {paper_id}")
            continue

        result = process_paper(paper_id, pdf_url, pdf_dir)
        if result:
            results[paper_id] = result

        # Optional pacing for remote servers
        time.sleep(0.2)

    # Save results
    if output_file:
        write_json(output_file, results)
        log(f"Saved extraction results to {output_file}")

    return results


def run_cli():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Download PDFs and extract text")
    parser.add_argument("--paper-ids", nargs="+", help="Specific paper IDs to process")
    parser.add_argument(
        "--records", default="data/records/records.json", help="Path to records JSON"
    )
    parser.add_argument("--pdf-dir", default="data/pdfs", help="Directory for PDFs")
    parser.add_argument("--output", help="Output JSON file for extraction results")
    parser.add_argument("--test", action="store_true", help="Test on first 10 papers")

    args = parser.parse_args()

    if args.test:
        # Get first 10 papers from records
        records = read_json(args.records)
        paper_ids = [r["id"] for r in records[:10]]
        log(f"Testing on {len(paper_ids)} papers")
    elif args.paper_ids:
        paper_ids = args.paper_ids
    else:
        parser.error("Must specify --paper-ids or --test")

    results = batch_download_and_extract(
        paper_ids=paper_ids,
        records_file=args.records,
        pdf_dir=args.pdf_dir,
        output_file=args.output,
    )

    log(f"\nProcessed {len(results)}/{len(paper_ids)} papers successfully")

    # Show summary
    if results:
        total_paras = sum(r["num_paragraphs"] for r in results.values())
        total_chars = sum(r["total_chars"] for r in results.values())
        log(f"Total paragraphs: {total_paras:,}")
        log(f"Total characters: {total_chars:,}")


if __name__ == "__main__":
    run_cli()
