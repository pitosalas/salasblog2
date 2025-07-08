"""
Test static file serving logic in server.py.

This test suite focuses on the problematic static file serving implementation
identified in the server.py review. Tests both the custom endpoints and the
catch-all route behavior.

Run with: uv run pytest tests/test_static_file_serving.py -v
"""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import HTTPException

# Import the server module and specific functions
from salasblog2.server import app, config


class TestStaticFileServing:
    """Test the custom static file serving endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create a test client for FastAPI app."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_output_dir(self):
        """Create a temporary output directory with test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create directory structure
            static_dir = temp_path / "static"
            static_dir.mkdir()
            blog_dir = temp_path / "blog"
            blog_dir.mkdir()
            pages_dir = temp_path / "pages"
            pages_dir.mkdir()
            
            # Create test files
            (static_dir / "css").mkdir()
            (static_dir / "js").mkdir()
            (static_dir / "css" / "style.css").write_text("body { color: blue; }")
            (static_dir / "js" / "script.js").write_text("console.log('test');")
            (static_dir / "favicon.ico").write_bytes(b"fake_favicon_data")
            
            (blog_dir / "test-post.html").write_text("<html><body><h1>Test Post</h1></body></html>")
            (blog_dir / "index.html").write_text("<html><body><h1>Blog Index</h1></body></html>")
            
            (pages_dir / "about.html").write_text("<html><body><h1>About Page</h1></body></html>")
            (pages_dir / "index.html").write_text("<html><body><h1>Pages Index</h1></body></html>")
            
            # Mock the config
            with patch.dict(config, {"output_dir": temp_path}):
                yield temp_path
    
    def test_serve_static_css_file(self, client, mock_output_dir):
        """Test serving CSS files via custom static endpoint."""
        response = client.get("/static/css/style.css")
        
        assert response.status_code == 200
        assert "text/css" in response.headers["content-type"]
        assert response.text == "body { color: blue; }"
    
    def test_serve_static_js_file(self, client, mock_output_dir):
        """Test serving JavaScript files via custom static endpoint."""
        response = client.get("/static/js/script.js")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/javascript"
        assert response.text == "console.log('test');"
    
    def test_serve_static_binary_file(self, client, mock_output_dir):
        """Test serving binary files via custom static endpoint."""
        response = client.get("/static/favicon.ico")
        
        assert response.status_code == 200
        assert response.content == b"fake_favicon_data"
    
    def test_serve_static_file_not_found(self, client, mock_output_dir):
        """Test static file not found returns 404."""
        response = client.get("/static/nonexistent.css")
        
        assert response.status_code == 404
    
    def test_serve_static_file_no_config(self, client):
        """Test static file serving with no output directory configured."""
        with patch.dict(config, {"output_dir": None}):
            response = client.get("/static/css/style.css")
            
            assert response.status_code == 404
    
    def test_serve_blog_file(self, client, mock_output_dir):
        """Test serving blog files via custom blog endpoint."""
        response = client.get("/blog/test-post.html")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/html; charset=utf-8"
        assert "<h1>Test Post</h1>" in response.text
    
    def test_serve_blog_directory_index(self, client, mock_output_dir):
        """Test serving blog directory index.html."""
        response = client.get("/blog/")
        
        assert response.status_code == 200
        assert "<h1>Blog Index</h1>" in response.text
    
    def test_serve_blog_file_not_found(self, client, mock_output_dir):
        """Test blog file not found returns 404."""
        response = client.get("/blog/nonexistent.html")
        
        assert response.status_code == 404
    
    def test_serve_pages_file(self, client, mock_output_dir):
        """Test serving pages files via custom pages endpoint."""
        response = client.get("/pages/about.html")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/html; charset=utf-8"
        assert "<h1>About Page</h1>" in response.text
    
    def test_serve_pages_directory_index(self, client, mock_output_dir):
        """Test serving pages directory index.html."""
        response = client.get("/pages/")
        
        assert response.status_code == 200
        assert "<h1>Pages Index</h1>" in response.text
    
    def test_serve_pages_file_not_found(self, client, mock_output_dir):
        """Test pages file not found returns 404."""
        response = client.get("/pages/nonexistent.html")
        
        assert response.status_code == 404


