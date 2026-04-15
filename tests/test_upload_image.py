"""
Tests for POST /api/upload-image endpoint.

Run with: uv run pytest tests/test_upload_image.py -v
"""

import pytest
import re
from pathlib import Path
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path):
    from salasblog2.server import app, config
    config["root_dir"] = tmp_path
    config["output_dir"] = tmp_path / "output"
    (tmp_path / "output").mkdir()
    config["admin_password"] = ""
    return TestClient(app)


@pytest.fixture
def authed_client(tmp_path):
    from salasblog2.server import app, config
    config["root_dir"] = tmp_path
    config["output_dir"] = tmp_path / "output"
    (tmp_path / "output").mkdir()
    config["admin_password"] = "secret"
    client = TestClient(app)
    client.post("/admin", data={"password": "secret"})
    return client


class TestUploadImage:

    def test_upload_returns_url(self, client, tmp_path):
        """Authenticated upload returns a JSON url."""
        image_data = b"\x89PNG\r\n\x1a\nfakeimage"
        response = client.post(
            "/api/upload-image",
            files={"file": ("photo.png", image_data, "image/png")},
        )
        assert response.status_code == 200
        body = response.json()
        assert "data" in body
        assert body["data"]["filePath"].startswith("/static/images/uploads/")
        assert body["data"]["filePath"].endswith("photo.png")

    def test_filename_is_date_prefixed(self, client, tmp_path):
        """Uploaded filename gets a YYYY-MM-DD prefix."""
        response = client.post(
            "/api/upload-image",
            files={"file": ("myimage.jpg", b"data", "image/jpeg")},
        )
        assert response.status_code == 200
        filename = response.json()["data"]["filePath"].split("/")[-1]
        assert re.match(r"^\d{4}-\d{2}-\d{2}-myimage\.jpg$", filename), \
            f"Expected date-prefixed filename, got: {filename}"

    def test_unauthenticated_returns_401(self, tmp_path):
        """Request without a valid session is rejected."""
        from salasblog2.server import app, config
        config["root_dir"] = tmp_path
        config["output_dir"] = tmp_path / "output"
        (tmp_path / "output").mkdir(exist_ok=True)
        config["admin_password"] = "secret"
        client = TestClient(app, raise_server_exceptions=False)
        response = client.post(
            "/api/upload-image",
            files={"file": ("photo.png", b"data", "image/png")},
        )
        assert response.status_code == 401
