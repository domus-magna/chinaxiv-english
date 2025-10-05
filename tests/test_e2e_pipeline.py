"""
End-to-end test for the entire ChinaXiv English translation pipeline.

This test validates the complete workflow from harvesting to translation to rendering.
"""
import json
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.harvest_ia import harvest_chinaxiv_metadata
from src.translate import translate_paper
from src.render import render_site, load_translated
from src.search_index import run_cli as build_search_index


class TestE2EPipeline:
    """End-to-end pipeline test."""
    
    def setup_method(self):
        """Set up test environment."""
        # Create temporary directory for test data
        self.test_dir = tempfile.mkdtemp(prefix="chinaxiv_e2e_test_")
        self.original_cwd = os.getcwd()
        
        # Create test data structure
        self.data_dir = os.path.join(self.test_dir, "data")
        self.records_dir = os.path.join(self.data_dir, "records")
        self.translated_dir = os.path.join(self.data_dir, "translated")
        self.site_dir = os.path.join(self.test_dir, "site")
        
        os.makedirs(self.records_dir, exist_ok=True)
        os.makedirs(self.translated_dir, exist_ok=True)
        os.makedirs(self.site_dir, exist_ok=True)
        
        # Copy templates
        templates_src = os.path.join(self.original_cwd, "src", "templates")
        templates_dst = os.path.join(self.test_dir, "src", "templates")
        shutil.copytree(templates_src, templates_dst)
        
        # Copy assets
        assets_src = os.path.join(self.original_cwd, "assets")
        assets_dst = os.path.join(self.test_dir, "assets")
        shutil.copytree(assets_src, assets_dst)
        
        # Create test config
        self.test_config = {
            "models": {
                "default_slug": "deepseek/deepseek-v3.2-exp"
            },
            "glossary": [
                {"zh": "机器学习", "en": "machine learning"},
                {"zh": "深度学习", "en": "deep learning"}
            ],
            "cost": {
                "pricing_per_mtoken": {
                    "deepseek/deepseek-v3.2-exp": {
                        "input": 0.27,
                        "output": 0.27
                    }
                }
            },
            "license_mapping": {
                "CC BY": {"derivatives_allowed": True},
                "CC BY-SA": {"derivatives_allowed": True},
                "CC BY-NC": {"derivatives_allowed": False}
            }
        }
        
        # Create test paper data
        self.test_paper = {
            "id": "test-paper-001",
            "oai_identifier": "oai:chinaxiv.org:test-paper-001",
            "title": "基于深度学习的图像识别方法研究",
            "abstract": "本文提出了一种新的基于深度学习的图像识别方法。该方法使用卷积神经网络进行特征提取，并通过多层感知机进行分类。实验结果表明，该方法在多个数据集上取得了良好的性能。",
            "creators": ["张三", "李四"],
            "subjects": ["计算机科学", "人工智能"],
            "date": "2024-01-15",
            "license": {"type": "CC BY", "derivatives_allowed": True},
            "source_url": "https://example.com/paper1",
            "pdf_url": "https://example.com/paper1.pdf"
        }
        
        # Save test paper to records
        records_file = os.path.join(self.records_dir, "ia_test_20240115.json")
        with open(records_file, "w", encoding="utf-8") as f:
            json.dump([self.test_paper], f, ensure_ascii=False, indent=2)
        
        # Save test paper to selected.json
        selected_file = os.path.join(self.data_dir, "selected.json")
        with open(selected_file, "w", encoding="utf-8") as f:
            json.dump([self.test_paper], f, ensure_ascii=False, indent=2)
    
    def teardown_method(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    @patch('src.harvest_ia.http_get')
    def test_harvest_metadata(self, mock_http_get):
        """Test metadata harvesting from Internet Archive."""
        # Mock IA API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "items": [
                {
                    "identifier": "test-paper-001",
                    "title": "基于深度学习的图像识别方法研究",
                    "description": "本文提出了一种新的基于深度学习的图像识别方法。",
                    "creator": ["张三", "李四"],
                    "subject": ["计算机科学", "人工智能"],
                    "date": "2024-01-15",
                    "licenseurl": "https://creativecommons.org/licenses/by/4.0/",
                    "files": [
                        {"name": "test-paper-001.pdf", "format": "PDF"}
                    ]
                }
            ],
            "cursor": "next_cursor"
        }
        mock_http_get.return_value = mock_response
        
        # Change to test directory
        os.chdir(self.test_dir)
        
        # Run harvest
        result, cursor = harvest_chinaxiv_metadata(limit=1, min_year=2024)
        
        # Verify results
        assert len(result) == 1
        assert result[0]["id"] == "ia-test-paper-001"
        assert result[0]["title"] == "基于深度学习的图像识别方法研究"
        assert result[0]["license"]["type"] == "CC BY"
        assert result[0]["license"]["derivatives_allowed"] is True
    
    @patch('src.services.translation_service.TranslationService._call_openrouter')
    @patch('src.pdf_pipeline.process_paper')
    def test_translate_paper(self, mock_process_paper, mock_translate):
        """Test paper translation."""
        # Mock PDF processing
        mock_process_paper.return_value = {
            "pdf_path": "test.pdf",
            "num_paragraphs": 2,
            "paragraphs": [
                "这是第一段内容。",
                "这是第二段内容。"
            ]
        }
        
        # Mock translation responses
        mock_translate.side_effect = [
            "Research on Image Recognition Methods Based on Deep Learning",  # title
            "This paper proposes a new image recognition method based on deep learning.",  # abstract
            "This is the first paragraph content.",  # body paragraph 1
            "This is the second paragraph content."  # body paragraph 2
        ]
        
        # Change to test directory
        os.chdir(self.test_dir)
        
        # Run translation
        result_path = translate_paper(
            "test-paper-001", 
            dry_run=False, 
            with_full_text=True
        )
        
        # Verify translation file was created
        assert os.path.exists(result_path)
        
        # Load and verify translation
        with open(result_path, "r", encoding="utf-8") as f:
            translation = json.load(f)
        
        assert translation["id"] == "test-paper-001"
        assert translation["title_en"] == "Research on Image Recognition Methods Based on Deep Learning"
        assert translation["abstract_en"] == "This paper proposes a new image recognition method based on deep learning."
        assert translation["body_en"] is not None
        assert len(translation["body_en"]) == 2
        assert translation["body_en"][0] == "This is the first paragraph content."
        assert translation["body_en"][1] == "This is the second paragraph content."
        assert translation["license"]["derivatives_allowed"] is True
    
    @patch('src.services.translation_service.TranslationService._call_openrouter')
    def test_translate_paper_dry_run(self, mock_translate):
        """Test paper translation in dry run mode."""
        # Change to test directory
        os.chdir(self.test_dir)
        
        # Run translation in dry run mode
        result_path = translate_paper(
            "test-paper-001", 
            dry_run=True, 
            with_full_text=False
        )
        
        # Verify translation file was created
        assert os.path.exists(result_path)
        
        # Load and verify translation
        with open(result_path, "r", encoding="utf-8") as f:
            translation = json.load(f)
        
        assert translation["id"] == "test-paper-001"
        assert translation["title_en"] is not None
        assert translation["abstract_en"] is not None
        assert translation["body_en"] is None  # No full text in dry run
        
        # Verify no actual translation calls were made
        mock_translate.assert_not_called()
    
    def test_render_site(self):
        """Test site rendering."""
        # Create test translation file
        translation = {
            "id": "test-paper-001",
            "title_en": "Research on Image Recognition Methods Based on Deep Learning",
            "abstract_en": "This paper proposes a new image recognition method based on deep learning.",
            "body_en": ["This is the first paragraph.", "This is the second paragraph."],
            "creators": ["张三", "李四"],
            "subjects": ["计算机科学", "人工智能"],
            "date": "2024-01-15",
            "license": {"type": "CC BY", "derivatives_allowed": True},
            "source_url": "https://example.com/paper1",
            "pdf_url": "https://example.com/paper1.pdf"
        }
        
        translation_file = os.path.join(self.translated_dir, "test-paper-001.json")
        with open(translation_file, "w", encoding="utf-8") as f:
            json.dump(translation, f, ensure_ascii=False, indent=2)
        
        # Change to test directory
        os.chdir(self.test_dir)
        
        # Run rendering
        items = load_translated()
        render_site(items)
        
        # Verify site files were created
        assert os.path.exists(os.path.join(self.site_dir, "index.html"))
        assert os.path.exists(os.path.join(self.site_dir, "items", "ia-test-paper-001.html"))
        
        # Verify index.html contains the paper
        with open(os.path.join(self.site_dir, "index.html"), "r", encoding="utf-8") as f:
            index_content = f.read()
        assert "ia-test-paper-001" in index_content
        assert "Research on Image Recognition Methods Based on Deep Learning" in index_content
    
    def test_build_search_index(self):
        """Test search index building."""
        # Create test translation file
        translation = {
            "id": "test-paper-001",
            "title_en": "Research on Image Recognition Methods Based on Deep Learning",
            "abstract_en": "This paper proposes a new image recognition method based on deep learning.",
            "body_en": ["This is the first paragraph.", "This is the second paragraph."],
            "creators": ["张三", "李四"],
            "subjects": ["计算机科学", "人工智能"],
            "date": "2024-01-15",
            "license": {"type": "CC BY", "derivatives_allowed": True},
            "source_url": "https://example.com/paper1",
            "pdf_url": "https://example.com/paper1.pdf"
        }
        
        translation_file = os.path.join(self.translated_dir, "test-paper-001.json")
        with open(translation_file, "w", encoding="utf-8") as f:
            json.dump(translation, f, ensure_ascii=False, indent=2)
        
        # Change to test directory
        os.chdir(self.test_dir)
        
        # Run search index building
        build_search_index()
        
        # Verify search index was created
        search_index_file = os.path.join(self.site_dir, "search-index.json")
        assert os.path.exists(search_index_file)
        
        # Load and verify search index
        with open(search_index_file, "r", encoding="utf-8") as f:
            search_index = json.load(f)
        
        assert "ia-test-paper-001" in search_index
        assert "Research on Image Recognition Methods Based on Deep Learning" in search_index["test-paper-001"]["title"]
        assert "deep learning" in search_index["ia-test-paper-001"]["abstract"]
    
    @patch('src.harvest_ia.http_get')
    @patch('src.services.translation_service.TranslationService._call_openrouter')
    @patch('src.pdf_pipeline.process_paper')
    def test_complete_pipeline(self, mock_process_paper, mock_translate, mock_http_get):
        """Test complete pipeline from harvest to search index."""
        # Mock IA API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "items": [
                {
                    "identifier": "test-paper-001",
                    "title": "基于深度学习的图像识别方法研究",
                    "description": "本文提出了一种新的基于深度学习的图像识别方法。",
                    "creator": ["张三", "李四"],
                    "subject": ["计算机科学", "人工智能"],
                    "date": "2024-01-15",
                    "licenseurl": "https://creativecommons.org/licenses/by/4.0/",
                    "files": [
                        {"name": "test-paper-001.pdf", "format": "PDF"}
                    ]
                }
            ],
            "cursor": "next_cursor"
        }
        mock_http_get.return_value = mock_response
        
        # Mock PDF processing
        mock_process_paper.return_value = {
            "pdf_path": "test.pdf",
            "num_paragraphs": 2,
            "paragraphs": [
                "这是第一段内容。",
                "这是第二段内容。"
            ]
        }
        
        # Mock translation responses
        mock_translate.side_effect = [
            "Research on Image Recognition Methods Based on Deep Learning",  # title
            "This paper proposes a new image recognition method based on deep learning.",  # abstract
            "This is the first paragraph content.",  # body paragraph 1
            "This is the second paragraph content."  # body paragraph 2
        ]
        
        # Change to test directory
        os.chdir(self.test_dir)
        
        # Step 1: Harvest metadata
        harvested, cursor = harvest_chinaxiv_metadata(limit=1, min_year=2024)
        assert len(harvested) == 1
        
        # Add harvested paper to selected.json for translation
        selected_file = os.path.join(self.data_dir, "selected.json")
        with open(selected_file, "w", encoding="utf-8") as f:
            json.dump(harvested, f, ensure_ascii=False, indent=2)
        
        # Step 2: Translate paper
        translation_path = translate_paper(
            "ia-test-paper-001", 
            dry_run=False, 
            with_full_text=True
        )
        assert os.path.exists(translation_path)
        
        # Step 3: Render site
        items = load_translated()
        render_site(items)
        assert os.path.exists(os.path.join(self.site_dir, "index.html"))
        assert os.path.exists(os.path.join(self.site_dir, "items", "ia-test-paper-001.html"))
        
        # Step 4: Build search index
        build_search_index()
        assert os.path.exists(os.path.join(self.site_dir, "search-index.json"))
        
        # Verify final site structure
        assert os.path.exists(os.path.join(self.site_dir, "assets", "style.css"))
        assert os.path.exists(os.path.join(self.site_dir, "assets", "site.js"))
        
        # Verify content in rendered files
        with open(os.path.join(self.site_dir, "index.html"), "r", encoding="utf-8") as f:
            index_content = f.read()
        assert "ia-test-paper-001" in index_content
        assert "Research on Image Recognition Methods Based on Deep Learning" in index_content
        
        with open(os.path.join(self.site_dir, "items", "test-paper-001.html"), "r", encoding="utf-8") as f:
            item_content = f.read()
        assert "Research on Image Recognition Methods Based on Deep Learning" in item_content
        assert "This paper proposes a new image recognition method based on deep learning." in item_content
        
        with open(os.path.join(self.site_dir, "search-index.json"), "r", encoding="utf-8") as f:
            search_index = json.load(f)
        assert "ia-test-paper-001" in search_index
        assert "deep learning" in search_index["ia-test-paper-001"]["abstract"]
