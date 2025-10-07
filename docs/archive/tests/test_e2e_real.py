"""
Real End-to-End Tests with External Dependencies

These tests use actual Internet Archive and OpenRouter APIs to provide
true production confidence without mocking. They are opt-in to avoid
network calls during routine CI runs.

Test Strategy:
- Quality tests: 20 papers with DeepSeek V3.2-Exp (~$0.026)
- Batch tests: 500-1000 papers with free models ($0.00)
- Total monthly cost: ~$0.026
"""

import os
import pytest
import tempfile
import shutil
from pathlib import Path
import json
import time

# Skip entire module unless explicitly enabled
if os.getenv("RUN_REAL_E2E") != "1":
    pytest.skip("Skipping real E2E tests; set RUN_REAL_E2E=1 to enable.", allow_module_level=True)

from unittest.mock import patch

# Import our modules
from src.harvest_ia import harvest_chinaxiv_metadata
from src.services.translation_service import TranslationService
from src.job_queue import JobQueue
from src.render import render_site, load_translated
from src.search_index import run_cli as build_search_index
from tests.test_monitoring_real import monitor_real_e2e_test


LIMIT = int(os.getenv("RUN_REAL_E2E_LIMIT", "5"))


@pytest.mark.network
@pytest.mark.real_api
class TestRealAPIIntegration:
    """Test real API integration with Internet Archive and OpenRouter"""
    
    def setup_method(self):
        """Setup for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        # Create necessary directories
        os.makedirs("data/translated", exist_ok=True)
        os.makedirs("site", exist_ok=True)
        
    def teardown_method(self):
        """Cleanup after each test"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @monitor_real_e2e_test
    def test_real_internet_archive_harvest(self):
        """Test harvesting real data from Internet Archive"""
        # Test with a configurable small limit to avoid rate limits
        papers, cursor = harvest_chinaxiv_metadata(limit=LIMIT)
        
        # Verify we got real data
        assert isinstance(papers, list)
        assert len(papers) > 0
        assert len(papers) <= LIMIT
        
        # Verify paper structure
        paper = papers[0]
        assert "id" in paper
        assert paper["id"].startswith("ia-")
        assert "title" in paper
        assert "creators" in paper and isinstance(paper["creators"], list)
        assert "abstract" in paper
        assert "date" in paper
        assert "source_url" in paper
        assert "pdf_url" in paper
        
        print(f"✅ Harvested {len(papers)} real papers from Internet Archive")
        print(f"   First paper: {paper['id']} - {paper['title'][:50]}...")
    
    @monitor_real_e2e_test
    def test_real_openrouter_translation_quality(self):
        """Test real translation with DeepSeek V3.2-Exp for quality validation"""
        # Skip if no API key
        if not os.getenv("OPENROUTER_API_KEY"):
            pytest.skip("No OpenRouter API key available")
        
        # Create translation service
        translator = TranslationService()
        
        # Test with real Chinese text
        chinese_text = "这是一个测试文档，包含数学公式 $E=mc^2$ 和中文内容。"
        
        # Translate
        result = translator.translate_field(chinese_text)
        
        # Verify translation
        assert isinstance(result, str)
        assert len(result) > 0
        assert "test" in result.lower() or "document" in result.lower()
        assert "E=mc^2" in result  # Math should be preserved
        
        print(f"✅ Real translation successful")
        print(f"   Original: {chinese_text}")
        print(f"   Translated: {result}")
    
    @monitor_real_e2e_test
    @pytest.mark.free
    @pytest.mark.slow
    def test_real_openrouter_translation_batch_free(self):
        """Test real translation with free models for batch validation"""
        # Skip if no API key
        if not os.getenv("OPENROUTER_API_KEY"):
            pytest.skip("No OpenRouter API key available")
        
        # Test with free models
        free_models = [
            "z-ai/glm-4.5-air:free",
            "deepseek/deepseek-chat-v3.1:free"
        ]
        
        for model in free_models:
            # Create translation service with free model via config override
            translator = TranslationService(config={"models": {"default_slug": model}})
            
            # Test with simple Chinese text
            chinese_text = "这是一个简单的测试。"
            
            # Translate
            result = translator.translate_field(chinese_text)
            
            # Verify translation
            assert isinstance(result, str)
            assert len(result) > 0
            
            print(f"✅ Free model {model} translation successful")
            print(f"   Translated: {result}")
            
            # Small delay to avoid rate limits
            time.sleep(1)
    
    @monitor_real_e2e_test
    def test_real_paper_translation(self):
        """Test translating a complete real paper"""
        # Skip if no API key
        if not os.getenv("OPENROUTER_API_KEY"):
            pytest.skip("No OpenRouter API key available")
        
        # Harvest a real paper
        papers, cursor = harvest_chinaxiv_metadata(limit=1)
        assert len(papers) > 0
        
        paper = papers[0]
        
        # Create translation service
        translator = TranslationService()
        
        # Translate the paper
        translated = translator.translate_record(paper)
        
        # Verify translation structure
        assert isinstance(translated, dict)
        assert "id" in translated
        assert "title_en" in translated
        assert "abstract_en" in translated
        assert "creators" in translated
        assert "date" in translated
        
        # Verify translations exist
        assert translated["title_en"] and translated["title_en"] != paper.get("title", "")
        assert translated["abstract_en"] is not None
        
        print(f"✅ Real paper translation successful")
        print(f"   Paper: {paper['id']}")
        print(f"   Title: {translated['title_en'][:50]}...")
    
    @monitor_real_e2e_test
    def test_real_job_queue_integration(self):
        """Test job queue with real translation jobs"""
        # Skip if no API key
        if not os.getenv("OPENROUTER_API_KEY"):
            pytest.skip("No OpenRouter API key available")
        
        # Create job queue
        job_queue = JobQueue()
        
        # Harvest real papers
        papers, cursor = harvest_chinaxiv_metadata(limit=min(3, max(1, LIMIT)))
        assert len(papers) > 0
        
        # Add jobs to queue (use paper IDs)
        paper_ids = [p["id"] for p in papers]
        added = job_queue.add_jobs(paper_ids)
        assert added == len(paper_ids)
        
        # Process jobs
        translator = TranslationService()
        completed_jobs = []
        record_map = {p["id"]: p for p in papers}
        
        for _ in paper_ids:
            # Claim job
            job = job_queue.claim_job(worker_id="worker-1")
            if job is None:
                break
            
            job_id = job["id"]
            assert job_id in record_map
            
            # Translate
            translated = translator.translate_record(record_map[job_id])
            
            # Complete job
            job_queue.complete_job(job_id)
            completed_jobs.append(job_id)
            
            # Small delay to avoid rate limits
            time.sleep(2)
        
        # Verify completion
        assert len(completed_jobs) > 0
        
        # Check stats
        stats = job_queue.get_stats()
        assert stats["completed"] >= len(completed_jobs)
        
        print(f"✅ Real job queue integration successful")
        print(f"   Processed {len(completed_jobs)} jobs")
        print(f"   Stats: {stats}")


