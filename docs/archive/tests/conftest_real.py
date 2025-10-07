"""
Configuration for Real E2E Tests

This file provides fixtures and configuration for tests that use
real external APIs (Internet Archive, OpenRouter).
"""

import os
import pytest
import tempfile
import shutil
from pathlib import Path


@pytest.fixture(scope="session")
def real_test_config():
    """Configuration for real E2E tests"""
    return {
        "quality_tests": {
            "model": "deepseek/deepseek-v3.2-exp",
            "papers": 20,
            "cost_per_paper": 0.0013,
            "total_cost": 0.026
        },
        "batch_tests": {
            "models": [
                "z-ai/glm-4.5-air:free",
                "deepseek/deepseek-chat-v3.1:free"
            ],
            "papers": 500,
            "cost_per_paper": 0.0,
            "total_cost": 0.0
        },
        "rate_limits": {
            "openrouter_delay": 1,  # seconds between requests
            "ia_delay": 0.5,  # seconds between IA requests
            "batch_delay": 2  # seconds between batch requests
        }
    }


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace for tests"""
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    
    # Create necessary directories
    os.makedirs(f"{temp_dir}/data/translated", exist_ok=True)
    os.makedirs(f"{temp_dir}/site", exist_ok=True)
    os.makedirs(f"{temp_dir}/data/monitoring", exist_ok=True)
    
    # Change to temp directory
    os.chdir(temp_dir)
    
    yield temp_dir
    
    # Cleanup
    os.chdir(original_cwd)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def api_key_required():
    """Skip test if OpenRouter API key is not available"""
    if not os.getenv("OPENROUTER_API_KEY"):
        pytest.skip("OpenRouter API key required for real E2E tests")


@pytest.fixture
def real_papers():
    """Harvest real papers for testing"""
    from src.harvest_ia import harvest_chinaxiv_metadata
    
    # Harvest a small number of real papers
    papers, cursor = harvest_chinaxiv_metadata(limit=5)
    
    if not papers:
        pytest.skip("No papers available from Internet Archive")
    
    return papers


@pytest.fixture
def real_translator():
    """Create a real translation service"""
    from src.services.translation_service import TranslationService
    
    # Use DeepSeek V3.2-Exp for quality tests via config override
    return TranslationService(config={"models": {"default_slug": "deepseek/deepseek-v3.2-exp"}})


@pytest.fixture
def free_translator():
    """Create a translation service with free model"""
    from src.services.translation_service import TranslationService
    
    # Use free model for batch tests via config override
    return TranslationService(config={"models": {"default_slug": "z-ai/glm-4.5-air:free"}})


@pytest.fixture
def real_job_queue():
    """Create a real job queue"""
    from src.job_queue import JobQueue
    
    return JobQueue()


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment before each test"""
    # Ensure we're in a clean state
    pass


def pytest_configure(config):
    """Configure pytest for real E2E tests"""
    # Add custom markers
    config.addinivalue_line(
        "markers", "real_api: mark test as using real APIs"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "cost: mark test as having API costs"
    )
    config.addinivalue_line(
        "markers", "free: mark test as using free models"
    )
    config.addinivalue_line(
        "markers", "network: mark test as requiring network access"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection for real E2E tests"""
    for item in items:
        # Mark real API tests
        if "real" in item.nodeid:
            item.add_marker(pytest.mark.real_api)
        
        # Mark slow tests
        if "batch" in item.nodeid or "scale" in item.nodeid:
            item.add_marker(pytest.mark.slow)
        
        # Mark cost tests
        if "quality" in item.nodeid or "deepseek" in item.nodeid:
            item.add_marker(pytest.mark.cost)
        
        # Mark free tests
        if "free" in item.nodeid or "batch" in item.nodeid:
            item.add_marker(pytest.mark.free)

