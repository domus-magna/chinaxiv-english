"""
SQLite-based job queue for batch translation.
"""

import sqlite3
import time
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple


DB_PATH = "data/jobs.db"


@contextmanager
def get_db():
    """Get database connection with proper settings."""
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")  # Better concurrency
    conn.execute("PRAGMA busy_timeout=30000")  # 30s timeout
    try:
        yield conn
    finally:
        conn.close()


def init_schema() -> None:
    """Create database schema if not exists."""
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paper_id TEXT UNIQUE NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                worker_id TEXT,
                attempts INTEGER DEFAULT 0,
                error TEXT,
                started_at TEXT,
                completed_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_status ON jobs(status);
            CREATE INDEX IF NOT EXISTS idx_paper_id ON jobs(paper_id);

            CREATE TABLE IF NOT EXISTS qa_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paper_id TEXT NOT NULL,
                model TEXT NOT NULL,
                overall_score REAL,
                accuracy REAL,
                fluency REAL,
                terminology REAL,
                completeness REAL,
                formatting REAL,
                organization REAL,
                comments TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_qa_paper_id ON qa_results(paper_id);

            CREATE TABLE IF NOT EXISTS worker_heartbeats (
                worker_id TEXT PRIMARY KEY,
                last_heartbeat TEXT NOT NULL,
                jobs_completed INTEGER DEFAULT 0
            );
        """)
        conn.commit()


def add_jobs(paper_ids: List[str]) -> int:
    """
    Add jobs to queue.

    Args:
        paper_ids: List of paper IDs to process

    Returns:
        Number of jobs added
    """
    with get_db() as conn:
        # Use INSERT OR IGNORE to skip duplicates
        added = 0
        for paper_id in paper_ids:
            cursor = conn.execute(
                "INSERT OR IGNORE INTO jobs (paper_id, status) VALUES (?, 'pending')",
                (paper_id,)
            )
            added += cursor.rowcount
        conn.commit()
        return added


def claim_job(worker_id: str) -> Optional[Dict]:
    """
    Atomically claim a pending job.

    Args:
        worker_id: Worker identifier

    Returns:
        Job dict or None if no jobs available
    """
    with get_db() as conn:
        # Find a pending job
        cursor = conn.execute(
            """
            SELECT id, paper_id, attempts
            FROM jobs
            WHERE status = 'pending'
            ORDER BY id ASC
            LIMIT 1
            """
        )
        row = cursor.fetchone()

        if not row:
            return None

        job_id = row['id']

        # Atomically claim it
        now = datetime.utcnow().isoformat()
        conn.execute(
            """
            UPDATE jobs
            SET status = 'in_progress',
                worker_id = ?,
                started_at = ?
            WHERE id = ? AND status = 'pending'
            """,
            (worker_id, now, job_id)
        )
        conn.commit()

        # Return job details
        return {
            'id': row['id'],
            'paper_id': row['paper_id'],
            'attempts': row['attempts']
        }


def complete_job(job_id: int) -> None:
    """Mark job as completed."""
    with get_db() as conn:
        now = datetime.utcnow().isoformat()
        conn.execute(
            """
            UPDATE jobs
            SET status = 'completed', completed_at = ?
            WHERE id = ?
            """,
            (now, job_id)
        )
        conn.commit()


def fail_job(job_id: int, error: str, max_attempts: int = 3) -> None:
    """
    Mark job as failed and retry if attempts < max.

    Args:
        job_id: Job ID
        error: Error message
        max_attempts: Max retry attempts
    """
    with get_db() as conn:
        cursor = conn.execute("SELECT attempts FROM jobs WHERE id = ?", (job_id,))
        row = cursor.fetchone()

        if not row:
            return

        attempts = row['attempts'] + 1

        if attempts >= max_attempts:
            # Permanent failure
            conn.execute(
                """
                UPDATE jobs
                SET status = 'failed',
                    attempts = ?,
                    error = ?
                WHERE id = ?
                """,
                (attempts, error, job_id)
            )
        else:
            # Retry - reset to pending
            conn.execute(
                """
                UPDATE jobs
                SET status = 'pending',
                    attempts = ?,
                    error = ?,
                    worker_id = NULL,
                    started_at = NULL
                WHERE id = ?
                """,
                (attempts, error, job_id)
            )

        conn.commit()


def update_heartbeat(worker_id: str) -> None:
    """Update worker heartbeat."""
    with get_db() as conn:
        now = datetime.utcnow().isoformat()
        conn.execute(
            """
            INSERT INTO worker_heartbeats (worker_id, last_heartbeat, jobs_completed)
            VALUES (?, ?, 0)
            ON CONFLICT(worker_id) DO UPDATE SET last_heartbeat = ?
            """,
            (worker_id, now, now)
        )
        conn.commit()


def increment_worker_jobs(worker_id: str) -> None:
    """Increment worker job counter."""
    with get_db() as conn:
        conn.execute(
            """
            UPDATE worker_heartbeats
            SET jobs_completed = jobs_completed + 1
            WHERE worker_id = ?
            """,
            (worker_id,)
        )
        conn.commit()


def get_stats() -> Dict:
    """Get queue statistics."""
    with get_db() as conn:
        cursor = conn.execute(
            """
            SELECT
                status,
                COUNT(*) as count
            FROM jobs
            GROUP BY status
            """
        )

        stats = {
            'total': 0,
            'pending': 0,
            'in_progress': 0,
            'completed': 0,
            'failed': 0
        }

        for row in cursor:
            stats[row['status']] = row['count']
            stats['total'] += row['count']

        # QA stats
        cursor = conn.execute("SELECT COUNT(*) as count FROM qa_results")
        stats['qa_completed'] = cursor.fetchone()['count']

        cursor = conn.execute("SELECT AVG(overall_score) as avg FROM qa_results")
        avg_row = cursor.fetchone()
        stats['qa_avg_score'] = avg_row['avg'] if avg_row['avg'] else 0.0

        # Worker stats
        cursor = conn.execute("SELECT COUNT(*) as count FROM worker_heartbeats")
        stats['active_workers'] = cursor.fetchone()['count']

        return stats


def reset_stuck_jobs(timeout_minutes: int = 10) -> int:
    """
    Reset jobs stuck in 'in_progress' for too long.

    Args:
        timeout_minutes: Minutes before considering job stuck

    Returns:
        Number of jobs reset
    """
    with get_db() as conn:
        cutoff = (datetime.utcnow() - timedelta(minutes=timeout_minutes)).isoformat()

        cursor = conn.execute(
            """
            UPDATE jobs
            SET status = 'pending',
                worker_id = NULL,
                started_at = NULL
            WHERE status = 'in_progress'
            AND started_at < ?
            """,
            (cutoff,)
        )

        count = cursor.rowcount
        conn.commit()
        return count


def save_qa_result(
    paper_id: str,
    model: str,
    overall: float,
    accuracy: float,
    fluency: float,
    terminology: float,
    completeness: float = 0.0,
    formatting: float = 0.0,
    organization: float = 0.0,
    comments: str = ""
) -> None:
    """Save QA evaluation result."""
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO qa_results (
                paper_id, model, overall_score, accuracy, fluency,
                terminology, completeness, formatting, organization, comments
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (paper_id, model, overall, accuracy, fluency, terminology, completeness, formatting, organization, comments)
        )
        conn.commit()


def get_recent_completions(limit: int = 5) -> List[Dict]:
    """Get recent completed jobs."""
    with get_db() as conn:
        cursor = conn.execute(
            """
            SELECT paper_id, worker_id, completed_at
            FROM jobs
            WHERE status = 'completed'
            ORDER BY completed_at DESC
            LIMIT ?
            """,
            (limit,)
        )
        return [dict(row) for row in cursor]


def get_failed_jobs() -> List[Dict]:
    """Get all permanently failed jobs."""
    with get_db() as conn:
        cursor = conn.execute(
            """
            SELECT id, paper_id, attempts, error
            FROM jobs
            WHERE status = 'failed'
            ORDER BY id
            """
        )
        return [dict(row) for row in cursor]
