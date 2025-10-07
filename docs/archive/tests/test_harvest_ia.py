"""
Tests for Internet Archive harvesting functionality.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.harvest_ia import (
    normalize_ia_record, construct_pdf_url, infer_license,
    harvest_chinaxiv_metadata, ensure_list
)


class TestHarvestIA:
    """Test Internet Archive harvesting functionality."""
    
    def test_ensure_list(self):
        """Test ensuring values are lists."""
        assert ensure_list(None) == []
        assert ensure_list("single") == ["single"]
        assert ensure_list(["item1", "item2"]) == ["item1", "item2"]
        assert ensure_list(123) == ["123"]
    
    def test_construct_pdf_url(self):
        """Test PDF URL construction."""
        identifier = "ChinaXiv-202211.00170V1"
        expected = "https://archive.org/download/ChinaXiv-202211.00170V1/ChinaXiv-202211.00170V1.pdf"
        assert construct_pdf_url(identifier) == expected
    
    def test_infer_license(self):
        """Test license inference."""
        # Default case
        result = infer_license({})
        assert result["derivatives_allowed"] is True
        assert result["raw"] == ""
    
    def test_normalize_ia_record(self):
        """Test normalizing IA record to standard format."""
        ia_item = {
            'identifier': 'ChinaXiv-202211.00170V1',
            'chinaxiv': '202211.00170V1',
            'title': 'Test Paper Title',
            'creator': 'Author Name',
            'description': 'Test abstract',
            'subject': 'cs.AI',
            'date': '2022-11-01'
        }
        
        result = normalize_ia_record(ia_item)
        
        assert result['id'] == 'ia-ChinaXiv-202211.00170V1'
        assert result['oai_identifier'] == '202211.00170V1'
        assert result['title'] == 'Test Paper Title'
        assert result['creators'] == ['Author Name']
        assert result['abstract'] == 'Test abstract'
        assert result['subjects'] == ['cs.AI']
        assert result['date'] == '2022-11-01'
        assert result['source_url'] == 'https://archive.org/details/ChinaXiv-202211.00170V1'
        assert result['pdf_url'] == 'https://archive.org/download/ChinaXiv-202211.00170V1/ChinaXiv-202211.00170V1.pdf'
        assert result['license']['derivatives_allowed'] is True
        assert result['setSpec'] is None
    
    def test_normalize_ia_record_multiple_creators(self):
        """Test normalizing record with multiple creators."""
        ia_item = {
            'identifier': 'ChinaXiv-202211.00170V1',
            'chinaxiv': '202211.00170V1',
            'title': 'Test Paper',
            'creator': ['Author 1', 'Author 2'],
            'description': 'Test abstract',
            'subject': ['cs.AI', 'cs.LG'],
            'date': '2022-11-01'
        }
        
        result = normalize_ia_record(ia_item)
        
        assert result['creators'] == ['Author 1', 'Author 2']
        assert result['subjects'] == ['cs.AI', 'cs.LG']
    
    def test_normalize_ia_record_missing_fields(self):
        """Test normalizing record with missing fields."""
        ia_item = {
            'identifier': 'ChinaXiv-202211.00170V1',
            'chinaxiv': '202211.00170V1'
        }
        
        result = normalize_ia_record(ia_item)
        
        assert result['id'] == 'ia-ChinaXiv-202211.00170V1'
        assert result['oai_identifier'] == '202211.00170V1'
        assert result['title'] == ''
        assert result['creators'] == []
        assert result['abstract'] == ''
        assert result['subjects'] == []
        assert result['date'] == ''
    
    @patch('src.harvest_ia.http_get')
    def test_harvest_chinaxiv_metadata_success(self, mock_http_get):
        """Test successful metadata harvesting."""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            'items': [
                {
                    'identifier': 'ChinaXiv-202211.00170V1',
                    'chinaxiv': '202211.00170V1',
                    'title': 'Test Paper',
                    'creator': 'Author',
                    'description': 'Test abstract',
                    'subject': 'cs.AI',
                    'date': '2022-11-01'
                }
            ],
            'cursor': 'next_cursor_token'
        }
        mock_http_get.return_value = mock_response
        
        records, next_cursor = harvest_chinaxiv_metadata(limit=100)
        
        assert len(records) == 1
        assert records[0]['id'] == 'ia-ChinaXiv-202211.00170V1'
        assert records[0]['title'] == 'Test Paper'
        assert next_cursor == 'next_cursor_token'
        
        # Verify API call
        mock_http_get.assert_called_once()
        call_args = mock_http_get.call_args
        assert 'fields' in call_args[1]['params']
        assert 'q' in call_args[1]['params']
        assert call_args[1]['params']['q'] == 'collection:chinaxivmirror'
    
    @patch('src.harvest_ia.http_get')
    def test_harvest_chinaxiv_metadata_with_cursor(self, mock_http_get):
        """Test harvesting with cursor pagination."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'items': [],
            'cursor': None
        }
        mock_http_get.return_value = mock_response
        
        records, next_cursor = harvest_chinaxiv_metadata(cursor='test_cursor')
        
        assert len(records) == 0
        assert next_cursor is None
        
        # Verify cursor was passed
        call_args = mock_http_get.call_args
        assert call_args[1]['params']['cursor'] == 'test_cursor'
    
    @patch('src.harvest_ia.http_get')
    def test_harvest_chinaxiv_metadata_min_year_filter(self, mock_http_get):
        """Test harvesting with year filter."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'items': [
                {
                    'identifier': 'ChinaXiv-202011.00170V1',
                    'chinaxiv': '202011.00170V1',
                    'title': 'Old Paper',
                    'creator': 'Author',
                    'description': 'Test abstract',
                    'subject': 'cs.AI',
                    'date': '2020-11-01'
                },
                {
                    'identifier': 'ChinaXiv-202211.00170V1',
                    'chinaxiv': '202211.00170V1',
                    'title': 'New Paper',
                    'creator': 'Author',
                    'description': 'Test abstract',
                    'subject': 'cs.AI',
                    'date': '2022-11-01'
                }
            ],
            'cursor': None
        }
        mock_http_get.return_value = mock_response
        
        records, next_cursor = harvest_chinaxiv_metadata(min_year=2021)
        
        # Should only include papers from 2021+
        assert len(records) == 1
        assert records[0]['title'] == 'New Paper'
        assert records[0]['date'] == '2022-11-01'
    
    @patch('src.harvest_ia.http_get')
    def test_harvest_chinaxiv_metadata_limit(self, mock_http_get):
        """Test harvesting with limit."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'items': [
                {
                    'identifier': f'ChinaXiv-202211.00{i:03d}V1',
                    'chinaxiv': f'202211.00{i:03d}V1',
                    'title': f'Paper {i}',
                    'creator': 'Author',
                    'description': 'Test abstract',
                    'subject': 'cs.AI',
                    'date': '2022-11-01'
                }
                for i in range(1, 6)  # 5 papers
            ],
            'cursor': None
        }
        mock_http_get.return_value = mock_response
        
        records, next_cursor = harvest_chinaxiv_metadata(limit=3)
        
        # Should be limited to 3 records
        assert len(records) == 3
        assert records[0]['title'] == 'Paper 1'
        assert records[1]['title'] == 'Paper 2'
        assert records[2]['title'] == 'Paper 3'
    
    @patch('src.harvest_ia.http_get')
    def test_harvest_chinaxiv_metadata_api_minimum(self, mock_http_get):
        """Test that API minimum limit is enforced."""
        mock_response = Mock()
        mock_response.json.return_value = {'items': [], 'cursor': None}
        mock_http_get.return_value = mock_response
        
        records, next_cursor = harvest_chinaxiv_metadata(limit=50)  # Below IA minimum
        
        # Should use IA minimum of 100
        call_args = mock_http_get.call_args
        assert call_args[1]['params']['count'] == 100
    
    @patch('src.harvest_ia.http_get')
    def test_harvest_chinaxiv_metadata_http_error(self, mock_http_get):
        """Test handling of HTTP errors."""
        from src.utils import HttpError
        mock_http_get.side_effect = HttpError("Connection failed")
        
        with pytest.raises(HttpError):
            harvest_chinaxiv_metadata()
    
    def test_normalize_ia_record_edge_cases(self):
        """Test edge cases in record normalization."""
        # Empty item
        result = normalize_ia_record({})
        assert result['id'] == 'ia-'
        assert result['oai_identifier'] == ''
        
        # None values
        ia_item = {
            'identifier': 'ChinaXiv-202211.00170V1',
            'chinaxiv': '202211.00170V1',
            'title': None,
            'creator': None,
            'description': None,
            'subject': None,
            'date': None
        }
        
        result = normalize_ia_record(ia_item)
        assert result['title'] is None
        assert result['creators'] == []
        assert result['abstract'] is None
        assert result['subjects'] == []
        assert result['date'] is None
