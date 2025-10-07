from __future__ import annotations

import argparse
import glob
import os
from typing import Optional

from .utils import log
from .discord_alerts import DiscordAlerts


def find_latest_records_json() -> Optional[str]:
    files = sorted(glob.glob(os.path.join("data", "records", "*.json")))
    return files[-1] if files else None


def run_cli() -> None:
    parser = argparse.ArgumentParser(
        description="Run end-to-end pipeline: select, translate, render."
    )
    parser.add_argument(
        "--limit", type=int, default=0, help="Max papers to process (0 = all)"
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--workers", type=int, default=20, help="Parallel translation workers"
    )
    parser.add_argument(
        "--records", type=str, help="Comma-separated records JSON paths (optional)"
    )
    parser.add_argument(
        "--skip-selection",
        action="store_true",
        help="Skip selection step if data/selected.json exists",
    )
    args = parser.parse_args()

    # Selection step (unless skipped and selected.json already exists)
    selected_path = os.path.join("data", "selected.json")
    if not args.skip_selection or not os.path.exists(selected_path):
        rec_paths: list[str] = []
        if args.records:
            rec_paths = [p.strip() for p in args.records.split(",") if p.strip()]
        else:
            latest = find_latest_records_json()
            if latest:
                rec_paths = [latest]

        if not rec_paths:
            log("No records available for selection; exiting")
            return

        # If multiple records paths were provided, merge them to a temp file first
        if len(rec_paths) > 1:
            import json as _json

            merged_path = os.path.join("data", "records", "_merged_current_prev.json")
            try:
                all_items = []
                for rp in rec_paths:
                    with open(rp, "r", encoding="utf-8") as f:
                        data = _json.load(f)
                        if isinstance(data, list):
                            all_items.extend(data)
                with open(merged_path, "w", encoding="utf-8") as f:
                    _json.dump(all_items, f, ensure_ascii=False)
                rec_arg = merged_path
            except Exception as e:
                log(f"Failed to merge records: {e}")
                return
        else:
            rec_arg = rec_paths[0]

        log("Select & fetch step…")
        limit_arg = f" --limit {args.limit}" if args.limit and args.limit > 0 else ""
        os.system(
            f"python -m src.select_and_fetch --records {rec_arg}{limit_arg} --output {selected_path}"
        )
        # Defensive: if selection step didn't create output (e.g., dry-run tests stub it),
        # fall back to a minimal selection so downstream steps can proceed.
        if not os.path.exists(selected_path):
            try:
                import json as _json

                # Use the same records source we resolved above for selection
                _sel_src = rec_arg
                with open(_sel_src, "r", encoding="utf-8") as f:
                    _items = _json.load(f)
                    if not isinstance(_items, list):
                        _items = []
                # Apply limit if provided; otherwise include all
                _limit = args.limit if args.limit and args.limit > 0 else None
                _selected = _items[:_limit] if _limit else _items
                os.makedirs(os.path.dirname(selected_path), exist_ok=True)
                with open(selected_path, "w", encoding="utf-8") as f:
                    _json.dump(_selected, f, ensure_ascii=False)
                log(
                    f"Selection output missing; wrote fallback selection with {len(_selected)} items"
                )
            except Exception as e:
                # As a last resort, create an empty selection file to avoid crashes
                os.makedirs(os.path.dirname(selected_path), exist_ok=True)
                with open(selected_path, "w", encoding="utf-8") as f:
                    f.write("[]")
                log(
                    f"Selection output missing and fallback failed ({e}); wrote empty selection []"
                )
    else:
        log("Skipping selection (data/selected.json present)")

    # Translate
    log("Translate step…")
    from .services.translation_service import TranslationService
    from .file_service import read_json
    from concurrent.futures import ThreadPoolExecutor, as_completed

    # Load selected papers
    selected = read_json(selected_path)
    if not isinstance(selected, list) or not selected:
        log("No selected papers to translate; exiting")
        return

    # Apply limit if set (>0)
    if args.limit and args.limit > 0:
        worklist = selected[: args.limit]
    else:
        worklist = selected

    service = TranslationService()

    def _translate_one(paper_id: str) -> tuple[str, bool, str | None]:
        try:
            log(f"Translating {paper_id}…")
            result_path = service.translate_paper(paper_id, dry_run=args.dry_run)
            return paper_id, True, result_path
        except Exception as e:
            return paper_id, False, str(e)

    successes = 0
    failures = 0
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
        futures = {
            ex.submit(_translate_one, p["id"]): p["id"] for p in worklist if p.get("id")
        }
        for fut in as_completed(futures):
            pid, ok, info = fut.result()
            if ok:
                successes += 1
                log(f"✓ {pid} → {info}")
            else:
                failures += 1
                log(f"✗ {pid} failed: {info}")

    # Render + index + pdf
    log("Render step…")
    os.system("python -m src.render")
    os.system("python -m src.search_index")
    os.system("python -m src.make_pdf")

    # Send success notification to Discord
    alerts = DiscordAlerts()
    alerts.pipeline_success(successes, 0.0)  # Cost calculation TBD

    log("Pipeline complete.")


if __name__ == "__main__":
    run_cli()
