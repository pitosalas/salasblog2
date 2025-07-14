import pytest
import json
import os
import tempfile
from unittest.mock import Mock, patch, mock_open, MagicMock
from datetime import datetime, timezone
from pathlib import Path
import requests

from salasblog2.raindrop import RaindropDownloader


class TestRaindropDownloader:
    """Test suite for RaindropDownloader class."""
    
    @pytest.fixture
    def downloader(self):
        """Create a RaindropDownloader instance for testing."""
        return RaindropDownloader(access_token='test_token')
    
    @pytest.fixture
    def sample_raindrops(self):
        """Sample raindrop data for testing."""
        return [
            {
                "_id": "12345",
                "title": "Test Article 1",
                "link": "https://example.com/article1",
                "excerpt": "This is a test article",
                "created": "2023-01-01T12:00:00Z",
                "lastUpdate": "2023-01-01T12:00:00Z",
                "collection": {"title": "Test Collection"},
                "tags": ["test", "article"]
            },
            {
                "_id": "67890",
                "title": "Test Article 2",
                "link": "https://example.com/article2",
                "excerpt": "Another test article",
                "created": "2023-01-02T12:00:00Z",
                "lastUpdate": "2023-01-02T12:00:00Z",
                "collection": {"title": "Test Collection"},
                "tags": ["test"]
            }
        ]
    
    def test_init(self):
        """Test RaindropDownloader initialization."""
        downloader = RaindropDownloader(access_token='test_token')
        assert downloader.access_token == 'test_token'
        assert downloader.base_url == "https://api.raindrop.io/rest/v1"
        assert downloader.drops_dir == Path("/data/content/raindrops")
        assert downloader.cache_file == Path("/data/content/.rd_cache.json")
    
    def test_load_cache_no_env_no_file(self, downloader):
        """Test loading cache when no environment variable or file exists."""
        with patch.dict(os.environ, {}, clear=True), \
             patch('pathlib.Path.exists', return_value=False):
            cache = downloader.load_cache()
            assert cache == {"last_sync_timestamp": None, "downloaded": set()}
    
    def test_load_cache_from_env(self, downloader):
        """Test loading cache from environment variable."""
        with patch.dict(os.environ, {"RAINDROP_LAST_SYNC": "2023-01-01T12:00:00Z"}):
            cache = downloader.load_cache()
            assert cache["last_sync_timestamp"] == "2023-01-01T12:00:00Z"
            assert cache["downloaded"] == set()
    
    def test_load_cache_from_file(self, downloader):
        """Test loading cache from file."""
        cache_data = {"last_sync_timestamp": "2023-01-01T12:00:00Z", "downloaded": ["123", "456"]}
        with patch.dict(os.environ, {}, clear=True), \
             patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=json.dumps(cache_data))):
            cache = downloader.load_cache()
            assert cache["last_sync_timestamp"] == "2023-01-01T12:00:00Z"
            # The load_cache method returns the data as-is when last_sync_timestamp is present
            assert cache["downloaded"] == ["123", "456"]
    
    def test_save_cache(self, downloader):
        """Test saving cache to file."""
        cache_data = {"last_sync_timestamp": "2023-01-01T12:00:00Z", "downloaded": {"123", "456"}}
        
        with patch('builtins.open', mock_open()) as mock_file:
            downloader.save_cache(cache_data)
            mock_file.assert_called_once()
            # Check that the file was written
            handle = mock_file()
            handle.write.assert_called()
    
    @patch('requests.get')
    def test_fetch_page_success(self, mock_get, downloader):
        """Test successful API page fetch."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"items": [{"_id": "123", "title": "Test"}]}
        mock_get.return_value = mock_response
        
        result = downloader._fetch_page(page=0, perpage=50)
        
        assert result == [{"_id": "123", "title": "Test"}]
        mock_get.assert_called_once()
    
    @patch('requests.get')
    def test_fetch_page_failure(self, mock_get, downloader):
        """Test API page fetch failure."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_get.return_value = mock_response
        
        with pytest.raises(Exception, match="Failed to fetch raindrops: 404"):
            downloader._fetch_page(page=0, perpage=50)
    
    def test_fetch_raindrops_first_sync(self, downloader, sample_raindrops):
        """Test fetch_raindrops during first sync."""
        with patch.object(downloader, '_fetch_page') as mock_fetch:
            mock_fetch.side_effect = [
                sample_raindrops,  # First page
                []  # Second page (empty)
            ]
            
            result = downloader.fetch_raindrops(max_items=100)
            
            assert len(result) == 2
            assert result[0]["_id"] == "12345"
            assert result[1]["_id"] == "67890"
    
    def test_determine_sync_mode_first_sync(self, downloader):
        """Test _determine_sync_mode for first sync."""
        cache = {"last_sync_timestamp": None, "downloaded": set()}
        
        with patch.object(downloader, 'fetch_raindrops', return_value=[]) as mock_fetch:
            new_drops, downloaded_ids = downloader._determine_sync_mode(
                reset=False, count=100, cache=cache
            )
            
            mock_fetch.assert_called_once()
            assert downloaded_ids == set()
    
    def test_determine_sync_mode_incremental_sync(self, downloader):
        """Test _determine_sync_mode for incremental sync."""
        cache = {
            "last_sync_timestamp": "2023-01-01T12:00:00Z",
            "downloaded": {"123", "456"}
        }
        
        with patch.object(downloader, 'fetch_raindrops', return_value=[]) as mock_fetch:
            new_drops, downloaded_ids = downloader._determine_sync_mode(
                reset=False, count=100, cache=cache
            )
            
            mock_fetch.assert_called_once_with(
                max_items=100, since_timestamp="2023-01-01T12:00:00Z"
            )
            assert downloaded_ids == {"123", "456"}
    
    def test_write_raindrops_to_files(self, downloader, sample_raindrops):
        """Test _write_raindrops_to_files method."""
        with patch('salasblog2.raindrop.generate_raindrop_filename') as mock_filename, \
             patch('salasblog2.raindrop.format_raindrop_as_markdown') as mock_format, \
             patch('builtins.open', mock_open()) as mock_file:
            
            mock_filename.side_effect = ["file1.md", "file2.md"]
            mock_format.return_value = "# Test Content"
            
            result = downloader._write_raindrops_to_files(sample_raindrops)
            
            assert result == ["file1.md", "file2.md"]
            assert mock_file.call_count == 2
    
    def test_update_cache_with_new_drops(self, downloader):
        """Test _update_cache with new raindrops."""
        cache = {"last_sync_timestamp": None, "downloaded": set()}
        new_drops = [
            {"_id": "123", "created": "2023-01-01T12:00:00Z"},
            {"_id": "456", "created": "2023-01-02T12:00:00Z"}
        ]
        downloaded_ids = {"123", "456"}
        
        with patch.object(downloader, 'save_cache') as mock_save:
            downloader._update_cache(cache, new_drops, downloaded_ids, reset=False)
            
            assert cache["last_sync_timestamp"] == "2023-01-02T12:00:00Z"
            assert cache["downloaded"] == {"123", "456"}
            mock_save.assert_called_once()
    
    def test_download_raindrops_integration(self, downloader, sample_raindrops):
        """Test full download_raindrops integration."""
        with patch.object(downloader, 'authenticate'), \
             patch.object(downloader, 'load_cache') as mock_load, \
             patch.object(downloader, '_determine_sync_mode') as mock_sync, \
             patch.object(downloader, '_write_raindrops_to_files') as mock_write, \
             patch.object(downloader, '_update_cache') as mock_update, \
             patch('pathlib.Path.mkdir'):
            
            mock_load.return_value = {"last_sync_timestamp": None, "downloaded": set()}
            mock_sync.return_value = (sample_raindrops, set())
            mock_write.return_value = ["file1.md", "file2.md"]
            
            result = downloader.download_raindrops(count=100)
            
            assert result == ["file1.md", "file2.md"]
            mock_write.assert_called_once_with(sample_raindrops)
            mock_update.assert_called_once()


