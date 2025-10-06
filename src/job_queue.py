"""
Simplified file-based job queue for batch translation.
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class JobQueue:
    """Simplified file-based job queue."""
    
    def __init__(self):
        self.jobs_dir = Path("data/jobs")
        self.jobs_dir.mkdir(exist_ok=True)
    
    def add_jobs(self, paper_ids: List[str]) -> int:
        """Add jobs to queue."""
        added = 0
        for paper_id in paper_ids:
            job_file = self.jobs_dir / f"{paper_id}.json"
            if not job_file.exists():
                job = {
                    "id": paper_id,
                    "status": "pending",
                    "created_at": datetime.now().isoformat(),
                    "attempts": 0
                }
                with open(job_file, "w") as f:
                    json.dump(job, f)
                added += 1
        return added
    
    def claim_job(self, worker_id: str) -> Optional[Dict]:
        """Claim a pending job."""
        for job_file in self.jobs_dir.glob("*.json"):
            with open(job_file, "r") as f:
                job = json.load(f)
            
            if job["status"] == "pending":
                job["status"] = "in_progress"
                job["worker_id"] = worker_id
                job["started_at"] = datetime.now().isoformat()
                
                with open(job_file, "w") as f:
                    json.dump(job, f)
                
                return job
        return None
    
    def complete_job(self, job_id: str):
        """Mark job as completed."""
        job_file = self.jobs_dir / f"{job_id}.json"
        if job_file.exists():
            with open(job_file, "r") as f:
                job = json.load(f)
            
            job["status"] = "completed"
            job["completed_at"] = datetime.now().isoformat()
            
            with open(job_file, "w") as f:
                json.dump(job, f)
    
    def fail_job(self, job_id: str, error: str):
        """Mark job as failed."""
        job_file = self.jobs_dir / f"{job_id}.json"
        if job_file.exists():
            with open(job_file, "r") as f:
                job = json.load(f)
            
            job["attempts"] += 1
            job["last_error"] = error
            
            if job["attempts"] >= 3:
                job["status"] = "failed"
            else:
                job["status"] = "pending"
            
            with open(job_file, "w") as f:
                json.dump(job, f)
    
    def get_stats(self) -> Dict:
        """Get job statistics."""
        stats = {"total": 0, "pending": 0, "in_progress": 0, "completed": 0, "failed": 0}
        
        for job_file in self.jobs_dir.glob("*.json"):
            with open(job_file, "r") as f:
                job = json.load(f)
            
            stats["total"] += 1
            stats[job["status"]] += 1
        
        return stats
    
    def cleanup_completed(self, days: int = 7):
        """Clean up completed jobs older than specified days."""
        cutoff = datetime.now() - timedelta(days=days)
        
        for job_file in self.jobs_dir.glob("*.json"):
            with open(job_file, "r") as f:
                job = json.load(f)
            
            if job["status"] == "completed":
                try:
                    completed_at = datetime.fromisoformat(job.get("completed_at", ""))
                    if completed_at < cutoff:
                        job_file.unlink()
                except ValueError:
                    continue


# Global job queue instance
job_queue = JobQueue()


# Convenience functions
def add_jobs(paper_ids: List[str]) -> int:
    """Convenience function to add jobs."""
    return job_queue.add_jobs(paper_ids)


def claim_job(worker_id: str) -> Optional[Dict]:
    """Convenience function to claim a job."""
    return job_queue.claim_job(worker_id)


def complete_job(job_id: str):
    """Convenience function to complete a job."""
    job_queue.complete_job(job_id)


def fail_job(job_id: str, error: str):
    """Convenience function to fail a job."""
    job_queue.fail_job(job_id, error)


def get_stats() -> Dict:
    """Convenience function to get job statistics."""
    return job_queue.get_stats()