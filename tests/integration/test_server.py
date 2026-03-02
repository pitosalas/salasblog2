"""
Integration tests for Salasblog2 FastAPI server.
These tests require a running server at localhost:8003.

To run these tests:
1. Start server: salasblog2 server --port 8003
2. Run tests: pytest tests/integration/test_server.py -v

Or skip with: pytest tests/ -k "not integration"
"""
import pytest
import requests
from pathlib import Path


@pytest.fixture(scope="module")
def base_url():
    """Base URL for the test server."""
    return "http://localhost:8003"


@pytest.fixture(scope="module")
def check_server_running(base_url):
    """Check if test server is running, skip tests if not."""
    try:
        response = requests.get(f"{base_url}/", timeout=2)
        if response.status_code != 200:
            pytest.skip("Test server not responding correctly at localhost:8003")
    except requests.exceptions.RequestException:
        pytest.skip("Test server not running at localhost:8003. Start with: salasblog2 server --port 8003")


@pytest.mark.integration
class TestServerEndpoints:
    """Integration tests for FastAPI server endpoints."""
    
    def test_home_page(self, base_url, check_server_running):
        """Test home page loads correctly."""
        response = requests.get(f"{base_url}/", timeout=5)
        assert response.status_code == 200
        # Check for common content (flexible to handle different themes)
        content = response.text.upper()
        assert any(keyword in content for keyword in ["SALAS", "BLOG", "HOME"]), "Home page should contain blog-related content"
    
    def test_admin_page(self, base_url, check_server_running):
        """Test admin page shows login form or admin panel."""
        response = requests.get(f"{base_url}/admin", timeout=5)
        assert response.status_code == 200
        content = response.text
        assert ("Admin Login" in content or "Admin Panel" in content), "Admin page should show login or panel"
    
    def test_api_regenerate(self, base_url, check_server_running):
        """Test API regenerate endpoint."""
        response = requests.get(f"{base_url}/api/regenerate", timeout=10)
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data, "API should return status"
        assert data["status"] == "success", "Regeneration should succeed"
    
    def test_static_files(self, base_url, check_server_running):
        """Test static files are served correctly."""
        # Try common static file paths
        static_paths = [
            "/static/css/style.css",
            "/static/js/search.js",
            "/static/css/main.css"  # Alternative path
        ]
        
        found_static = False
        for path in static_paths:
            try:
                response = requests.get(f"{base_url}{path}", timeout=5)
                if response.status_code == 200:
                    found_static = True
                    break
            except:
                continue
        
        assert found_static, f"At least one static file should be accessible from {static_paths}"
    
    def test_individual_page(self, base_url, check_server_running):
        """Test individual pages can be accessed."""
        # Try common page paths
        page_paths = [
            "/about.html",
            "/about/",
            "/contact.html",
            "/pages/"  # Pages listing
        ]
        
        found_page = False
        for path in page_paths:
            try:
                response = requests.get(f"{base_url}{path}", timeout=5)
                if response.status_code == 200:
                    found_page = True
                    break
            except:
                continue
        
        assert found_page, f"At least one page should be accessible from {page_paths}"
    
    def test_rsd_xml(self, base_url, check_server_running):
        """Test RSD XML for blog API discovery."""
        response = requests.get(f"{base_url}/rsd.xml", timeout=5)
        assert response.status_code == 200
        assert "application/rsd+xml" in response.headers.get("content-type", "")
        assert "<rsd" in response.text, "Should contain RSD XML content"
    
    def test_xmlrpc_endpoint(self, base_url, check_server_running):
        """Test XML-RPC endpoint responds to GET."""
        response = requests.get(f"{base_url}/xmlrpc", timeout=5)
        assert response.status_code == 200
        assert "XML-RPC endpoint ready" in response.text


@pytest.mark.integration  
class TestServerAPI:
    """Integration tests for API endpoints that don't require authentication."""
    
    def test_sync_status(self, base_url, check_server_running):
        """Test sync status endpoint."""
        response = requests.get(f"{base_url}/api/sync-status", timeout=5)
        assert response.status_code == 200
        
        data = response.json()
        assert "running" in data, "Sync status should include running state"
        assert "message" in data, "Sync status should include message"
    
    def test_scheduler_status(self, base_url, check_server_running):
        """Test Git scheduler status endpoint."""
        response = requests.get(f"{base_url}/api/scheduler/status", timeout=5)
        assert response.status_code == 200
        
        data = response.json()
        assert "running" in data, "Scheduler status should include running state"
        assert "git_configured" in data, "Scheduler status should include git config state"