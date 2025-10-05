from __future__ import annotations

import argparse
import glob
import os
from typing import Optional

from .harvest_ia import run_cli as harvest_cli
from .select_and_fetch import run_cli as select_cli
from .render import run_cli as render_cli
from .search_index import run_cli as search_cli
from .make_pdf import run_cli as pdf_cli
from .utils import log
from .discord_alerts import DiscordAlerts


def find_latest_records_json() -> Optional[str]:
    files = sorted(glob.glob(os.path.join("data", "records", "*.json")))
    return files[-1] if files else None


def run_cli() -> None:
    parser = argparse.ArgumentParser(description="Run end-to-end pipeline on a small window.")
    parser.add_argument("--limit", type=int, default=10, help="Number of papers to process")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    # Harvest
    import sys
    log("Harvest step…")
    # Temporarily modify sys.argv for harvest_ia
    original_argv = sys.argv[:]
    sys.argv = ['harvest_ia', '--limit', str(args.limit)]
    try:
        harvest_cli()
    finally:
        sys.argv = original_argv
    rec_path = find_latest_records_json()
    if not rec_path:
        log("No records harvested; exiting")
        return

    # Select & fetch
    log("Select & fetch step…")
    os.system(f"python -m src.select_and_fetch --records {rec_path} --limit {args.limit} --output data/selected.json")

    # Translate
    log("Translate step…")
    # Use the new translation service directly instead of CLI
    from .services.translation_service import TranslationService
    from .file_service import read_json, write_json
    import glob
    
    # Load selected papers
    selected = read_json("data/selected.json")
    service = TranslationService()
    
    for paper in selected[:args.limit]:
        try:
            log(f"Translating {paper['id']}...")
            result_path = service.translate_paper(paper['id'], dry_run=args.dry_run)
            log(f"Completed {paper['id']} → {result_path}")
        except Exception as e:
            log(f"Failed to translate {paper['id']}: {e}")
            continue

    # Render + index + pdf
    log("Render step…")
    os.system("python -m src.render")
    os.system("python -m src.search_index")
    os.system("python -m src.make_pdf")
    
    # Send success notification to Discord
    alerts = DiscordAlerts()
    alerts.pipeline_success(args.limit, 0.0)  # Cost would need to be calculated
    
    log("Pipeline complete.")


if __name__ == "__main__":
    run_cli()

