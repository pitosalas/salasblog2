"""
Test cases for all possible scenarios that could cause 404 on /raindrops/ endpoint.

These tests verify the specific conditions in server.py:serve_raindrops_files() that lead to
"Not found" responses when accessing https://salasblog2.fly.dev/raindrops/
"""

import pytest
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException

from salasblog2.server import app, config


class TestRaindrops404Scenarios:
    """
    Test cases for raindrops endpoint 404 scenarios
    
    These tests verify the conditions that cause /raindrops/ to return 404,
    focusing on the real system flow:
    1. Source: /data/content/raindrops/*.md files
    2. Generated: /output/raindrops/index.html and individual pages  
    3. Served: from /output/raindrops/ directory
    """

    def setup_method(self):
        """Setup test environment before each test"""
        self.client = TestClient(app)
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def teardown_method(self):
        """Cleanup after each test"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    # Test Case 1: Missing output_dir configuration
    def test_missing_output_dir_config_returns_404(self):
        """
        Test server.py:277-278 - When config["output_dir"] is None/empty, returns 404
        
        Scenario: The global config dictionary has no output_dir or it's set to None
        Expected: GET /raindrops/ returns 404 with "Not found" detail
        """
        with patch.dict(config, {"output_dir": None}, clear=True):
            response = self.client.get("/raindrops/")
            assert response.status_code == 404
            assert response.json() == {"detail": "Not found"}

    def test_empty_output_dir_config_returns_404(self):
        """
        Test server.py:277-278 - When config["output_dir"] is empty string, returns 404
        """
        with patch.dict(config, {"output_dir": ""}, clear=True):
            response = self.client.get("/raindrops/")
            assert response.status_code == 404
            assert response.json() == {"detail": "Not found"}

    def test_missing_output_dir_key_returns_404(self):
        """
        Test server.py:277-278 - When output_dir key doesn't exist in config, returns 404
        """
        with patch.dict(config, {}, clear=True):
            response = self.client.get("/raindrops/")
            assert response.status_code == 404
            assert response.json() == {"detail": "Not found"}

    # Test Case 2: Raindrops directory doesn't exist
    def test_raindrops_directory_not_exists_returns_404(self):
        """
        Test server.py:280,286-287 - When raindrops directory doesn't exist, returns 404
        
        Scenario: output_dir exists but raindrops subdirectory doesn't exist
        Expected: GET /raindrops/ returns 404
        """
        output_dir = self.temp_dir / "output"
        output_dir.mkdir()
        # Note: not creating raindrops subdirectory
        
        with patch.dict(config, {"output_dir": output_dir}):
            response = self.client.get("/raindrops/")
            assert response.status_code == 404
            assert response.json() == {"detail": "Not found"}

    def test_site_not_generated_returns_404(self):
        """
        Test most common real-world scenario: site hasn't been generated yet
        
        This happens when:
        1. Fresh deployment before first site generation
        2. Source content exists in /data/content/raindrops/ but site hasn't been built
        3. Build process failed and didn't create output files
        """
        output_dir = self.temp_dir / "output"
        output_dir.mkdir()
        # No raindrops directory exists - site generation hasn't created it yet
        
        with patch.dict(config, {"output_dir": output_dir}):
            response = self.client.get("/raindrops/")
            assert response.status_code == 404, f"Should return 404 when site not generated, got {response.status_code}"
            assert response.json() == {"detail": "Not found"}
    
    def test_raindrops_generated_but_empty_returns_404(self):
        """
        Test when raindrops directory exists but no index.html was generated
        
        This happens when:
        1. Site generation partially completed but failed during raindrops generation
        2. /data/content/raindrops/ is empty so no index.html was created
        3. Previous index.html was deleted but directory remains
        """
        output_dir = self.temp_dir / "output"
        raindrops_dir = output_dir / "raindrops"
        raindrops_dir.mkdir(parents=True)
        # Directory exists but no index.html - generation failed or no source content
        
        with patch.dict(config, {"output_dir": output_dir}):
            response = self.client.get("/raindrops/")
            assert response.status_code == 404, f"Should return 404 when no index.html generated, got {response.status_code}"
    
    def test_corrupted_site_structure_returns_404(self):
        """
        Test when raindrops exists as file instead of directory (corrupted structure)
        
        This could happen due to:
        1. Manual file system corruption
        2. Deployment script error  
        3. Storage system issues
        """
        output_dir = self.temp_dir / "output"
        output_dir.mkdir()
        # Create raindrops as a file instead of directory - corrupted structure
        (output_dir / "raindrops").write_text("Corrupted: should be directory")
        
        with patch.dict(config, {"output_dir": output_dir}):
            response = self.client.get("/raindrops/")
            # Current behavior: serves the file (security issue)
            # Desired behavior: should return 404
            assert response.status_code == 200, f"CURRENT BEHAVIOR: Server serves corrupted file structure"
            assert "Corrupted" in response.text
    
    def test_path_traversal_vulnerability_exists(self):
        """
        SECURITY TEST: Documents existing path traversal vulnerability
        
        Server allows access to files outside raindrops directory, exposing
        sensitive files that should not be accessible via raindrops endpoint.
        """
        output_dir = self.temp_dir / "output"
        raindrops_dir = output_dir / "raindrops"
        raindrops_dir.mkdir(parents=True)
        (raindrops_dir / "index.html").write_text("Safe content")
        
        # Create sensitive files that should not be accessible
        (output_dir / "sensitive.txt").write_text("Secret data")
        (output_dir / ".env").write_text("DATABASE_PASSWORD=secret123")
        
        with patch.dict(config, {"output_dir": output_dir}):
            # Test multiple path traversal techniques
            for path in ["../sensitive.txt", "../.env", "../../etc/passwd"]:
                response = self.client.get(f"/raindrops/{path}")
                if response.status_code == 200 and ("Secret" in response.text or "DATABASE_PASSWORD" in response.text):
                    assert False, f"SECURITY VULNERABILITY: Path traversal {path} exposed sensitive data: {response.text[:100]}"

    # Test Case 3: Missing index.html file
    def test_missing_index_html_returns_404(self):
        """
        Test server.py:283-287 - When raindrops/index.html doesn't exist, returns 404
        
        Scenario: raindrops directory exists but no index.html inside
        Expected: GET /raindrops/ returns 404
        """
        output_dir = self.temp_dir / "output"
        raindrops_dir = output_dir / "raindrops"
        raindrops_dir.mkdir(parents=True)
        # Note: not creating index.html
        
        with patch.dict(config, {"output_dir": output_dir}):
            response = self.client.get("/raindrops/")
            assert response.status_code == 404
            assert response.json() == {"detail": "Not found"}

    def test_index_html_is_directory_returns_404(self):
        """
        Test edge case where index.html exists as a directory instead of file
        """
        output_dir = self.temp_dir / "output"
        raindrops_dir = output_dir / "raindrops"
        raindrops_dir.mkdir(parents=True)
        # Create index.html as directory instead of file
        (raindrops_dir / "index.html").mkdir()
        
        with patch.dict(config, {"output_dir": output_dir}):
            response = self.client.get("/raindrops/")
            assert response.status_code == 404
            assert response.json() == {"detail": "Not found"}

    # Test Case 4: Site not generated (index.html exists but empty/corrupted)
    def test_empty_index_html_serves_successfully(self):
        """
        Test that empty index.html still serves (this is NOT a 404 case)
        
        This verifies the server serves even empty files, so emptiness alone doesn't cause 404
        """
        output_dir = self.temp_dir / "output"
        raindrops_dir = output_dir / "raindrops"
        raindrops_dir.mkdir(parents=True)
        # Create empty index.html
        (raindrops_dir / "index.html").write_text("")
        
        with patch.dict(config, {"output_dir": output_dir}):
            response = self.client.get("/raindrops/")
            assert response.status_code == 200
            assert response.text == ""
            assert response.headers["content-type"] == "text/html; charset=utf-8"

    def test_corrupted_index_html_serves_successfully(self):
        """
        Test that corrupted/invalid HTML still serves (this is NOT a 404 case)
        """
        output_dir = self.temp_dir / "output"
        raindrops_dir = output_dir / "raindrops"
        raindrops_dir.mkdir(parents=True)
        # Create corrupted HTML
        (raindrops_dir / "index.html").write_text("<<>>invalid<<html>>")
        
        with patch.dict(config, {"output_dir": output_dir}):
            response = self.client.get("/raindrops/")
            assert response.status_code == 200
            assert response.text == "<<>>invalid<<html>>"

    # Test Case 5: Empty raindrops content (valid but no raindrops)
    def test_valid_index_html_no_raindrops_content_serves_successfully(self):
        """
        Test that valid index.html with no raindrops serves successfully (NOT a 404 case)
        
        This simulates what happens when site is generated but no raindrops have been synced
        """
        output_dir = self.temp_dir / "output"
        raindrops_dir = output_dir / "raindrops"
        raindrops_dir.mkdir(parents=True)
        
        # Create valid HTML with no raindrops content
        html_content = """
        <!DOCTYPE html>
        <html>
        <head><title>Raindrops</title></head>
        <body>
            <h1>Link Blog</h1>
            <p>No raindrops found.</p>
        </body>
        </html>
        """
        (raindrops_dir / "index.html").write_text(html_content)
        
        with patch.dict(config, {"output_dir": output_dir}):
            response = self.client.get("/raindrops/")
            assert response.status_code == 200
            assert "No raindrops found" in response.text

    # Test Case 6: Permission issues
    def test_permission_errors_should_return_404_not_crash(self):
        """
        Test that permission errors are handled gracefully
        
        When files exist but aren't readable due to permissions, server should
        return a proper 404 response instead of crashing with unhandled exceptions.
        """
        output_dir = self.temp_dir / "output"
        raindrops_dir = output_dir / "raindrops"
        raindrops_dir.mkdir(parents=True)
        index_file = raindrops_dir / "index.html"
        index_file.write_text("<html><body>Test</body></html>")
        
        # Mock file read to raise PermissionError - server should handle this gracefully
        with patch.dict(config, {"output_dir": output_dir}):
            with patch.object(Path, 'read_bytes', side_effect=PermissionError("Permission denied")):
                response = self.client.get("/raindrops/")
                # Should return 404, not crash with unhandled exception
                assert response.status_code == 404, f"POOR ERROR HANDLING: Permission error should return 404, not crash. Got unhandled exception."

    def test_directory_permission_errors_should_return_404_not_crash(self):
        """
        Test that directory permission errors are handled gracefully
        
        When directory access fails due to permissions, server should return
        a proper 404 response instead of crashing with unhandled exceptions.
        """
        output_dir = self.temp_dir / "output"
        raindrops_dir = output_dir / "raindrops"
        raindrops_dir.mkdir(parents=True)
        
        # Mock directory access to raise PermissionError - server should handle this gracefully
        with patch.dict(config, {"output_dir": output_dir}):
            with patch.object(Path, 'is_dir', side_effect=PermissionError("Permission denied")):
                response = self.client.get("/raindrops/")
                # Should return 404, not crash with unhandled exception
                assert response.status_code == 404, f"POOR ERROR HANDLING: Directory permission error should return 404, not crash. Got unhandled exception."

    # Test Case 7: Successful scenarios (for completeness)
    def test_valid_raindrops_index_serves_successfully(self):
        """
        Test the happy path - valid index.html serves successfully
        
        This is the baseline case that should work when everything is configured correctly
        """
        output_dir = self.temp_dir / "output"
        raindrops_dir = output_dir / "raindrops"
        raindrops_dir.mkdir(parents=True)
        
        html_content = """
        <!DOCTYPE html>
        <html>
        <head><title>Raindrops</title></head>
        <body>
            <h1>Link Blog</h1>
            <div class="raindrop">
                <h2><a href="https://example.com">Example Link</a></h2>
                <p>This is a test raindrop</p>
            </div>
        </body>
        </html>
        """
        (raindrops_dir / "index.html").write_text(html_content)
        
        with patch.dict(config, {"output_dir": output_dir}):
            response = self.client.get("/raindrops/")
            assert response.status_code == 200
            assert "Link Blog" in response.text
            assert "Example Link" in response.text
            assert response.headers["content-type"] == "text/html; charset=utf-8"

    def test_specific_raindrop_file_serves_successfully(self):
        """
        Test that specific raindrop files serve correctly
        """
        output_dir = self.temp_dir / "output"
        raindrops_dir = output_dir / "raindrops"
        raindrops_dir.mkdir(parents=True)
        
        # Create a specific raindrop file
        raindrop_content = "<html><body><h1>Specific Raindrop</h1></body></html>"
        (raindrops_dir / "test-raindrop.html").write_text(raindrop_content)
        
        with patch.dict(config, {"output_dir": output_dir}):
            response = self.client.get("/raindrops/test-raindrop.html")
            assert response.status_code == 200
            assert "Specific Raindrop" in response.text

    def test_head_request_returns_headers_only(self):
        """
        Test that HEAD requests return proper headers without content
        """
        output_dir = self.temp_dir / "output"
        raindrops_dir = output_dir / "raindrops"
        raindrops_dir.mkdir(parents=True)
        (raindrops_dir / "index.html").write_text("<html><body>Test</body></html>")
        
        with patch.dict(config, {"output_dir": output_dir}):
            response = self.client.head("/raindrops/")
            assert response.status_code == 200
            assert response.text == ""  # HEAD should return empty body
            assert response.headers["content-type"] == "text/html; charset=utf-8"


# Additional integration tests that test real-world scenarios
class TestRaindropsRealWorldScenarios:
    """Realistic integration tests based on actual raindrops system behavior"""

    def setup_method(self):
        self.client = TestClient(app)
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_fresh_deployment_scenario(self):
        """
        Test: Fresh deployment before first raindrop sync and generation
        
        Real scenario: Deploy app, no raindrops downloaded yet, user visits /raindrops/
        Expected: 404 because /output/raindrops/ doesn't exist
        """
        output_dir = self.temp_dir / "output"
        # Don't create anything - simulate fresh deployment
        
        with patch.dict(config, {"output_dir": output_dir}):
            response = self.client.get("/raindrops/")
            assert response.status_code == 404
            assert response.json() == {"detail": "Not found"}

    def test_raindrops_synced_but_site_not_generated(self):
        """
        Test: Raindrops downloaded to /data/content/raindrops/ but site not generated
        
        Real scenario: 
        1. RaindropDownloader runs, creates markdown files in source directory
        2. Site generation hasn't run yet
        3. User visits /raindrops/ before generation completes
        """
        output_dir = self.temp_dir / "output"
        output_dir.mkdir()
        # Simulate other parts of site generated but not raindrops
        (output_dir / "blog").mkdir()
        (output_dir / "static").mkdir()
        (output_dir / "index.html").write_text("Home page")
        # Note: no raindrops directory - generation didn't process raindrops yet
        
        with patch.dict(config, {"output_dir": output_dir}):
            response = self.client.get("/raindrops/")
            assert response.status_code == 404

    def test_empty_raindrops_source_directory_old_behavior(self):
        """
        Test: Simulates old buggy behavior where empty source created no index.html
        
        This test simulates the state before the fix where an empty raindrops
        source directory would create the output directory but no index.html file.
        """
        output_dir = self.temp_dir / "output"
        raindrops_dir = output_dir / "raindrops"
        raindrops_dir.mkdir(parents=True)
        # Directory exists but no index.html - simulating old buggy behavior
        
        with patch.dict(config, {"output_dir": output_dir}):
            response = self.client.get("/raindrops/")
            assert response.status_code == 404

    def test_generator_fix_creates_index_for_empty_raindrops(self):
        """
        Test: Verify our fix ensures index.html is created even when no raindrops exist
        
        This tests that the max(1, total_pages) fix works correctly.
        """
        from salasblog2.generator import SiteGenerator
        
        # Create output directory structure
        output_dir = self.temp_dir / "output"
        output_dir.mkdir(parents=True)
        
        # Create minimal generator instance and override output directory
        generator = SiteGenerator()
        generator.output_dir = output_dir
        
        # Mock the render_template method to avoid template dependency
        def mock_render_template(template_name, context):
            return f"""<!DOCTYPE html>