class TestDuplicateDetection:
    """Test suite specifically for duplicate detection logic."""
    
    @pytest.fixture
    def downloader(self):
        """Create a RaindropDownloader instance for testing."""
        return RaindropDownloader(access_token='test_token')
    
    def test_duplicate_detection_in_incremental_sync(self, downloader):
        """Test that incremental sync properly filters out duplicates."""
        cache = {
            "last_sync_timestamp": "2023-01-01T00:00:00Z",
            "downloaded": {"123", "456"}
        }
        
        # Mock API response with mix of new and existing items
        api_response = [
            {"_id": "123", "title": "Already Downloaded"},  # Duplicate
            {"_id": "789", "title": "New Item 1"},           # New
            {"_id": "456", "title": "Also Downloaded"},     # Duplicate
            {"_id": "101", "title": "New Item 2"}           # New
        ]
        
        with patch.object(downloader, 'fetch_raindrops', return_value=api_response):
            new_drops, downloaded_ids = downloader._determine_sync_mode(
                reset=False, count=100, cache=cache
            )
            
            # Should only return new items
            assert len(new_drops) == 2
            new_ids = {item["_id"] for item in new_drops}
            assert new_ids == {"789", "101"}
    
    def test_duplicate_detection_preserves_order(self, downloader):
        """Test that duplicate filtering preserves order of remaining items."""
        cache = {
            "last_sync_timestamp": "2023-01-01T00:00:00Z",
            "downloaded": {"222"}
        }
        
        api_response = [
            {"_id": "111", "title": "First New"},
            {"_id": "222", "title": "Duplicate"},      # Should be filtered
            {"_id": "333", "title": "Second New"},
            {"_id": "444", "title": "Third New"}
        ]
        
        with patch.object(downloader, 'fetch_raindrops', return_value=api_response):
            new_drops, _ = downloader._determine_sync_mode(
                reset=False, count=100, cache=cache
            )
            
            # Check that order is preserved
            assert new_drops[0]["_id"] == "111"
            assert new_drops[1]["_id"] == "333"
            assert new_drops[2]["_id"] == "444"
    
    def test_string_id_comparison(self, downloader):
        """Test that ID comparison works correctly with string conversion."""
        cache = {
            "last_sync_timestamp": "2023-01-01T00:00:00Z",
            "downloaded": {"12345"}  # String ID in cache
        }
        
        api_response = [
            {"_id": 12345, "title": "Numeric ID"},    # Numeric ID from API
            {"_id": "67890", "title": "String ID"}    # String ID from API
        ]
        
        with patch.object(downloader, 'fetch_raindrops', return_value=api_response):
            new_drops, _ = downloader._determine_sync_mode(
                reset=False, count=100, cache=cache
            )
            
            # Should recognize numeric 12345 as duplicate of string "12345"
            assert len(new_drops) == 1
            assert new_drops[0]["_id"] == "67890"


