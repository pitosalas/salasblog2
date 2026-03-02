"""
Test MIME type handling for CSS and JavaScript files.

This test verifies that the custom static file serving endpoints correctly
handle MIME types for CSS and JS files, addressing the original issue where
FastAPI's StaticFiles returned inconsistent MIME types between HEAD and GET.

Run with: uv run pytest tests/test_mime_types.py -v
"""
import pytest
import requests
import tempfile
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient

from salasblog2.server import app, config


class TestMimeTypesLocal:
    """Test MIME types against test instance of the server."""
    
    @pytest.fixture
    def client(self):
        """Create a test client for FastAPI app."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_output_dir(self):
        """Create a temporary output directory with CSS and JS files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create directory structure
            static_dir = temp_path / "static"
            static_dir.mkdir()
            css_dir = static_dir / "css"
            css_dir.mkdir()
            js_dir = static_dir / "js"
            js_dir.mkdir()
            
            # Create valid CSS file
            css_content = """
body {
    color: #333;
    font-family: Arial, sans-serif;
}
.header {
    background-color: #f5f5f5;
    padding: 20px;
}
"""
            (css_dir / "style.css").write_text(css_content)
            
            # Create valid JavaScript file
            js_content = """
function hello() {
    console.log('Hello, World!');
}

document.addEventListener('DOMContentLoaded', function() {
    hello();
});
"""
            (js_dir / "script.js").write_text(js_content)
            
            # Mock the config
            with patch.dict(config, {"output_dir": temp_path}):
                yield temp_path
    
    def test_css_get_mime_type_and_content(self, client, mock_output_dir):
        """Test CSS file GET returns text/css MIME type and valid CSS content."""
        response = client.get("/static/css/style.css")
        
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/css")
        
        # Verify it's valid CSS content
        css_content = response.text
        assert "body" in css_content
        assert "color: #333" in css_content
        assert "{" in css_content and "}" in css_content
    
    def test_css_head_mime_type(self, client, mock_output_dir):
        """Test CSS file HEAD returns text/css MIME type."""
        response = client.head("/static/css/style.css")
        
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/css")
        # HEAD should not return content
        assert response.text == ""
    
    def test_css_head_get_consistency(self, client, mock_output_dir):
        """Test CSS file HEAD and GET return consistent MIME types."""
        get_response = client.get("/static/css/style.css")
        head_response = client.head("/static/css/style.css")
        
        assert get_response.status_code == 200
        assert head_response.status_code == 200
        assert get_response.headers["content-type"] == head_response.headers["content-type"]
    
    def test_js_get_mime_type_and_content(self, client, mock_output_dir):
        """Test JS file GET returns application/javascript MIME type and valid JS content."""
        response = client.get("/static/js/script.js")
        
        assert response.status_code == 200
        # Accept both application/javascript and text/javascript
        content_type = response.headers["content-type"]
        assert content_type.startswith("application/javascript") or content_type.startswith("text/javascript")
        
        # Verify it's valid JavaScript content
        js_content = response.text
        assert "function hello()" in js_content
        assert "console.log" in js_content
        assert "document.addEventListener" in js_content
    
    def test_js_head_mime_type(self, client, mock_output_dir):
        """Test JS file HEAD returns application/javascript MIME type."""
        response = client.head("/static/js/script.js")
        
        assert response.status_code == 200
        # Accept both application/javascript and text/javascript
        content_type = response.headers["content-type"]
        assert content_type.startswith("application/javascript") or content_type.startswith("text/javascript")
        # HEAD should not return content
        assert response.text == ""
    
    def test_js_head_get_consistency(self, client, mock_output_dir):
        """Test JS file HEAD and GET return consistent MIME types."""
        get_response = client.get("/static/js/script.js")
        head_response = client.head("/static/js/script.js")
        
        assert get_response.status_code == 200
        assert head_response.status_code == 200
        assert get_response.headers["content-type"] == head_response.headers["content-type"]


