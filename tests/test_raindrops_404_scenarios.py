#!/usr/bin/env python3
# test_raindrops_404_scenarios.py — 404 scenarios for the /raindrops/ endpoint
# Author: Pito Salas and Claude Code
# Open Source Under MIT license

import pytest
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException

from salasblog2.server import app, config


class TestRaindrops404Scenarios:

    def test_missing_output_dir_config_returns_404(self, tmp_path):
        client = TestClient(app)
        with patch.dict(config, {"output_dir": None}, clear=True):
            response = client.get("/raindrops/")
            assert response.status_code == 404
            assert response.json() == {"detail": "Not found"}

    def test_empty_output_dir_config_returns_404(self, tmp_path):
        client = TestClient(app)
        with patch.dict(config, {"output_dir": ""}, clear=True):
            response = client.get("/raindrops/")
            assert response.status_code == 404
            assert response.json() == {"detail": "Not found"}

    def test_missing_output_dir_key_returns_404(self, tmp_path):
        client = TestClient(app)
        with patch.dict(config, {}, clear=True):
            response = client.get("/raindrops/")
            assert response.status_code == 404
            assert response.json() == {"detail": "Not found"}

    def test_raindrops_directory_not_exists_returns_404(self, tmp_path):
        client = TestClient(app)
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        # Note: not creating raindrops subdirectory

        with patch.dict(config, {"output_dir": output_dir}):
            response = client.get("/raindrops/")
            assert response.status_code == 404
            assert response.json() == {"detail": "Not found"}

    def test_site_not_generated_returns_404(self, tmp_path):
        client = TestClient(app)
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        # No raindrops directory exists - site generation hasn't created it yet

        with patch.dict(config, {"output_dir": output_dir}):
            response = client.get("/raindrops/")
            assert response.status_code == 404, f"Should return 404 when site not generated, got {response.status_code}"
            assert response.json() == {"detail": "Not found"}

    def test_raindrops_generated_but_empty_returns_404(self, tmp_path):
        client = TestClient(app)
        output_dir = tmp_path / "output"
        raindrops_dir = output_dir / "raindrops"
        raindrops_dir.mkdir(parents=True)
        # Directory exists but no index.html

        with patch.dict(config, {"output_dir": output_dir}):
            response = client.get("/raindrops/")
            assert response.status_code == 404, f"Should return 404 when no index.html generated, got {response.status_code}"

    def test_corrupted_site_structure_returns_404(self, tmp_path):
        client = TestClient(app)
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        # Create raindrops as a file instead of directory - corrupted structure
        (output_dir / "raindrops").write_text("Corrupted: should be directory")

        with patch.dict(config, {"output_dir": output_dir}):
            response = client.get("/raindrops/")
            assert response.status_code == 404, "Server should return 404 for corrupted site structure"

    def test_path_traversal_vulnerability_exists(self, tmp_path):
        # SECURITY TEST: Documents existing path traversal vulnerability
        client = TestClient(app)
        output_dir = tmp_path / "output"
        raindrops_dir = output_dir / "raindrops"
        raindrops_dir.mkdir(parents=True)
        (raindrops_dir / "index.html").write_text("Safe content")

        (output_dir / "sensitive.txt").write_text("Secret data")
        (output_dir / ".env").write_text("DATABASE_PASSWORD=secret123")

        with patch.dict(config, {"output_dir": output_dir}):
            # Hidden files must never be served (even via normalized URLs)
            for path in ["../.env", "../.env.local"]:
                response = client.get(f"/raindrops/{path}")
                assert "DATABASE_PASSWORD" not in response.text, \
                    f"Hidden file exposed via {path}"

            # Paths that escape with multiple segments must not expose system files
            response = client.get("/raindrops/../../etc/passwd")
            assert response.status_code in [404, 400], \
                "Deep traversal should be blocked"

    def test_missing_index_html_returns_404(self, tmp_path):
        client = TestClient(app)
        output_dir = tmp_path / "output"
        raindrops_dir = output_dir / "raindrops"
        raindrops_dir.mkdir(parents=True)
        # Note: not creating index.html

        with patch.dict(config, {"output_dir": output_dir}):
            response = client.get("/raindrops/")
            assert response.status_code == 404
            assert response.json() == {"detail": "Not found"}

    def test_index_html_is_directory_returns_404(self, tmp_path):
        client = TestClient(app)
        output_dir = tmp_path / "output"
        raindrops_dir = output_dir / "raindrops"
        raindrops_dir.mkdir(parents=True)
        # Create index.html as directory instead of file
        (raindrops_dir / "index.html").mkdir()

        with patch.dict(config, {"output_dir": output_dir}):
            response = client.get("/raindrops/")
            assert response.status_code == 404
            assert response.json() == {"detail": "Not found"}

    def test_empty_index_html_serves_successfully(self, tmp_path):
        client = TestClient(app)
        output_dir = tmp_path / "output"
        raindrops_dir = output_dir / "raindrops"
        raindrops_dir.mkdir(parents=True)
        (raindrops_dir / "index.html").write_text("")

        with patch.dict(config, {"output_dir": output_dir}):
            response = client.get("/raindrops/")
            assert response.status_code == 200
            assert response.text == ""
            assert response.headers["content-type"] == "text/html; charset=utf-8"

    def test_corrupted_index_html_serves_successfully(self, tmp_path):
        client = TestClient(app)
        output_dir = tmp_path / "output"
        raindrops_dir = output_dir / "raindrops"
        raindrops_dir.mkdir(parents=True)
        (raindrops_dir / "index.html").write_text("<<>>invalid<<html>>")

        with patch.dict(config, {"output_dir": output_dir}):
            response = client.get("/raindrops/")
            assert response.status_code == 200
            assert response.text == "<<>>invalid<<html>>"

    def test_valid_index_html_no_raindrops_content_serves_successfully(self, tmp_path):
        client = TestClient(app)
        output_dir = tmp_path / "output"
        raindrops_dir = output_dir / "raindrops"
        raindrops_dir.mkdir(parents=True)

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
            response = client.get("/raindrops/")
            assert response.status_code == 200
            assert "No raindrops found" in response.text

    def test_permission_errors_should_return_404_not_crash(self, tmp_path):
        client = TestClient(app)
        output_dir = tmp_path / "output"
        raindrops_dir = output_dir / "raindrops"
        raindrops_dir.mkdir(parents=True)
        index_file = raindrops_dir / "index.html"
        index_file.write_text("<html><body>Test</body></html>")

        with patch.dict(config, {"output_dir": output_dir}):
            with patch.object(Path, 'read_bytes', side_effect=PermissionError("Permission denied")):
                response = client.get("/raindrops/")
                assert response.status_code == 404, f"POOR ERROR HANDLING: Permission error should return 404, not crash. Got unhandled exception."

    def test_directory_permission_errors_should_return_404_not_crash(self, tmp_path):
        client = TestClient(app)
        output_dir = tmp_path / "output"
        raindrops_dir = output_dir / "raindrops"
        raindrops_dir.mkdir(parents=True)

        with patch.dict(config, {"output_dir": output_dir}):
            with patch.object(Path, 'is_dir', side_effect=PermissionError("Permission denied")):
                response = client.get("/raindrops/")
                assert response.status_code == 404, f"POOR ERROR HANDLING: Directory permission error should return 404, not crash. Got unhandled exception."

    def test_valid_raindrops_index_serves_successfully(self, tmp_path):
        client = TestClient(app)
        output_dir = tmp_path / "output"
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
            response = client.get("/raindrops/")
            assert response.status_code == 200
            assert "Link Blog" in response.text
            assert "Example Link" in response.text
            assert response.headers["content-type"] == "text/html; charset=utf-8"

    def test_specific_raindrop_file_serves_successfully(self, tmp_path):
        client = TestClient(app)
        output_dir = tmp_path / "output"
        raindrops_dir = output_dir / "raindrops"
        raindrops_dir.mkdir(parents=True)

        raindrop_content = "<html><body><h1>Specific Raindrop</h1></body></html>"
        (raindrops_dir / "test-raindrop.html").write_text(raindrop_content)

        with patch.dict(config, {"output_dir": output_dir}):
            response = client.get("/raindrops/test-raindrop.html")
            assert response.status_code == 200
            assert "Specific Raindrop" in response.text

    def test_head_request_returns_headers_only(self, tmp_path):
        client = TestClient(app)
        output_dir = tmp_path / "output"
        raindrops_dir = output_dir / "raindrops"
        raindrops_dir.mkdir(parents=True)
        (raindrops_dir / "index.html").write_text("<html><body>Test</body></html>")

        with patch.dict(config, {"output_dir": output_dir}):
            response = client.head("/raindrops/")
            assert response.status_code == 200
            assert response.text == ""  # HEAD should return empty body
            assert response.headers["content-type"] == "text/html; charset=utf-8"


