#!/usr/bin/env python3
"""
Smoke runner to translate a small batch of papers end-to-end, with QA and optional alerts.

Usage (local):
  python scripts/smoke_translate.py --limit 20 --workers 20 --month 202509 --alert

Usage (CI):
  python scripts/smoke_translate.py --limit ${{ inputs.limit }} --workers ${{ inputs.workers }} --month ${{ inputs.month }} --alert --deploy ${{ inputs.deploy }}
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Ensure repository root on sys.path so "python scripts/smoke_translate.py" works everywhere
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.discord_alerts import DiscordAlerts  # type: ignore
PY = sys.executable


def path_for_month_records(month: str) -> Optional[str]:
    """Return the path to a month records file if it exists."""
    candidate = REPO_ROOT / "data" / "records" / f"chinaxiv_{month}.json"
    return str(candidate) if candidate.exists() else None


def run(cmd: str) -> int:
    print(f"$ {cmd}")
    return os.system(cmd)


def load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def count_existing(ids: List[str], directory: Path) -> int:
    count = 0
    for pid in ids:
        if (directory / f"{pid}.json").exists():
            count += 1
    return count


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke translate N unseen papers with QA")
    parser.add_argument("--limit", type=int, default=20, help="How many papers to process")
    parser.add_argument("--workers", type=int, default=20, help="Parallel translation workers")
    parser.add_argument("--month", type=str, help="Limit to month (YYYYMM)")
    parser.add_argument("--records", type=str, help="Explicit records JSON path")
    parser.add_argument("--alert", action="store_true", help="Send Discord alerts")
    parser.add_argument(
        "--qa-threshold",
        type=float,
        default=5.0,
        help="Max allowed QA failure rate in percent before failing (default: 5.0)",
    )
    parser.add_argument("--deploy", action="store_true", help="Deploy site after success")
    args = parser.parse_args()

    alerts = DiscordAlerts() if args.alert else None

    # Resolve records source
    records_path: Optional[str] = None
    if args.records:
        records_path = args.records
    elif args.month:
        records_path = path_for_month_records(args.month)
        if not records_path:
            print(f"No records found for month {args.month}")
            return 1
    else:
        # Fallback to the latest records file by mtime
        records_dir = REPO_ROOT / "data" / "records"
        json_files = sorted(records_dir.glob("*.json"), key=lambda p: p.stat().st_mtime)
        if not json_files:
            print("No records available in data/records")
            return 1
        records_path = str(json_files[-1])

    selected_path = REPO_ROOT / "data" / "selected.json"

    # Selection (also fetches PDFs and updates seen.json to ensure dedupe)
    sel_rc = run(
        f"{PY} -m src.select_and_fetch --records {records_path} --limit {args.limit} --output {selected_path}"
    )
    if sel_rc != 0 or not selected_path.exists():
        msg = f"Selection failed (rc={sel_rc}) or {selected_path} missing"
        print(msg)
        if alerts:
            alerts.send_alert("error", "Smoke selection failed", description=msg)
        return 1

    # Read selected list and extract IDs
    try:
        selected: List[Dict[str, Any]] = load_json(selected_path)
    except Exception as e:
        print(f"Failed to read {selected_path}: {e}")
        return 1

    paper_ids: List[str] = [it.get("id") for it in selected if isinstance(it, dict) and it.get("id")]
    print(f"Selected {len(paper_ids)} papers: {paper_ids[:min(5, len(paper_ids))]}{' …' if len(paper_ids) > 5 else ''}")

    # Translate with QA enabled
    pipe_rc = run(
        f"{PY} -m src.pipeline --skip-selection --workers {args.workers} --with-qa"
    )
    if pipe_rc != 0:
        msg = f"Pipeline failed (rc={pipe_rc})"
        print(msg)
        if alerts:
            alerts.send_alert("critical", "Smoke pipeline failed", description=msg)
        return 1

    # Count results
    translated_dir = REPO_ROOT / "data" / "translated"
    flagged_dir = REPO_ROOT / "data" / "flagged"
    translated_count = count_existing(paper_ids, translated_dir)
    flagged_count = count_existing(paper_ids, flagged_dir)

    # Basic QA pass rate
    total = max(1, len(paper_ids))
    pass_rate = (translated_count / total) * 100.0
    fail_rate = 100.0 - pass_rate
    print(
        f"Smoke summary: selected={len(paper_ids)} translated={translated_count} flagged={flagged_count} pass_rate={pass_rate:.1f}% fail_rate={fail_rate:.1f}%"
    )
    if fail_rate > args.qa_threshold:
        print(f"QA failure rate {fail_rate:.1f}% exceeds threshold {args.qa_threshold:.1f}%")
        if alerts:
            alerts.send_alert(
                alert_type="warning",
                title="Smoke QA threshold exceeded",
                description=f"fail_rate={fail_rate:.1f}% > threshold={args.qa_threshold:.1f}%",
                fields=[
                    {"name": "Selected", "value": str(len(paper_ids)), "inline": True},
                    {"name": "Translated", "value": str(translated_count), "inline": True},
                    {"name": "Flagged", "value": str(flagged_count), "inline": True},
                ],
            )
        return 2

    # Optional deploy
    if args.deploy:
        print("Deploying site…")
        deploy_rc = run(f"{PY} -m src.render && {PY} -m src.search_index && {PY} -m src.make_pdf")
        if deploy_rc != 0:
            print("Site build failed; skipping deploy")
        else:
            print("Site build complete")

    # Alerts
    if alerts:
        fields = [
            {"name": "Selected", "value": str(len(paper_ids)), "inline": True},
            {"name": "Translated", "value": str(translated_count), "inline": True},
            {"name": "Flagged", "value": str(flagged_count), "inline": True},
            {"name": "Pass rate", "value": f"{pass_rate:.1f}%", "inline": True},
        ]
        alerts.send_alert(
            alert_type="info",
            title="Smoke translation completed",
            description=f"Records: {Path(records_path).name if records_path else 'unknown'}",
            fields=fields,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


