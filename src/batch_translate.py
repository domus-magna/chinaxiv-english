"""
CLI controller for batch translation system.
"""

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List

from .job_queue import job_queue
from .streaming import process_papers_streaming
from .utils import log
from .monitoring import alert_info, alert_warning, alert_error, alert_critical


def harvest_papers(years: List[str]) -> List[str]:
    """
    Harvest papers from Internet Archive for specified years.

    Args:
        years: List of years (e.g., ['2024', '2025'])

    Returns:
        List of paper IDs
    """
    import requests

    paper_ids = []

    for year in years:
        log(f"Harvesting {year} papers from Internet Archive...")

        url = "https://archive.org/advancedsearch.php"
        params = {
            'q': f'collection:chinaxivmirror AND identifier:*{year}*',
            'fl': 'identifier',
            'rows': 10000,  # Max per request
            'output': 'json',
            'sort': 'identifier desc'
        }

        resp = requests.get(url, params=params, timeout=30)
        data = resp.json()

        items = data.get('response', {}).get('docs', [])
        year_ids = [f"ia-{item['identifier']}" for item in items]

        log(f"Found {len(year_ids)} papers from {year}")
        paper_ids.extend(year_ids)

    return paper_ids


def init_queue(years: List[str], limit: int = None, use_harvested: bool = False) -> None:
    """Initialize job queue with papers."""
    # Job queue is file-based, no schema initialization needed

    # Load papers from harvested records or harvest fresh
    if use_harvested:
        import glob
        records_dir = "data/records"
        ia_files = glob.glob(os.path.join(records_dir, "ia_*.json"))

        if not ia_files:
            log("No harvested records found, falling back to fresh harvest")
            paper_ids = harvest_papers(years)
        else:
            # Sort by modification time, newest first
            ia_files = sorted(ia_files, key=os.path.getmtime, reverse=True)
            log(f"Loading from harvested records: {os.path.basename(ia_files[0])}")
            from .utils import read_json
            ia_records = read_json(ia_files[0])
            paper_ids = [r['id'] for r in ia_records]
            log(f"Loaded {len(paper_ids)} papers from harvested records")
    else:
        paper_ids = harvest_papers(years)

    if limit:
        paper_ids = paper_ids[:limit]

    # Add to queue
    added = job_queue.add_jobs(paper_ids)

    log(f"Initialized {added} jobs in queue")


def start_workers(num_workers: int) -> None:
    """Process jobs using streaming to reduce memory usage."""
    log(f"Processing jobs using streaming (workers={num_workers} for compatibility)...")
    
    # Get pending jobs
    stats = job_queue.get_stats()
    if stats['pending'] == 0:
        log("No pending jobs to process")
        return
    
    log(f"Processing {stats['pending']} pending jobs...")
    
    # Get all pending paper IDs
    pending_ids = []
    for job_file in Path("data/jobs").glob("*.json"):
        with open(job_file, "r") as f:
            job = json.load(f)
        if job["status"] == "pending":
            pending_ids.append(job["id"])
    
    # Process papers one at a time
    completed = 0
    failed = 0
    
    try:
        for result in process_papers_streaming(pending_ids):
            if result["status"] == "completed":
                completed += 1
                job_queue.complete_job(result["id"])
            else:
                failed += 1
                job_queue.fail_job(result["id"], result.get("error", "Unknown error"))
            
            if (completed + failed) % 10 == 0:
                log(f"Progress: {completed + failed}/{len(pending_ids)} processed")
                
    except KeyboardInterrupt:
        log("Interrupted by user")
    
    # Final stats
    log(f"Processing complete: {completed}/{len(pending_ids)} completed, {failed} failed")
    
    if failed > 0:
        alert_warning(f"Processing completed with {failed} failures")
    else:
        alert_info("Processing completed successfully")


def stop_workers() -> None:
    """Stop all running workers."""
    pid_dir = Path("data/workers")

    if not pid_dir.exists():
        log("No workers running")
        return

    pid_files = list(pid_dir.glob("*.pid"))

    if not pid_files:
        log("No workers running")
        return

    log(f"Stopping {len(pid_files)} workers...")

    for pid_file in pid_files:
        try:
            with open(pid_file) as f:
                pid = int(f.read().strip())

            os.kill(pid, signal.SIGTERM)
            log(f"Sent SIGTERM to {pid_file.stem} (PID: {pid})")

        except (OSError, ValueError) as e:
            log(f"Failed to stop {pid_file.stem}: {e}")

    # Wait for graceful shutdown
    time.sleep(2)
    
    # Send alert about worker shutdown
    if pid_files:
        alert_warning(
            "Workers Stopped",
            f"Stopped {len(pid_files)} translation workers",
            source="batch_translate",
            metadata={"stopped_count": len(pid_files)}
        )

    # Check if any still running
    for pid_file in list(pid_dir.glob("*.pid")):
        try:
            with open(pid_file) as f:
                pid = int(f.read().strip())

            # Force kill if still alive
            os.kill(pid, signal.SIGKILL)
            log(f"Force killed {pid_file.stem} (PID: {pid})")

        except (OSError, ValueError):
            pass

        # Remove stale PID file
        pid_file.unlink()

    log("All workers stopped")


