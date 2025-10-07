from __future__ import annotations

import argparse
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .utils import (
    http_get,
    log,
    write_json,
    ensure_dir,
)


def ensure_list(val: Any) -> List[str]:
    """Ensure value is a list of strings."""
    if val is None:
        return []
    if isinstance(val, list):
        return [str(v) for v in val]
    return [str(val)]


def construct_pdf_url(identifier: str) -> str:
    """
    Construct Internet Archive PDF download URL.

    Args:
        identifier: Archive.org identifier (e.g., 'ChinaXiv-202211.00170V1')

    Returns:
        PDF download URL
    """
    # PDF filename convention in IA: {identifier}.pdf
    return f"https://archive.org/download/{identifier}/{identifier}.pdf"


def infer_license(item: Dict) -> Dict[str, Any]:
    """
    DISABLED: We do not care about licenses. All papers translated in full.

    Infer license from Internet Archive metadata.

    For V1, default to unknown (derivatives_allowed: None).
    Future: check item metadata for license info.
    """
    # DISABLED: We do not care about licenses
    return {"raw": "", "derivatives_allowed": True}  # Always allow derivatives


def normalize_ia_record(item: Dict) -> Dict[str, Any]:
    """
    Normalize Internet Archive item to standard format.

    Maps:
        identifier -> id (with 'ia-' prefix)
        chinaxiv -> oai_identifier (original ChinaXiv ID)
        title -> title
        creator -> creators (ensure list)
        description -> abstract
        subject -> subjects (ensure list)
        date -> date
    """
    identifier = item.get("identifier", "")

    return {
        "id": f"ia-{identifier}",
        "oai_identifier": item.get("chinaxiv", ""),
        "title": item.get("title", ""),
        "creators": ensure_list(item.get("creator")),
        "abstract": item.get("description", ""),
        "subjects": ensure_list(item.get("subject")),
        "date": item.get("date", ""),
        "source_url": f"https://archive.org/details/{identifier}",
        "pdf_url": construct_pdf_url(identifier),
        "license": infer_license(item),
        "setSpec": None,  # IA doesn't use sets
    }


def harvest_chinaxiv_metadata(
    cursor: Optional[str] = None, limit: int = 10000, min_year: Optional[int] = None
) -> Tuple[List[Dict], Optional[str]]:
    """
    Harvest ChinaXiv metadata from Internet Archive.

    Args:
        cursor: Resume from this cursor (for pagination)
        limit: Max items per request (default: 10000, min: 100 per IA API requirement)
        min_year: Filter for papers >= this year (e.g., 2017)

    Returns:
        (records, next_cursor): List of normalized records and cursor for next page
    """
    # IA API requires count >= 100
    api_limit = max(100, limit)

    url = "https://archive.org/services/search/v1/scrape"
    params = {
        "fields": "identifier,chinaxiv,title,creator,subject,date,description",
        "q": "collection:chinaxivmirror",
        "count": api_limit,
    }
    if cursor:
        params["cursor"] = cursor

    log(
        f"Fetching from IA (limit={api_limit}, cursor={cursor[:20] if cursor else 'none'})"
    )
    resp = http_get(url, params=params)
    try:
        data = resp.json()
    except Exception as e:
        raise RuntimeError(f"Invalid JSON from IA scrape endpoint: {e}")

    items = data.get("items", [])
    log(f"Received {len(items)} items from IA")

    # Normalize all items
    records = []
    for item in items:
        normalized = normalize_ia_record(item)

        # Apply year filter if specified
        if min_year is not None:
            date_str = normalized.get("date", "")
            if date_str and len(date_str) >= 4:
                year = date_str[:4]
                if year.isdigit() and int(year) < min_year:
                    continue  # Skip papers before min_year

        records.append(normalized)

    if min_year:
        log(f"Filtered to {len(records)} records (>= {min_year})")

    # Truncate to requested limit if user asked for less than IA minimum
    if limit < len(records):
        records = records[:limit]
        log(f"Truncated to {limit} records")

    next_cursor = data.get("cursor")

    return records, next_cursor


def harvest_all_records(min_year: Optional[int] = None) -> List[Dict]:
    """
    Harvest all records from Internet Archive, paginating until exhausted.

    Args:
        min_year: Filter for papers >= this year (e.g., 2017)

    Returns:
        List of all normalized records
    """
    all_records = []
    cursor = None
    batch = 0

    while True:
        batch += 1
        records, next_cursor = harvest_chinaxiv_metadata(
            cursor=cursor, limit=10000, min_year=min_year
        )

        all_records.extend(records)
        log(f"Batch {batch}: {len(records)} records (total: {len(all_records):,})")

        if not next_cursor:
            break

        cursor = next_cursor

    return all_records


def run_cli() -> None:
    parser = argparse.ArgumentParser(
        description="Harvest ChinaXiv metadata from Internet Archive."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10000,
        help="Max records per batch (default: 10000)",
    )
    parser.add_argument("--cursor", help="Resume from cursor (for pagination)")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Harvest all records (paginate until exhausted)",
    )
    parser.add_argument(
        "--min-year", type=int, help="Filter for papers >= this year (e.g., 2017)"
    )
    args = parser.parse_args()

    if args.all:
        # Harvest all records
        records = harvest_all_records(min_year=args.min_year)

        # Save to data/records/
        ensure_dir(os.path.join("data", "records"))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = os.path.join("data", "records", f"ia_all_{timestamp}.json")
        write_json(out_path, records)
        log(f"Wrote {len(records):,} records → {out_path}")
    else:
        # Single batch
        records, next_cursor = harvest_chinaxiv_metadata(
            cursor=args.cursor, limit=args.limit, min_year=args.min_year
        )

        # Save to data/records/
        ensure_dir(os.path.join("data", "records"))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = os.path.join("data", "records", f"ia_batch_{timestamp}.json")
        write_json(out_path, records)
        log(f"Wrote {len(records)} records → {out_path}")

        if next_cursor:
            log(f"More records available. Resume with: --cursor {next_cursor}")


if __name__ == "__main__":
    run_cli()
