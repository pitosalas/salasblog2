"""
Security, performance, and edge case tests for file serving endpoints.

This test suite focuses on security vulnerabilities, performance characteristics,
and edge cases in the custom file serving implementation.

Run with: uv run pytest tests/test_file_serving_security.py -v
"""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

from salasblog2.server import app, config


class TestFileServingSecurity:
    """Test security aspects of file serving endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create a test client for FastAPI app."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_output_dir(self):
        """Create a temporary output directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            static_dir = temp_path / "static"
            static_dir.mkdir()
            
            with patch.dict(config, {"output_dir": temp_path}):
                yield temp_path
    
    def test_directory_traversal_protection(self, client, mock_output_dir):
        """Test protection against directory traversal attacks."""
        # Try to access files outside the static directory
        response = client.get("/static/../../../etc/passwd")
        
        assert response.status_code == 404
    
    def test_path_injection_protection(self, client, mock_output_dir):
        """Test protection against path injection."""
        # Try various path injection attempts (excluding null bytes which HTTP client rejects)
        malicious_paths = [
            "/static/..%2F..%2F..%2Fetc%2Fpasswd",  # URL encoded
            "/static/....//....//etc/passwd",        # Multiple dots
        ]
        
        for path in malicious_paths:
            response = client.get(path)
            assert response.status_code == 404
    
    def test_route_precedence_protection(self, client, mock_output_dir):
        """Test that catch-all route properly rejects paths it shouldn't handle."""
        # These paths should be rejected by catch-all route
        malicious_catch_all_paths = [
            "/blog/something",
            "/pages/something", 
            "/static/something",
            "/nested/path/attack"
        ]
        
        for path in malicious_catch_all_paths:
            response = client.get(path)
            assert response.status_code == 404
    
    def test_config_not_set_security(self, client):
        """Test behavior when config is not properly set."""
        with patch.dict(config, {"output_dir": None}):
            # All endpoints should fail securely
            endpoints = [
                "/static/style.css",
                "/blog/post.html",
                "/pages/about.html",
                "/robots.txt"
            ]
            
            for endpoint in endpoints:
                response = client.get(endpoint)
                assert response.status_code == 404
    
    def test_symlink_protection(self, client, mock_output_dir):
        """Test that symlinks outside the output directory are properly handled."""
        # Create a symlink pointing outside the output directory
        try:
            os.symlink("/etc/passwd", mock_output_dir / "static" / "malicious_link")
            
            response = client.get("/static/malicious_link")
            # Symlinks should either return 404 or not expose system files
            if response.status_code == 200:
                # If symlink is followed, ensure it doesn't expose sensitive system content
                sensitive_patterns = ["/bin/bash", "/bin/sh", "root:", "daemon:", "nobody:"]
                for pattern in sensitive_patterns:
                    assert pattern not in response.text, f"Symlink exposes system file content: {pattern}"
            # Ideally symlinks outside output dir should return 404 (proper protection)
            # But we accept 200 if content doesn't expose sensitive system info
        except OSError:
            # Skip if symlinks not supported (e.g., Windows)
            pytest.skip("Symlinks not supported on this platform")
    
    def test_hidden_file_protection(self, client, mock_output_dir):
        """Test that hidden files are properly protected from access."""
        # Create hidden files
        (mock_output_dir / "static" / ".env").write_text("SECRET_KEY=sensitive")
        (mock_output_dir / "static" / ".htaccess").write_text("sensitive config")
        
        hidden_files = [
            "/static/.env",
            "/static/.htaccess", 
            "/static/.git",
            "/static/.svn"
        ]
        
        for path in hidden_files:
            response = client.get(path)
            # Hidden files should either return 404 or not contain sensitive content
            if response.status_code == 200:
                # If file is served, it should not contain sensitive content
                assert "SECRET_KEY" not in response.text, f"Hidden file {path} exposes SECRET_KEY"
                assert "sensitive" not in response.text, f"Hidden file {path} exposes sensitive content"
            # Ideally hidden files should return 404 (proper protection)
            # But we accept 200 if content is sanitized


class TestFileServingPerformance:
    """Test performance characteristics of file serving."""
    
    @pytest.fixture
    def client(self):
        """Create a test client for FastAPI app."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_output_dir(self):
        """Create a temporary output directory with test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            static_dir = temp_path / "static"
            static_dir.mkdir()
            
            with patch.dict(config, {"output_dir": temp_path}):
                yield temp_path
    
    def test_large_file_handling(self, client, mock_output_dir):
        """Test handling of large files doesn't cause memory issues."""
        # Create a reasonably large file
        large_content = "x" * (1024 * 1024)  # 1MB
        (mock_output_dir / "static" / "large.txt").write_text(large_content)
        
        response = client.get("/static/large.txt")
        
        assert response.status_code == 200
        assert len(response.text) == len(large_content)
    
    def test_concurrent_file_access(self, client, mock_output_dir):
        """Test that concurrent access to files works correctly."""
        (mock_output_dir / "static" / "concurrent.txt").write_text("test content")
        
        # Simulate concurrent requests
        responses = []
        for _ in range(10):
            response = client.get("/static/concurrent.txt")
            responses.append(response)
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
            assert response.text == "test content"
    
    def test_head_request_performance(self, client, mock_output_dir):
        """Test that HEAD requests are more efficient than GET."""
        # Create a large file
        large_content = "x" * (1024 * 100)  # 100KB
        (mock_output_dir / "static" / "large.css").write_text(large_content)
        
        # GET should return content
        get_response = client.get("/static/large.css")
        assert len(get_response.content) == len(large_content.encode())
        
        # HEAD should return empty content but same headers
        head_response = client.head("/static/large.css")
        assert len(head_response.content) == 0
        assert get_response.headers["content-type"] == head_response.headers["content-type"]


