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
    parser.add_argument(
        "--with-qa",
        action="store_true",
        help="Enable QA filtering (saves passed to data/translated/, flagged to data/flagged/)",
    )
    parser.add_argument(
        "--cloud-mode",
        action="store_true",
        help="Use cloud job queue (for GitHub Actions workflows)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Batch size for cloud mode (default: 100)",
    )
    parser.add_argument(
        "--worker-id",
        type=str,
        default="local-worker",
        help="Worker ID for cloud mode (default: local-worker)",
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

    # Determine worklist based on mode
    if args.cloud_mode:
        # Cloud mode: claim batch from cloud job queue
        from .cloud_job_queue import cloud_queue

        log(f"Cloud mode: claiming batch of {args.batch_size} jobs...")
        jobs = cloud_queue.claim_batch(args.worker_id, batch_size=args.batch_size)

        if not jobs:
            log("No pending jobs in queue")
            return

        log(f"Claimed {len(jobs)} jobs")
        worklist = [{"id": job["paper_id"]} for job in jobs]
    else:
        # Standard mode: use selection
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

    # Import QA if enabled
    if args.with_qa:
        from .qa_filter import filter_translation_file

    def _translate_one(paper_id: str) -> tuple[str, bool, str | None, bool | None]:
        try:
            log(f"Translating {paper_id}…")
            result_path = service.translate_paper(paper_id, dry_run=args.dry_run)

            # QA filtering if enabled
            qa_passed = None
            if args.with_qa and not args.dry_run:
                # Load translation
                import json

                with open(result_path, "r", encoding="utf-8") as f:
                    translation = json.load(f)

                # Filter and save to appropriate directory
                qa_passed, qa_result = filter_translation_file(
                    translation, save_passed=True, save_flagged=True
                )

                if qa_passed:
                    log(f"  QA: PASS (score: {qa_result.score:.2f})")
                else:
                    log(
                        f"  QA: FLAGGED ({qa_result.status.value}, score: {qa_result.score:.2f})"
                    )

            return paper_id, True, result_path, qa_passed
        except Exception as e:
            return paper_id, False, str(e), None

    successes = 0
    failures = 0
    qa_passed_count = 0
    qa_flagged_count = 0

    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
        futures = {
            ex.submit(_translate_one, p["id"]): p["id"] for p in worklist if p.get("id")
        }
        for fut in as_completed(futures):
            pid, ok, info, qa_passed = fut.result()
            if ok:
                successes += 1
                log(f"✓ {pid} → {info}")

                # Update cloud queue if in cloud mode
                if args.cloud_mode:
                    from .cloud_job_queue import cloud_queue

                    if qa_passed is False:
                        cloud_queue.complete_job(pid, qa_passed=False)
                        qa_flagged_count += 1
                    else:
                        cloud_queue.complete_job(pid, qa_passed=True)
                        if qa_passed is True:
                            qa_passed_count += 1
            else:
                failures += 1
                log(f"✗ {pid} failed: {info}")

                # Mark as failed in cloud queue
                if args.cloud_mode:
                    from .cloud_job_queue import cloud_queue

                    cloud_queue.fail_job(pid, str(info))

    # Print QA summary if enabled
    if args.with_qa:
        total_qa = qa_passed_count + qa_flagged_count
        pass_rate = (qa_passed_count / total_qa * 100) if total_qa > 0 else 0.0
        log(f"\nQA Summary:")
        log(f"  Passed: {qa_passed_count}")
        log(f"  Flagged: {qa_flagged_count}")
        log(f"  Pass rate: {pass_rate:.1f}%")

    # Render + index + pdf (skip if cloud mode - will be done after all batches)
    if not args.cloud_mode:
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