def show_status() -> None:
    """Show queue status."""
    stats = job_queue.get_stats()

    print()
    print("=" * 60)
    print("BATCH TRANSLATION STATUS")
    print("=" * 60)
    print(f"Total Jobs:     {stats['total']:,}")
    print(f"Completed:      {stats['completed']:,} ({stats['completed']/stats['total']*100:.1f}%)" if stats['total'] > 0 else "Completed:      0 (0%)")
    print(f"In Progress:    {stats['in_progress']:,}")
    print(f"Pending:        {stats['pending']:,}")
    print(f"Failed:         {stats['failed']:,}")
    print()

    # Active workers
    pid_dir = Path("data/workers")
    if pid_dir.exists():
        worker_pids = list(pid_dir.glob("*.pid"))
        print(f"Active Workers: {len(worker_pids)}")
    else:
        print("Active Workers: 0")

    # Estimated time
    if stats['completed'] > 0 and stats['pending'] > 0:
        # Rough estimate: 25 seconds per paper
        est_seconds = stats['pending'] * 25
        est_minutes = est_seconds / 60
        print(f"Est. Time:      {est_minutes:.0f} minutes")

    print("=" * 60)
    print()


def watch_status() -> None:
    """Watch status with live updates."""
    print("Watching status (Ctrl+C to stop)...\n")

    try:
        while True:
            # Clear screen
            os.system('clear' if os.name != 'nt' else 'cls')

            # Show stats
            show_status()

            # Recent completions
            recent = job_queue.get_recent_completions(limit=5)
            if recent:
                print("Recent Completions:")
                for r in recent:
                    ts = r['completed_at'][:19] if r['completed_at'] else 'N/A'
                    print(f"  [{ts}] {r['paper_id']} ({r['worker_id']})")
                print()

            time.sleep(5)

    except KeyboardInterrupt:
        print("\nStopped watching")


def resume() -> None:
    """Resume from crash - reset stuck jobs."""
    log("Resetting stuck jobs...")

    reset_count = job_queue.reset_stuck_jobs(timeout_minutes=10)

    log(f"Reset {reset_count} stuck jobs to pending")

    # Restart workers
    stats = job_queue.get_stats()
    if stats['pending'] > 0:
        num_workers = min(10, stats['pending'])
        start_workers(num_workers)


def show_failed() -> None:
    """Show failed jobs."""
    failed = job_queue.get_failed_jobs()

    if not failed:
        print("No failed jobs")
        return

    print()
    print("=" * 60)
    print(f"FAILED JOBS ({len(failed)})")
    print("=" * 60)

    for job in failed:
        print(f"\nPaper: {job['paper_id']}")
        print(f"Attempts: {job['attempts']}")
        print(f"Error: {job['error'][:100]}...")


def retry_failed(num_workers: int) -> None:
    """Retry failed jobs - reset to pending and start workers."""
    log("Resetting failed jobs to pending...")

    reset_count = job_queue.reset_failed_jobs()

    log(f"Reset {reset_count} failed jobs to pending")

    # Start workers if there are jobs to retry
    if reset_count > 0:
        log(f"Starting {num_workers} workers to retry failed jobs...")
        start_workers(num_workers)
    else:
        log("No failed jobs to retry")


def run_cli() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Batch translation system")
    subparsers = parser.add_subparsers(dest='command', required=True)

    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize job queue')
    init_parser.add_argument('--years', default='2024,2025', help='Years to harvest (comma-separated)')
    init_parser.add_argument('--limit', type=int, help='Limit number of jobs (for testing)')
    init_parser.add_argument('--use-harvested', action='store_true', help='Use existing harvested IA records instead of re-harvesting')

    # Start command
    start_parser = subparsers.add_parser('start', help='Start worker processes')
    start_parser.add_argument('--workers', type=int, default=10, help='Number of workers')

    # Stop command
    subparsers.add_parser('stop', help='Stop all workers')

    # Status command
    subparsers.add_parser('status', help='Show queue status')

    # Watch command
    subparsers.add_parser('watch', help='Watch status (live updates)')

    # Resume command
    subparsers.add_parser('resume', help='Resume from crash')

    # Failed command
    subparsers.add_parser('failed', help='Show failed jobs')

    # Retry command
    retry_parser = subparsers.add_parser('retry', help='Retry failed jobs')
    retry_parser.add_argument('--workers', type=int, default=10, help='Number of workers')

    args = parser.parse_args()

    # Execute command
    if args.command == 'init':
        years = args.years.split(',')
        init_queue(years, limit=args.limit, use_harvested=args.use_harvested)

    elif args.command == 'start':
        start_workers(args.workers)

    elif args.command == 'stop':
        stop_workers()

    elif args.command == 'status':
        show_status()

    elif args.command == 'watch':
        watch_status()

    elif args.command == 'resume':
        resume()

    elif args.command == 'failed':
        show_failed()

    elif args.command == 'retry':
        retry_failed(args.workers)


if __name__ == "__main__":
    run_cli()