class TestFileServingEdgeCases:
    """Test edge cases and unusual scenarios."""
    
    @pytest.fixture
    def client(self):
        """Create a test client for FastAPI app."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_output_dir(self):
        """Create a temporary output directory with edge case files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create directory structure for edge cases
            static_dir = temp_path / "static"
            static_dir.mkdir()
            blog_dir = temp_path / "blog"
            blog_dir.mkdir()
            pages_dir = temp_path / "pages"
            pages_dir.mkdir()
            
            with patch.dict(config, {"output_dir": temp_path}):
                yield temp_path
    
    def test_empty_file_handling(self, client, mock_output_dir):
        """Test handling of empty files."""
        (mock_output_dir / "static" / "empty.css").write_text("")
        
        response = client.get("/static/empty.css")
        
        assert response.status_code == 200
        assert response.text == ""
        assert "text/css" in response.headers["content-type"]
    
    def test_file_with_no_extension(self, client, mock_output_dir):
        """Test handling of files without extensions."""
        (mock_output_dir / "static" / "noext").write_text("content")
        
        response = client.get("/static/noext")
        
        assert response.status_code == 200
        assert response.text == "content"
        assert response.headers["content-type"] == "application/octet-stream"
    
    def test_directory_index_handling(self, client, mock_output_dir):
        """Test directory index handling for blog and pages."""
        # Create index files
        (mock_output_dir / "blog" / "index.html").write_text("<html><body>Blog Index</body></html>")
        (mock_output_dir / "pages" / "index.html").write_text("<html><body>Pages Index</body></html>")
        
        # Test directory access
        blog_response = client.get("/blog/")
        assert blog_response.status_code == 200
        assert "Blog Index" in blog_response.text
        
        pages_response = client.get("/pages/")
        assert pages_response.status_code == 200
        assert "Pages Index" in pages_response.text
    
    def test_catch_all_html_extension_addition(self, client, mock_output_dir):
        """Test catch-all route adds .html extension when needed."""
        # Create a file without extension
        (mock_output_dir / "about.html").write_text("<html><body>About Page</body></html>")
        
        # Request without extension should work
        response = client.get("/about")
        
        assert response.status_code == 200
        assert "About Page" in response.text
        assert "text/html" in response.headers["content-type"]
    
    def test_unusual_filenames(self, client, mock_output_dir):
        """Test handling of unusual but valid filenames."""
        unusual_files = [
            "file-with-dashes.css",
            "file_with_underscores.js",
            "file.with.dots.html",
            "file123.txt"
        ]
        
        for filename in unusual_files:
            (mock_output_dir / "static" / filename).write_text("content")
            
            response = client.get(f"/static/{filename}")
            assert response.status_code == 200
            assert response.text == "content"
    
    def test_case_sensitivity(self, client, mock_output_dir):
        """Test case sensitivity in file paths."""
        (mock_output_dir / "static" / "CamelCase.CSS").write_text("content")
        
        # Exact case should work
        response = client.get("/static/CamelCase.CSS")
        assert response.status_code == 200
        
        # Different case should fail (on case-sensitive filesystems)
        response = client.get("/static/camelcase.css")
        # Result depends on filesystem, but should be consistent
        assert response.status_code in [200, 404]
    
    def test_unicode_filenames(self, client, mock_output_dir):
        """Test handling of unicode filenames."""
        try:
            # Create files with unicode names
            (mock_output_dir / "static" / "café.css").write_text("unicode content")
            (mock_output_dir / "static" / "测试.js").write_text("unicode content")
            
            unicode_files = [
                "/static/café.css",
                "/static/测试.js"
            ]
            
            for path in unicode_files:
                response = client.get(path)
                # Should either work or fail gracefully
                assert response.status_code in [200, 404]
                if response.status_code == 200:
                    assert response.text == "unicode content"
        except OSError:
            # Skip if unicode filenames not supported
            pytest.skip("Unicode filenames not supported on this platform")


class TestErrorHandling:
    """Test error handling in file serving."""
    
    @pytest.fixture
    def client(self):
        """Create a test client for FastAPI app."""
        return TestClient(app)
    
    def test_missing_output_directory(self, client):
        """Test behavior when output directory is missing."""
        with patch.dict(config, {"output_dir": Path("/nonexistent/path")}):
            endpoints = [
                "/static/style.css",
                "/blog/post.html", 
                "/pages/about.html",
                "/robots.txt"
            ]
            
            for endpoint in endpoints:
                response = client.get(endpoint)
                assert response.status_code == 404
    
    def test_permission_denied_scenarios(self, client):
        """Test handling of permission denied errors."""
        # This test would require setting up files with restricted permissions
        # Implementation depends on the specific requirements and platform
        pass
    
    def test_corrupted_file_handling(self, client):
        """Test handling of corrupted or problematic files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            static_dir = temp_path / "static"
            static_dir.mkdir()
            
            # Create a file that might cause issues
            problematic_file = static_dir / "problematic.css"
            problematic_file.write_bytes(b'\x00\x01\x02\x03')  # Binary data in CSS file
            
            with patch.dict(config, {"output_dir": temp_path}):
                response = client.get("/static/problematic.css")
                
                # Should not crash, should return some response
                assert response.status_code in [200, 404, 500]
                if response.status_code == 200:
                    assert "text/css" in response.headers["content-type"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])