@pytest.mark.integration
class TestMimeTypesRunningServer:
    """Test MIME types against running web site."""
    
    @pytest.fixture(scope="class")
    def base_url(self):
        """Base URL for the running server."""
        return "https://salasblog2.fly.dev"
    
    @pytest.fixture(scope="class")
    def check_server_running(self, base_url):
        """Check if server is running, skip tests if not."""
        try:
            response = requests.get(f"{base_url}/", timeout=5)
            if response.status_code != 200:
                pytest.skip(f"Server not responding correctly at {base_url}")
        except requests.exceptions.RequestException:
            pytest.skip(f"Server not running at {base_url}")
    
    def test_css_get_mime_type_and_content_live(self, base_url, check_server_running):
        """Test CSS file GET returns text/css MIME type and valid CSS content on live server."""
        # Try common CSS file paths
        css_paths = [
            "/static/css/style.css",
            "/static/css/main.css",
            "/static/style.css"
        ]
        
        css_found = False
        for path in css_paths:
            try:
                response = requests.get(f"{base_url}{path}", timeout=5)
                if response.status_code == 200:
                    css_found = True
                    
                    # Check MIME type
                    assert response.headers["content-type"].startswith("text/css"), \
                        f"CSS file {path} should return text/css MIME type, got: {response.headers['content-type']}"
                    
                    # Check it's valid CSS content
                    css_content = response.text
                    assert len(css_content) > 0, f"CSS file {path} should not be empty"
                    # Basic CSS validation - should contain CSS-like content
                    assert "{" in css_content and "}" in css_content, \
                        f"CSS file {path} should contain valid CSS syntax"
                    
                    break
            except requests.exceptions.RequestException:
                continue
        
        assert css_found, f"No CSS files found at {css_paths}"
    
    def test_css_head_mime_type_live(self, base_url, check_server_running):
        """Test CSS file HEAD returns text/css MIME type on live server."""
        css_paths = [
            "/static/css/style.css",
            "/static/css/main.css",
            "/static/style.css"
        ]
        
        css_found = False
        for path in css_paths:
            try:
                response = requests.head(f"{base_url}{path}", timeout=5)
                if response.status_code == 200:
                    css_found = True
                    
                    # Check MIME type
                    assert response.headers["content-type"].startswith("text/css"), \
                        f"CSS file {path} HEAD should return text/css MIME type, got: {response.headers['content-type']}"
                    
                    # HEAD should not return content
                    assert len(response.text) == 0, f"HEAD request for {path} should not return content"
                    
                    break
            except requests.exceptions.RequestException:
                continue
        
        assert css_found, f"No CSS files found at {css_paths}"
    
    def test_css_head_get_consistency_live(self, base_url, check_server_running):
        """Test CSS file HEAD and GET return consistent MIME types on live server."""
        css_paths = [
            "/static/css/style.css",
            "/static/css/main.css",
            "/static/style.css"
        ]
        
        css_found = False
        for path in css_paths:
            try:
                get_response = requests.get(f"{base_url}{path}", timeout=5)
                head_response = requests.head(f"{base_url}{path}", timeout=5)
                
                if get_response.status_code == 200 and head_response.status_code == 200:
                    css_found = True
                    
                    # Check consistency
                    assert get_response.headers["content-type"] == head_response.headers["content-type"], \
                        f"CSS file {path} GET and HEAD should return same MIME type. GET: {get_response.headers['content-type']}, HEAD: {head_response.headers['content-type']}"
                    
                    break
            except requests.exceptions.RequestException:
                continue
        
        assert css_found, f"No CSS files found at {css_paths}"
    
    def test_js_get_mime_type_and_content_live(self, base_url, check_server_running):
        """Test JS file GET returns application/javascript MIME type and valid JS content on live server."""
        js_paths = [
            "/static/js/script.js",
            "/static/js/main.js",
            "/static/script.js"
        ]
        
        js_found = False
        for path in js_paths:
            try:
                response = requests.get(f"{base_url}{path}", timeout=5)
                if response.status_code == 200:
                    js_found = True
                    
                    # Check MIME type
                    content_type = response.headers["content-type"]
                    assert content_type.startswith("application/javascript") or content_type.startswith("text/javascript"), \
                        f"JS file {path} should return javascript MIME type, got: {content_type}"
                    
                    # Check it's valid JavaScript content
                    js_content = response.text
                    assert len(js_content) > 0, f"JS file {path} should not be empty"
                    # Basic JS validation - should contain JavaScript-like content
                    js_indicators = ["function", "var", "let", "const", "console", "document", "window", "=", ";"]
                    assert any(indicator in js_content for indicator in js_indicators), \
                        f"JS file {path} should contain valid JavaScript syntax"
                    
                    break
            except requests.exceptions.RequestException:
                continue
        
        assert js_found, f"No JavaScript files found at {js_paths}"
    
    def test_js_head_mime_type_live(self, base_url, check_server_running):
        """Test JS file HEAD returns application/javascript MIME type on live server."""
        js_paths = [
            "/static/js/script.js",
            "/static/js/main.js",
            "/static/script.js"
        ]
        
        js_found = False
        for path in js_paths:
            try:
                response = requests.head(f"{base_url}{path}", timeout=5)
                if response.status_code == 200:
                    js_found = True
                    
                    # Check MIME type
                    content_type = response.headers["content-type"]
                    assert content_type.startswith("application/javascript") or content_type.startswith("text/javascript"), \
                        f"JS file {path} HEAD should return javascript MIME type, got: {content_type}"
                    
                    # HEAD should not return content
                    assert len(response.text) == 0, f"HEAD request for {path} should not return content"
                    
                    break
            except requests.exceptions.RequestException:
                continue
        
        assert js_found, f"No JavaScript files found at {js_paths}"
    
    def test_js_head_get_consistency_live(self, base_url, check_server_running):
        """Test JS file HEAD and GET return consistent MIME types on live server."""
        js_paths = [
            "/static/js/script.js",
            "/static/js/main.js",
            "/static/script.js"
        ]
        
        js_found = False
        for path in js_paths:
            try:
                get_response = requests.get(f"{base_url}{path}", timeout=5)
                head_response = requests.head(f"{base_url}{path}", timeout=5)
                
                if get_response.status_code == 200 and head_response.status_code == 200:
                    js_found = True
                    
                    # Check consistency
                    assert get_response.headers["content-type"] == head_response.headers["content-type"], \
                        f"JS file {path} GET and HEAD should return same MIME type. GET: {get_response.headers['content-type']}, HEAD: {head_response.headers['content-type']}"
                    
                    break
            except requests.exceptions.RequestException:
                continue
        
        assert js_found, f"No JavaScript files found at {js_paths}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])