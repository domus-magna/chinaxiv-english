from __future__ import annotations

import argparse
import glob
import os
from typing import Optional

from .harvest_oai import run_cli as harvest_cli
from .select_and_fetch import run_cli as select_cli
from .translate import run_cli as translate_cli
from .render import run_cli as render_cli
from .search_index import run_cli as search_cli
from .make_pdf import run_cli as pdf_cli
from .utils import log


def find_latest_records_json() -> Optional[str]:
    files = sorted(glob.glob(os.path.join("data", "records", "*.json")))
    return files[-1] if files else None


def run_cli() -> None:
    parser = argparse.ArgumentParser(description="Run end-to-end pipeline on a small window.")
    parser.add_argument("--from", dest="from_day")
    parser.add_argument("--until", dest="until_day")
    parser.add_argument("--limit", type=int, default=2)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    # Harvest
    import sys

    h_args = ["-m", "src.harvest_oai"]
    if args.from_day and args.until_day:
        h_args += ["--from", args.from_day, "--until", args.until_day]
    # Invoke as a module
    from runpy import run_module

    log("Harvest step…")
    run_module("src.harvest_oai", run_name="__main__")
    rec_path = find_latest_records_json()
    if not rec_path:
        log("No records harvested; exiting")
        return

    # Select & fetch
    log("Select & fetch step…")
    os.system(f"python -m src.select_and_fetch --records {rec_path} --limit {args.limit} --output data/selected.json")

    # Translate
    log("Translate step…")
    tr_cmd = "python -m src.translate --selected data/selected.json"
    if args.dry_run:
        tr_cmd += " --dry-run"
    os.system(tr_cmd)

    # Render + index + pdf
    log("Render step…")
    os.system("python -m src.render")
    os.system("python -m src.search_index")
    os.system("python -m src.make_pdf")
    log("Pipeline complete.")


if __name__ == "__main__":
    run_cli()