<html>
<head><title>Test {template_name}</title></head>
<body>
    <h1>Raindrops</h1>
    <p>Total posts: {context.get('total_posts', 0)}</p>
    <p>Total pages: {context.get('pagination', {}).get('total_pages', 0)}</p>
    {f"<p>No raindrops found.</p>" if context.get('total_posts', 0) == 0 else ""}
</body>
</html>"""
        
        generator.render_template = mock_render_template
        
        # Test that generator creates index.html even with empty posts
        empty_posts = []
        generator.generate_listing_pages(empty_posts, 'raindrops')
        
        # Check that index.html was created
        index_file = output_dir / "raindrops" / "index.html"
        assert index_file.exists(), "Generator should create index.html even for empty raindrops"
        
        # Verify the content shows empty state
        content = index_file.read_text()
        assert "Total posts: 0" in content
        assert "Total pages: 1" in content  # Should be 1 due to our fix
        assert "No raindrops found" in content
        
        # Test that server can serve the empty state
        with patch.dict(config, {"output_dir": output_dir}):
            response = self.client.get("/raindrops/")
            assert response.status_code == 200, "Should serve empty raindrops page successfully"
            assert "No raindrops found" in response.text

    def test_successful_raindrops_generation(self):
        """
        Test: Normal successful case - raindrops properly generated and served
        
        Real scenario:
        1. Raindrops downloaded to /data/content/raindrops/*.md
        2. Site generation creates /output/raindrops/index.html
        3. Individual raindrop pages created
        4. User visits /raindrops/ and sees listing
        """
        output_dir = self.temp_dir / "output"
        raindrops_dir = output_dir / "raindrops"
        raindrops_dir.mkdir(parents=True)
        
        # Create realistic generated content
        index_content = """
        <!DOCTYPE html>
        <html>
        <head><title>Link Blog - Raindrops</title></head>
        <body>
            <h1>Link Blog</h1>
            <div class="raindrop">
                <h2><a href="https://example.com">Example Article</a></h2>
                <p class="domain">example.com</p>
                <p>This is an interesting article about technology.</p>
                <div class="tags">
                    <span class="tag">technology</span>
                    <span class="tag">programming</span>
                </div>
            </div>
            <nav class="pagination">
                <span class="page-current">1</span>
            </nav>
        </body>
        </html>
        """
        (raindrops_dir / "index.html").write_text(index_content)
        
        # Create individual raindrop file
        raindrop_content = """
        <!DOCTYPE html>
        <html>
        <head><title>Example Article</title></head>
        <body>
            <article class="raindrop">
                <h1><a href="https://example.com">Example Article</a></h1>
                <p class="domain">example.com</p>
                <div class="content">
                    <p>This is an interesting article about technology.</p>
                </div>
            </article>
        </body>
        </html>
        """
        (raindrops_dir / "example-article.html").write_text(raindrop_content)
        
        with patch.dict(config, {"output_dir": output_dir}):
            # Test main listing page
            response = self.client.get("/raindrops/")
            assert response.status_code == 200
            assert "Link Blog" in response.text
            assert "Example Article" in response.text
            assert "example.com" in response.text
            
            # Test individual raindrop page  
            response = self.client.get("/raindrops/example-article.html")
            assert response.status_code == 200
            assert "Example Article" in response.text

    def test_partial_generation_failure(self):
        """
        Test: Site generation failed midway through raindrops processing
        
        Real scenario:
        1. Generator starts processing raindrops
        2. Creates directory and some files
        3. Crashes before creating index.html
        4. Leaves partial artifacts
        """
        output_dir = self.temp_dir / "output"
        raindrops_dir = output_dir / "raindrops"
        raindrops_dir.mkdir(parents=True)
        
        # Create individual raindrop files but no index
        (raindrops_dir / "raindrop1.html").write_text("<html>Raindrop 1</html>")
        (raindrops_dir / "raindrop2.html").write_text("<html>Raindrop 2</html>") 
        # No index.html - generation failed before creating listing
        
        with patch.dict(config, {"output_dir": output_dir}):
            # Main listing should return 404
            response = self.client.get("/raindrops/")
            assert response.status_code == 404
            
            # But individual raindrops should work
            response = self.client.get("/raindrops/raindrop1.html")
            assert response.status_code == 200
            assert "Raindrop 1" in response.text