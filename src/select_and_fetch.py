from __future__ import annotations

import argparse
import os
import re
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

from .utils import (
    ensure_dir,
    getenv_bool,
    http_get,
    log,
    read_json,
    read_seen,
    sanitize_filename,
    write_json,
    write_seen,
)


def find_latex_archive_links(html: str, base_url: Optional[str] = None) -> List[str]:
    soup = BeautifulSoup(html, "html.parser")
    links: List[str] = []
    for a in soup.find_all("a"):
        href = a.get("href") or ""
        text = (a.get_text() or "").lower()
        if not href:
            continue
        if any(href.lower().endswith(ext) for ext in (".tar.gz", ".zip")) and (
            "tex" in href.lower() or "source" in href.lower() or "latex" in href.lower() or "tex" in text
        ):
            if href.startswith("http"):
                links.append(href)
            elif base_url and href.startswith("/"):
                # naive join
                from urllib.parse import urljoin

                links.append(urljoin(base_url, href))
    return links


def download_file(url: str, dest_path: str) -> Optional[str]:
    try:
        resp = http_get(url)
    except Exception as e:
        log(f"download failed {url}: {e}")
        return None
    # Validate PDF downloads
    content = resp.content
    if dest_path.lower().endswith('.pdf'):
        headers = getattr(resp, 'headers', {}) or {}
        ctype = headers.get('Content-Type', '').lower()
        if ('pdf' not in ctype) and (not content.startswith(b'%PDF-')):
            log(f"skipping non-PDF content from {url}")
            return None
    ensure_dir(os.path.dirname(dest_path))
    with open(dest_path, "wb") as f:
        f.write(content)
    return dest_path


def fetch_pdf_from_ia(identifier: str, dest_dir: str = "data/pdfs") -> Optional[str]:
    """
    Download PDF from Internet Archive.

    Args:
        identifier: Archive.org identifier (e.g., 'ChinaXiv-202211.00170V1')
        dest_dir: Destination directory for PDF

    Returns:
        Path to downloaded PDF or None
    """
    # Get item metadata to find PDF filename
    metadata_url = f"https://archive.org/metadata/{identifier}"
    try:
        metadata = http_get(metadata_url).json()
    except Exception as e:
        log(f"Failed to get IA metadata for {identifier}: {e}")
        return None

    # Find PDF file (usually ends with .pdf)
    files = metadata.get('files', [])
    pdf_files = [f for f in files if f.get('name', '').endswith('.pdf')]

    if not pdf_files:
        log(f"No PDF found for {identifier}")
        return None

    pdf_file = pdf_files[0]['name']
    pdf_url = f"https://archive.org/download/{identifier}/{pdf_file}"

    # Download to dest_dir/{identifier}.pdf
    output_path = os.path.join(dest_dir, f"{identifier}.pdf")
    return download_file(pdf_url, output_path)


def process_records(records_path: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = read_json(records_path)
    seen = read_seen()
    processed: List[Dict[str, Any]] = []
    count = 0
    for rec in records:
        if limit and count >= limit:
            break
        rid = rec.get("id")
        if not rid or rid in (seen.get("ids") or []):
            continue

        # Download PDF - handle Internet Archive records specially
        pdf_path = None
        if rid.startswith("ia-"):
            # Internet Archive record - use metadata API
            ia_identifier = rid[3:]  # Remove 'ia-' prefix
            pdf_path = fetch_pdf_from_ia(ia_identifier, dest_dir="data/pdfs")
        else:
            # Standard record - use direct PDF URL
            pdf_url = rec.get("pdf_url")
            if pdf_url:
                fname = sanitize_filename(f"{rid}.pdf")
                target = os.path.join("data", "pdfs", fname)
                result = download_file(pdf_url, target)
                pdf_path = result if result else None

        # Try to discover LaTeX source archive from landing page
        latex_path = None
        if rec.get("source_url"):
            try:
                html = http_get(rec["source_url"]).text
                links = find_latex_archive_links(html, base_url=rec["source_url"]) or []
                if links:
                    ext = ".tar.gz" if links[0].lower().endswith(".tar.gz") else ".zip"
                    lname = sanitize_filename(f"{rid}{ext}")
                    latex_path = os.path.join("data", "sources", lname)
                    download_file(links[0], latex_path)
            except Exception as e:
                log(f"source discovery failed: {e}")

        rec["files"] = {
            "pdf_path": pdf_path,
            "latex_source_path": latex_path,
            "has_latex_source": bool(latex_path),
        }
        processed.append(rec)
        count += 1
        # Mark seen immediately to avoid reprocessing
        seen.setdefault("ids", []).append(rid)
    write_seen(seen)
    return processed


def run_cli() -> None:
    parser = argparse.ArgumentParser(description="Select new records and fetch PDFs/sources.")
    parser.add_argument("--records", required=True, help="Path to normalized records JSON")
    parser.add_argument("--limit", type=int, help="Max items to process")
    parser.add_argument("--output", help="Output JSON of selected records")
    args = parser.parse_args()

    out = process_records(args.records, args.limit)
    out_path = args.output or os.path.join("data", "selected.json")
    write_json(out_path, out)
    log(f"Selected {len(out)} new items → {out_path}")


if __name__ == "__main__":
    run_cli()