class TestCacheManagement:
    """Test suite for cache management functionality."""
    
    @pytest.fixture
    def downloader(self):
        """Create a RaindropDownloader instance for testing."""
        return RaindropDownloader(access_token='test_token')
    
    def test_cache_conversion_from_old_format(self, downloader):
        """Test conversion of old cache format to new format."""
        old_cache = {"downloaded": {"123": "file1.md", "456": "file2.md"}}
        
        with patch.dict(os.environ, {}, clear=True), \
             patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=json.dumps(old_cache))):
            
            cache = downloader.load_cache()
            
            assert cache["last_sync_timestamp"] is None
            assert cache["downloaded"] == {"123", "456"}
    
    def test_cache_save_converts_set_to_list(self, downloader):
        """Test that cache saving converts sets to lists for JSON serialization."""
        cache = {"last_sync_timestamp": "2023-01-01T12:00:00Z", "downloaded": {"123", "456"}}
        
        with patch('builtins.open', mock_open()) as mock_file, \
             patch('json.dump') as mock_json_dump:
            
            downloader.save_cache(cache)
            
            # Verify JSON dump was called with list instead of set
            saved_data = mock_json_dump.call_args[0][0]
            assert isinstance(saved_data["downloaded"], list)
            assert set(saved_data["downloaded"]) == {"123", "456"}
    
    def test_cache_loading_malformed_json(self, downloader):
        """Test cache loading with malformed JSON file."""
        with patch.dict(os.environ, {}, clear=True), \
             patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data="invalid json")):
            
            # Should raise JSONDecodeError since the code doesn't handle it
            with pytest.raises(json.JSONDecodeError):
                downloader.load_cache()


class TestErrorHandling:
    """Test suite for error handling in refactored methods."""
    
    @pytest.fixture
    def downloader(self):
        """Create a RaindropDownloader instance for testing."""
        return RaindropDownloader(access_token='test_token')
    
    @patch('requests.get')
    def test_fetch_page_network_timeout(self, mock_get, downloader):
        """Test fetch_page with network timeout."""
        mock_get.side_effect = requests.Timeout("Request timed out")
        
        with pytest.raises(requests.Timeout):
            downloader._fetch_page(page=0, perpage=50)
    
    @patch('requests.get')
    def test_fetch_page_connection_error(self, mock_get, downloader):
        """Test fetch_page with connection error."""
        mock_get.side_effect = requests.ConnectionError("Connection failed")
        
        with pytest.raises(requests.ConnectionError):
            downloader._fetch_page(page=0, perpage=50)
    
    def test_authentication_missing_token(self):
        """Test authentication with missing token."""
        downloader = RaindropDownloader(access_token=None)
        
        with pytest.raises(Exception, match="RAINDROP_TOKEN environment variable not set"):
            downloader.authenticate()
    
    @patch('requests.get')
    def test_authentication_failure(self, mock_get, downloader):
        """Test authentication failure."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response
        
        with pytest.raises(Exception, match="Authentication failed: 401"):
            downloader.authenticate()
    
    def test_download_raindrops_exception_handling(self, downloader):
        """Test that download_raindrops handles exceptions gracefully."""
        with patch.object(downloader, 'authenticate', side_effect=Exception("Auth failed")):
            result = downloader.download_raindrops()
            
            # Should return empty list on exception
            assert result == []
    
    def test_fetch_raindrops_invalid_timestamp(self, downloader):
        """Test fetch_raindrops with invalid timestamp format."""
        with patch.object(downloader, '_fetch_page') as mock_fetch:
            mock_fetch.return_value = []
            
            # Should handle invalid timestamp gracefully
            result = downloader.fetch_raindrops(since_timestamp="invalid-timestamp")
            assert result == []
    
    def test_update_cache_with_no_drops(self, downloader):
        """Test _update_cache when no new drops are provided."""
        cache = {"last_sync_timestamp": None, "downloaded": set()}
        
        with patch.object(downloader, 'save_cache') as mock_save:
            downloader._update_cache(cache, [], set(), reset=False)
            
            # Should set a timestamp even with no drops
            assert cache["last_sync_timestamp"] is not None
            mock_save.assert_called_once()
    
    def test_reset_data_with_nonexistent_directories(self, downloader):
        """Test reset_data when directories don't exist."""
        with patch('pathlib.Path.exists', return_value=False):
            
            # Should not raise exception
            downloader.reset_data()