class TestCatchAllRoute:
    """Test the catch-all route behavior and conflicts."""
    
    @pytest.fixture
    def client(self):
        """Create a test client for FastAPI app."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_output_dir(self):
        """Create a temporary output directory with root files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create root-level files
            (temp_path / "index.html").write_text("<html><body><h1>Home</h1></body></html>")
            (temp_path / "robots.txt").write_text("User-agent: *\nDisallow:")
            (temp_path / "sitemap.xml").write_text("<?xml version='1.0'?><urlset></urlset>")
            
            # Create files that should NOT be served by catch-all
            (temp_path / "blog.html").write_text("<html><body>Blog page</body></html>")
            (temp_path / "pages.html").write_text("<html><body>Pages page</body></html>")
            (temp_path / "static.html").write_text("<html><body>Static page</body></html>")
            
            with patch.dict(config, {"output_dir": temp_path}):
                yield temp_path
    
    def test_catch_all_serves_root_index(self, client, mock_output_dir):
        """Test catch-all route serves root index.html."""
        response = client.get("/")
        
        assert response.status_code == 200
        assert "<h1>Home</h1>" in response.text
    
    def test_catch_all_serves_robots_txt(self, client, mock_output_dir):
        """Test catch-all route serves robots.txt."""
        response = client.get("/robots.txt")
        
        assert response.status_code == 200
        assert "User-agent: *" in response.text
    
    def test_catch_all_serves_sitemap_xml(self, client, mock_output_dir):
        """Test catch-all route serves sitemap.xml."""
        response = client.get("/sitemap.xml")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/xml"
        assert "<?xml version='1.0'?>" in response.text
    
    def test_catch_all_rejects_blog_path(self, client, mock_output_dir):
        """Test catch-all route rejects blog paths."""
        response = client.get("/blog/something")
        
        assert response.status_code == 404
    
    def test_catch_all_rejects_pages_path(self, client, mock_output_dir):
        """Test catch-all route rejects pages paths."""
        response = client.get("/pages/something")
        
        assert response.status_code == 404
    
    def test_catch_all_rejects_static_path(self, client, mock_output_dir):
        """Test catch-all route rejects static paths."""
        response = client.get("/static/something")
        
        assert response.status_code == 404
    
    def test_catch_all_adds_html_extension(self, client, mock_output_dir):
        """Test catch-all route adds .html extension if needed."""
        # Create a file without extension
        (mock_output_dir / "about.html").write_text("<html><body>About</body></html>")
        
        response = client.get("/about")
        
        assert response.status_code == 200
        assert "<html><body>About</body></html>" in response.text
    
    def test_catch_all_file_not_found(self, client, mock_output_dir):
        """Test catch-all route returns 404 for missing files."""
        response = client.get("/nonexistent")
        
        assert response.status_code == 404


class TestMimeTypeDetection:
    """Test MIME type detection in custom file serving."""
    
    @pytest.fixture
    def client(self):
        """Create a test client for FastAPI app."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_output_dir(self):
        """Create a temporary output directory with various file types."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            static_dir = temp_path / "static"
            static_dir.mkdir()
            
            # Create files of various types
            (static_dir / "style.css").write_text("body { color: red; }")
            (static_dir / "script.js").write_text("alert('test');")
            (static_dir / "page.html").write_text("<html><body>Test</body></html>")
            (static_dir / "image.png").write_bytes(b"fake_png_data")
            (static_dir / "document.pdf").write_bytes(b"fake_pdf_data")
            (static_dir / "unknown.xyz").write_text("unknown file type")
            
            with patch.dict(config, {"output_dir": temp_path}):
                yield temp_path
    
    def test_css_mime_type(self, client, mock_output_dir):
        """Test CSS files get correct MIME type."""
        response = client.get("/static/style.css")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/css"
    
    def test_js_mime_type(self, client, mock_output_dir):
        """Test JavaScript files get correct MIME type."""
        response = client.get("/static/script.js")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/javascript"
    
    def test_html_mime_type(self, client, mock_output_dir):
        """Test HTML files get correct MIME type."""
        response = client.get("/static/page.html")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/html"
    
    def test_png_mime_type(self, client, mock_output_dir):
        """Test PNG files get correct MIME type."""
        response = client.get("/static/image.png")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
    
    def test_pdf_mime_type(self, client, mock_output_dir):
        """Test PDF files get correct MIME type."""
        response = client.get("/static/document.pdf")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
    
    def test_unknown_mime_type(self, client, mock_output_dir):
        """Test unknown file types get default MIME type."""
        response = client.get("/static/unknown.xyz")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/octet-stream"