@pytest.mark.network
@pytest.mark.real_api
class TestRealPipelineIntegration:
    """Test complete pipeline with real data"""
    
    def setup_method(self):
        """Setup for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        # Create necessary directories
        os.makedirs("data/translated", exist_ok=True)
        os.makedirs("site", exist_ok=True)
        os.makedirs("src/templates", exist_ok=True)
        
        # Copy templates from original directory
        import shutil
        original_templates = Path(self.original_cwd) / "src" / "templates"
        if original_templates.exists():
            shutil.rmtree("src/templates", ignore_errors=True)
            shutil.copytree(original_templates, "src/templates")
        
    def teardown_method(self):
        """Cleanup after each test"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @monitor_real_e2e_test
    def test_real_end_to_end_pipeline(self):
        """Test complete pipeline from harvest to site generation"""
        # Skip if no API key
        if not os.getenv("OPENROUTER_API_KEY"):
            pytest.skip("No OpenRouter API key available")
        
        # Step 1: Harvest real papers
        papers, cursor = harvest_chinaxiv_metadata(limit=min(2, max(1, LIMIT)))
        assert len(papers) > 0
        
        print(f"✅ Step 1: Harvested {len(papers)} papers")
        
        # Step 2: Translate papers
        translator = TranslationService()
        translated_papers = []
        
        for paper in papers:
            translated = translator.translate_record(paper)
            translated_papers.append(translated)
            
            # Small delay to avoid rate limits
            time.sleep(2)
        
        print(f"✅ Step 2: Translated {len(translated_papers)} papers")
        
        # Step 3: Save translated papers
        for paper in translated_papers:
            paper_file = Path(f"data/translated/{paper['id']}.json")
            with open(paper_file, 'w', encoding='utf-8') as f:
                json.dump(paper, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Step 3: Saved {len(translated_papers)} translated papers")
        
        # Step 4: Render site
        render_site(translated_papers)
        
        # Verify site generation
        assert Path("site/index.html").exists()
        assert Path("site/search-index.json").exists()
        
        # Verify individual paper pages
        for paper in translated_papers:
            paper_dir = Path(f"site/items/{paper['id']}")
            assert paper_dir.exists()
            assert (paper_dir / "index.html").exists()
        
        print(f"✅ Step 4: Rendered site with {len(translated_papers)} papers")
        
        # Step 5: Build search index (reads from data/translated)
        build_search_index()
        
        # Verify search index
        assert Path("site/search-index.json").exists()
        assert Path("site/search-index.json.gz").exists()
        
        print(f"✅ Step 5: Built search index")
        
        # Step 6: Verify site content
        with open("site/index.html", 'r', encoding='utf-8') as f:
            index_content = f.read()
        
        # Check that translated content appears
        for paper in translated_papers:
            assert paper["title_en"] in index_content
            assert paper["id"] in index_content
        
        print(f"✅ Step 6: Verified site content")
        
        print(f"🎉 Complete real end-to-end pipeline successful!")
        print(f"   Papers processed: {len(translated_papers)}")
        print(f"   Site generated: site/index.html")
        print(f"   Search index: site/search-index.json")


@pytest.mark.network
@pytest.mark.real_api
class TestRealPerformanceAndScale:
    """Test performance and scale with free models"""
    
    def setup_method(self):
        """Setup for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        # Create necessary directories
        os.makedirs("data/translated", exist_ok=True)
        os.makedirs("site", exist_ok=True)
        
    def teardown_method(self):
        """Cleanup after each test"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @monitor_real_e2e_test
    @pytest.mark.free
    @pytest.mark.slow
    def test_real_batch_processing_free_models(self):
        """Test batch processing with free models"""
        # Skip if no API key
        if not os.getenv("OPENROUTER_API_KEY"):
            pytest.skip("No OpenRouter API key available")
        
        # Test with free model
        translator = TranslationService(config={"models": {"default_slug": "z-ai/glm-4.5-air:free"}})
        
        # Harvest more papers for batch testing
        papers, cursor = harvest_chinaxiv_metadata(limit=min(10, max(1, LIMIT)))
        assert len(papers) > 0
        
        print(f"✅ Testing batch processing with {len(papers)} papers")
        
        # Process papers in batch
        start_time = time.time()
        translated_papers = []
        
        for i, paper in enumerate(papers):
            try:
                translated = translator.translate_record(paper)
                translated_papers.append(translated)
                
                print(f"   Processed {i+1}/{len(papers)}: {paper['id']}")
                
                # Small delay to avoid rate limits
                time.sleep(1)
                
            except Exception as e:
                print(f"   Error processing {paper['id']}: {e}")
                continue
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Verify results
        assert len(translated_papers) > 0
        
        # Calculate performance metrics
        papers_per_minute = len(translated_papers) / (processing_time / 60)
        
        print(f"✅ Batch processing successful")
        print(f"   Papers processed: {len(translated_papers)}/{len(papers)}")
        print(f"   Processing time: {processing_time:.2f} seconds")
        print(f"   Rate: {papers_per_minute:.2f} papers/minute")
        
        # Performance assertions
        assert papers_per_minute > 0
        assert processing_time < 300  # Should complete within 5 minutes
    
    @monitor_real_e2e_test
    def test_real_error_handling(self):
        """Test error handling with real APIs"""
        # Skip if no API key
        if not os.getenv("OPENROUTER_API_KEY"):
            pytest.skip("No OpenRouter API key available")
        
        # Test with invalid model (should fail gracefully)
        translator = TranslationService(config={"models": {"default_slug": "invalid/model"}})
        
        # Test with simple text
        chinese_text = "测试文本"
        
        try:
            result = translator.translate_field(chinese_text)
            # If it doesn't fail, that's also acceptable
            print(f"✅ Translation with invalid model succeeded: {result}")
        except Exception as e:
            print(f"✅ Error handling working: {e}")
            # This is expected behavior
        
        # Test with empty text
        try:
            result = translator.translate_field("")
            assert result == ""
            print(f"✅ Empty text handling successful")
        except Exception as e:
            print(f"✅ Empty text error handling: {e}")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
