"""
Tests for job queue functionality.
"""
import pytest
import sqlite3
import tempfile
import os
from unittest.mock import patch, MagicMock
from src.job_queue import (
    init_schema, add_jobs, claim_job, complete_job, fail_job,
    reset_stuck_jobs, save_qa_result, get_stats
)


class TestJobQueue:
    """Test job queue functionality."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            db_path = f.name
        
        # Override the global DB_PATH for testing
        with patch('src.job_queue.DB_PATH', db_path):
            yield db_path
        
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_init_schema(self, temp_db):
        """Test database schema initialization."""
        with patch('src.job_queue.DB_PATH', temp_db):
            init_schema()
            
            # Verify tables were created
            with sqlite3.connect(temp_db) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                assert 'jobs' in tables
                assert 'qa_results' in tables
                assert 'worker_heartbeats' in tables
    
    def test_add_jobs(self, temp_db):
        """Test adding jobs to the queue."""
        with patch('src.job_queue.DB_PATH', temp_db):
            init_schema()
            
            paper_ids = ['paper-1', 'paper-2', 'paper-3']
            added = add_jobs(paper_ids)
            
            assert added == 3
            
            # Verify jobs were added
            with sqlite3.connect(temp_db) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT paper_id FROM jobs")
                results = [row[0] for row in cursor.fetchall()]
                
                assert set(results) == set(paper_ids)
    
    def test_add_jobs_duplicate(self, temp_db):
        """Test adding duplicate jobs."""
        with patch('src.job_queue.DB_PATH', temp_db):
            init_schema()
            
            paper_ids = ['paper-1', 'paper-2']
            add_jobs(paper_ids)
            
            # Try to add duplicates
            paper_ids_dup = ['paper-2', 'paper-3']
            added = add_jobs(paper_ids_dup)
            
            # Should only add the new one
            assert added == 1
            
            # Verify total count
            with sqlite3.connect(temp_db) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM jobs")
                count = cursor.fetchone()[0]
                assert count == 3
    
    def test_claim_job(self, temp_db):
        """Test claiming a job."""
        with patch('src.job_queue.DB_PATH', temp_db):
            init_schema()
            
            paper_ids = ['paper-1', 'paper-2', 'paper-3']
            add_jobs(paper_ids)
            
            # Claim a job
            job = claim_job('worker-1')
            
            assert job is not None
            assert job['paper_id'] in paper_ids
            assert job['id'] is not None
            
            # Verify job status in database
            with sqlite3.connect(temp_db) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT status, worker_id FROM jobs WHERE paper_id = ?", (job['paper_id'],))
                status, worker_id = cursor.fetchone()
                assert status == 'in_progress'
                assert worker_id == 'worker-1'
    
    def test_claim_job_no_jobs(self, temp_db):
        """Test claiming when no jobs available."""
        with patch('src.job_queue.DB_PATH', temp_db):
            init_schema()
            
            job = claim_job('worker-1')
            assert job is None
    
    def test_claim_job_concurrent(self, temp_db):
        """Test concurrent job claiming."""
        with patch('src.job_queue.DB_PATH', temp_db):
            init_schema()
            
            paper_ids = ['paper-1', 'paper-2']
            add_jobs(paper_ids)
            
            # Simulate concurrent claims
            job1 = claim_job('worker-1')
            job2 = claim_job('worker-2')
            
            # Should get different jobs
            assert job1 is not None
            assert job2 is not None
            assert job1['paper_id'] != job2['paper_id']
            
            # Third claim should return None
            job3 = claim_job('worker-3')
            assert job3 is None
    
    def test_complete_job(self, temp_db):
        """Test completing a job."""
        with patch('src.job_queue.DB_PATH', temp_db):
            init_schema()
            
            paper_ids = ['paper-1']
            add_jobs(paper_ids)
            
            # Claim and complete job
            job = claim_job('worker-1')
            assert job is not None
            
            complete_job(job['id'])
            
            # Verify job status
            with sqlite3.connect(temp_db) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT status FROM jobs WHERE id = ?", (job['id'],))
                status = cursor.fetchone()[0]
                assert status == 'completed'
    
    def test_fail_job(self, temp_db):
        """Test failing a job."""
        with patch('src.job_queue.DB_PATH', temp_db):
            init_schema()
            
            paper_ids = ['paper-1']
            add_jobs(paper_ids)
            
            # Claim and fail job
            job = claim_job('worker-1')
            assert job is not None
            
            fail_job(job['id'], 'Test error')
            
            # Verify job status (should be pending for retry, not failed yet)
            with sqlite3.connect(temp_db) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT status, error, attempts FROM jobs WHERE id = ?", (job['id'],))
                status, error, attempts = cursor.fetchone()
                assert status == 'pending'  # Retry, not failed yet
                assert error == 'Test error'
                assert attempts == 1
    
    def test_fail_job_retry(self, temp_db):
        """Test job retry logic."""
        with patch('src.job_queue.DB_PATH', temp_db):
            init_schema()
            
            paper_ids = ['paper-1']
            add_jobs(paper_ids)
            
            # Claim and fail job multiple times
            job = claim_job('worker-1')
            assert job is not None
            
            # First failure
            fail_job(job['id'], 'Error 1')
            
            # Should be able to claim again
            job2 = claim_job('worker-1')
            assert job2 is not None
            assert job2['paper_id'] == job['paper_id']
            
            # Second failure
            fail_job(job2['id'], 'Error 2')
            
            # Third failure should mark as failed
            job3 = claim_job('worker-1')
            assert job3 is not None
            fail_job(job3['id'], 'Error 3')
            
            # Should not be claimable anymore
            job4 = claim_job('worker-1')
            assert job4 is None
            
            # Verify final status
            with sqlite3.connect(temp_db) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT status, attempts FROM jobs WHERE paper_id = ?", (job['paper_id'],))
                status, attempts = cursor.fetchone()
                assert status == 'failed'
                assert attempts == 3
    
    def test_reset_stuck_jobs(self, temp_db):
        """Test resetting stuck jobs."""
        with patch('src.job_queue.DB_PATH', temp_db):
            init_schema()
            
            paper_ids = ['paper-1', 'paper-2']
            add_jobs(paper_ids)
            
            # Claim jobs
            job1 = claim_job('worker-1')
            job2 = claim_job('worker-2')
            
            # Manually set old timestamps to simulate stuck jobs
            with sqlite3.connect(temp_db) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE jobs 
                    SET started_at = datetime('now', '-1 hour')
                    WHERE id IN (?, ?)
                """, (job1['id'], job2['id']))
                conn.commit()
            
            # Reset stuck jobs
            reset_count = reset_stuck_jobs()
            assert reset_count == 2
            
            # Verify jobs are back to pending
            with sqlite3.connect(temp_db) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT status FROM jobs WHERE id IN (?, ?)", (job1['id'], job2['id']))
                statuses = [row[0] for row in cursor.fetchall()]
                assert all(status == 'pending' for status in statuses)
    
    def test_save_qa_result(self, temp_db):
        """Test saving QA results."""
        with patch('src.job_queue.DB_PATH', temp_db):
            init_schema()
            
            save_qa_result(
                paper_id='paper-1',
                model='test-model',
                overall=9.5,
                accuracy=9.0,
                fluency=10.0,
                terminology=9.5,
                completeness=9.0,
                comments='Great translation'
            )
            
            # Verify QA result was saved
            with sqlite3.connect(temp_db) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM qa_results WHERE paper_id = ?", ('paper-1',))
                result = cursor.fetchone()
                
                assert result is not None
                assert result[1] == 'paper-1'  # paper_id
                assert result[2] == 'test-model'  # model
                assert result[3] == 9.5  # overall_score
    
    def test_get_stats(self, temp_db):
        """Test getting queue statistics."""
        with patch('src.job_queue.DB_PATH', temp_db):
            init_schema()
            
            # Add some jobs
            paper_ids = ['paper-1', 'paper-2', 'paper-3', 'paper-4']
            add_jobs(paper_ids)
            
            # Claim one job
            job = claim_job('worker-1')
            complete_job(job['id'])
            
            # Fail another job (but it will retry, not fail permanently)
            job2 = claim_job('worker-1')
            fail_job(job2['id'], 'Test error')
            
            # Get stats
            stats = get_stats()
            
            assert stats['total'] == 4
            assert stats['completed'] == 1
            assert stats['failed'] == 0  # Not failed yet, just retrying
            assert stats['pending'] == 3  # 2 original + 1 retry
            assert stats['in_progress'] == 0
    
    def test_worker_heartbeat(self, temp_db):
        """Test worker heartbeat functionality."""
        with patch('src.job_queue.DB_PATH', temp_db):
            init_schema()
            
            # Update heartbeat
            from src.job_queue import update_heartbeat
            update_heartbeat('worker-1')
            
            # Verify heartbeat was saved
            with sqlite3.connect(temp_db) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT last_heartbeat, jobs_completed FROM worker_heartbeats WHERE worker_id = ?", ('worker-1',))
                result = cursor.fetchone()
                
                assert result is not None
                assert result[1] == 0  # jobs_completed starts at 0
                assert result[0] is not None  # last_heartbeat