# Additional integration tests that test real-world scenarios
class TestRaindropsRealWorldScenarios:
    """Realistic integration tests based on actual raindrops system behavior"""

    def test_fresh_deployment_scenario(self, tmp_path):
        client = TestClient(app)
        output_dir = tmp_path / "output"
        # Don't create anything - simulate fresh deployment

        with patch.dict(config, {"output_dir": output_dir}):
            response = client.get("/raindrops/")
            assert response.status_code == 404
            assert response.json() == {"detail": "Not found"}

    def test_raindrops_synced_but_site_not_generated(self, tmp_path):
        client = TestClient(app)
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        # Simulate other parts of site generated but not raindrops
        (output_dir / "blog").mkdir()
        (output_dir / "static").mkdir()
        (output_dir / "index.html").write_text("Home page")
        # Note: no raindrops directory - generation didn't process raindrops yet

        with patch.dict(config, {"output_dir": output_dir}):
            response = client.get("/raindrops/")
            assert response.status_code == 404

    def test_empty_raindrops_source_directory_old_behavior(self, tmp_path):
        client = TestClient(app)
        output_dir = tmp_path / "output"
        raindrops_dir = output_dir / "raindrops"
        raindrops_dir.mkdir(parents=True)
        # Directory exists but no index.html - simulating old buggy behavior

        with patch.dict(config, {"output_dir": output_dir}):
            response = client.get("/raindrops/")
            assert response.status_code == 404

    def test_generator_fix_creates_index_for_empty_raindrops(self, tmp_path):
        client = TestClient(app)
        from salasblog2.generator import SiteGenerator

        output_dir = tmp_path / "output"
        output_dir.mkdir(parents=True)

        generator = SiteGenerator()
        generator.output_dir = output_dir

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

        empty_posts = []
        generator.generate_listing_pages(empty_posts, 'raindrops')

        index_file = output_dir / "raindrops" / "index.html"
        assert index_file.exists(), "Generator should create index.html even for empty raindrops"

        content = index_file.read_text()
        assert "Total posts: 0" in content
        assert "Total pages: 1" in content  # Should be 1 due to our fix
        assert "No raindrops found" in content

        with patch.dict(config, {"output_dir": output_dir}):
            response = client.get("/raindrops/")
            assert response.status_code == 200, "Should serve empty raindrops page successfully"
            assert "No raindrops found" in response.text

    def test_successful_raindrops_generation(self, tmp_path):
        client = TestClient(app)
        output_dir = tmp_path / "output"
        raindrops_dir = output_dir / "raindrops"
        raindrops_dir.mkdir(parents=True)

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
            response = client.get("/raindrops/")
            assert response.status_code == 200
            assert "Link Blog" in response.text
            assert "Example Article" in response.text
            assert "example.com" in response.text

            response = client.get("/raindrops/example-article.html")
            assert response.status_code == 200
            assert "Example Article" in response.text

    def test_partial_generation_failure(self, tmp_path):
        client = TestClient(app)
        output_dir = tmp_path / "output"
        raindrops_dir = output_dir / "raindrops"
        raindrops_dir.mkdir(parents=True)

        (raindrops_dir / "raindrop1.html").write_text("<html>Raindrop 1</html>")
        (raindrops_dir / "raindrop2.html").write_text("<html>Raindrop 2</html>")
        # No index.html - generation failed before creating listing

        with patch.dict(config, {"output_dir": output_dir}):
            response = client.get("/raindrops/")
            assert response.status_code == 404

            response = client.get("/raindrops/raindrop1.html")
            assert response.status_code == 200
            assert "Raindrop 1" in response.text
