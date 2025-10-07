"""
Background worker process for batch translation.
"""

import argparse
import os
import signal
import sys
import time
from pathlib import Path

from . import job_queue
from .utils import log
from .config import load_dotenv


class BackgroundWorker:
    """Independent worker process for translation jobs."""

    def __init__(self, worker_id: int):
        self.worker_id = f"worker-{worker_id}"
        self.pid = os.getpid()
        self.should_stop = False
        self.jobs_processed = 0
        self.idle_cycles = 0
        self.max_idle_cycles = 24  # 2 minutes (5s * 24)

    def write_pid_file(self) -> None:
        """Write PID file for process tracking."""
        pid_dir = Path("data/workers")
        pid_dir.mkdir(parents=True, exist_ok=True)

        pid_file = pid_dir / f"{self.worker_id}.pid"
        with open(pid_file, "w") as f:
            f.write(str(self.pid))

        log(f"[{self.worker_id}] Started (PID: {self.pid})")

    def remove_pid_file(self) -> None:
        """Remove PID file on shutdown."""
        pid_file = Path("data/workers") / f"{self.worker_id}.pid"
        if pid_file.exists():
            pid_file.unlink()

    def handle_shutdown(self, signum, frame):
        """Handle shutdown signals gracefully."""
        log(f"[{self.worker_id}] Received shutdown signal")
        self.should_stop = True

    def run_translation(self, paper_id: str) -> None:
        """
        Run translation for a paper.

        Args:
            paper_id: Paper identifier
        """
        # Import here to avoid circular imports
        from .translate import translate_paper

        translate_paper(paper_id)

    def run_qa_evaluation(self, paper_id: str) -> None:
        """
        Run QA evaluation for a paper.

        Args:
            paper_id: Paper identifier
        """
        # Import here
        import subprocess

        try:
            # Run evaluation script with DB storage
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/evaluate_translation.py",
                    f"data/translated/{paper_id}.json",
                    "--store-db",
                ],
                capture_output=True,
                text=True,
                timeout=120,  # 2 min timeout
            )

            if result.returncode != 0:
                log(f"[{self.worker_id}] QA failed for {paper_id}: {result.stderr}")

        except Exception as e:
            log(f"[{self.worker_id}] QA error for {paper_id}: {e}")

    def run(self) -> None:
        """Main worker loop."""
        # Load environment variables from .env (override existing)
        load_dotenv(override=True)

        # Setup
        self.write_pid_file()

        # Signal handlers
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        signal.signal(signal.SIGINT, self.handle_shutdown)

        log(f"[{self.worker_id}] Ready")

        # Main loop
        while not self.should_stop:
            # Update heartbeat
            job_queue.update_heartbeat(self.worker_id)

            # Claim a job
            job = job_queue.claim_job(self.worker_id)

            if not job:
                self.idle_cycles += 1

                # Auto-exit if idle too long
                if self.idle_cycles >= self.max_idle_cycles:
                    log(f"[{self.worker_id}] No jobs for 2 minutes, exiting")
                    break

                time.sleep(5)
                continue

            # Reset idle counter
            self.idle_cycles = 0

            # Process job
            job_id = job["id"]
            paper_id = job["paper_id"]
            attempts = job["attempts"]

            log(f"[{self.worker_id}] Processing {paper_id} (attempt {attempts + 1})")

            try:
                # Translate
                self.run_translation(paper_id)

                # QA sampling (every 10th job)
                if job_id % 10 == 0:
                    log(f"[{self.worker_id}] Running QA for {paper_id}")
                    self.run_qa_evaluation(paper_id)

                # Mark complete
                job_queue.complete_job(job_id)
                job_queue.increment_worker_jobs(self.worker_id)
                self.jobs_processed += 1

                log(
                    f"[{self.worker_id}] Completed {paper_id} ({self.jobs_processed} total)"
                )

            except Exception as e:
                error_msg = str(e)
                log(f"[{self.worker_id}] Failed {paper_id}: {error_msg}")
                job_queue.fail_job(job_id, error_msg)

                # Sleep on error to avoid rapid retries
                time.sleep(2)

        # Cleanup
        log(f"[{self.worker_id}] Shutting down ({self.jobs_processed} jobs completed)")
        self.remove_pid_file()


def run_cli() -> None:
    """CLI entry point for worker."""
    parser = argparse.ArgumentParser(description="Background translation worker")
    parser.add_argument("worker_id", type=int, help="Worker ID (0-based)")
    args = parser.parse_args()

    worker = BackgroundWorker(args.worker_id)
    worker.run()


if __name__ == "__main__":
    run_cli()