class TestStaticFileServingProblems:
    """Test the specific problems identified in server.py review."""
    
    @pytest.fixture
    def client(self):
        """Create a test client for FastAPI app."""
        return TestClient(app)
    
    def test_debug_logging_in_static_endpoint(self, client):
        """Test that debug logging is present in static endpoint (problem identified)."""
        with patch('salasblog2.server.logging.getLogger') as mock_logger:
            mock_logger_instance = Mock()
            mock_logger.return_value = mock_logger_instance
            
            # This should trigger the debug logging
            response = client.get("/static/nonexistent.css")
            
            # Verify the problematic debug logging was called
            mock_logger_instance.error.assert_called()
            error_calls = mock_logger_instance.error.call_args_list
            assert any("STATIC FILE REQUEST" in str(call) for call in error_calls)
    
    def test_config_not_set_error_handling(self, client):
        """Test behavior when config is not properly set."""
        with patch.dict(config, {"output_dir": None}):
            response = client.get("/static/style.css")
            
            assert response.status_code == 404
    
    def test_catch_all_route_logs_error(self, client):
        """Test that catch-all route logs error when hit (problem identified)."""
        with patch('salasblog2.server.logging.getLogger') as mock_logger:
            mock_logger_instance = Mock()
            mock_logger.return_value = mock_logger_instance
            
            # This should trigger the catch-all route error logging
            response = client.get("/some/nested/path")
            
            # Verify the problematic error logging was called
            mock_logger_instance.error.assert_called()
            error_calls = mock_logger_instance.error.call_args_list
            assert any("CATCH-ALL ROUTE HIT" in str(call) for call in error_calls)
    
    def test_route_precedence_problem(self, client):
        """Test that route precedence works correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create conflicting files
            static_dir = temp_path / "static"
            static_dir.mkdir()
            (static_dir / "test.css").write_text("static file")
            (temp_path / "static.html").write_text("catch-all file")
            
            with patch.dict(config, {"output_dir": temp_path}):
                # Static route should take precedence
                response = client.get("/static/test.css")
                assert response.status_code == 200
                assert response.text == "static file"
                
                # But catch-all should reject static paths
                response = client.get("/static/nonexistent.css")
                assert response.status_code == 404
    
    def test_mount_static_files_not_called(self, client):
        """Test that mount_static_files is not being used (problem identified)."""
        # This test verifies the problem exists - the mount_static_files function
        # is defined but not used, forcing reliance on custom endpoints
        from salasblog2.server import mount_static_files
        
        # Function exists but is not called in the app lifecycle
        assert callable(mount_static_files)
        
        # Check that the app doesn't have StaticFiles mounts
        static_mounts = [route for route in app.router.routes 
                        if hasattr(route, 'app') and 'static' in str(route.path)]
        
        # Should be empty because mount_static_files is not called
        assert len(static_mounts) == 0


class TestPerformanceAndSecurity:
    """Test performance and security aspects of static file serving."""
    
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
        # Try various path injection attempts
        malicious_paths = [
            "/static/..%2F..%2F..%2Fetc%2Fpasswd",  # URL encoded
            "/static/....//....//etc/passwd",        # Multiple dots
            "/static/\x00/etc/passwd",               # Null byte
        ]
        
        for path in malicious_paths:
            response = client.get(path)
            assert response.status_code == 404
    
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])