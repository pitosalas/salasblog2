"""
Tests for XML-RPC request parsing in server.py, focused on base64 support.

Run with: uv run pytest tests/test_xmlrpc_parsing.py -v
"""

import pytest
import base64
from unittest.mock import patch, MagicMock


def _make_xmlrpc_body(method_name: str, params_xml: str) -> bytes:
    return f"""<?xml version="1.0"?>
<methodCall>
  <methodName>{method_name}</methodName>
  <params>
    {params_xml}
  </params>
</methodCall>""".encode("utf-8")


def _base64_param(data: bytes) -> str:
    encoded = base64.b64encode(data).decode("ascii")
    return f"<param><value><base64>{encoded}</base64></value></param>"


def _struct_with_base64(key: str, data: bytes, name: str = "image.png", mime: str = "image/png") -> str:
    encoded = base64.b64encode(data).decode("ascii")
    return f"""<param><value><struct>
      <member><name>name</name><value><string>{name}</string></value></member>
      <member><name>type</name><value><string>{mime}</string></value></member>
      <member><name>{key}</name><value><base64>{encoded}</base64></value></member>
    </struct></value></param>"""


class TestBase64Parsing:
    """Test that the XML-RPC dispatcher correctly parses base64 values."""

    @pytest.fixture
    def client(self, tmp_path):
        """FastAPI test client with isolated content directory."""
        from fastapi.testclient import TestClient
        from salasblog2.server import app, config
        config["output_dir"] = tmp_path / "output"
        (tmp_path / "output").mkdir()
        return TestClient(app)

    def test_top_level_base64_param_decoded_to_bytes(self, client, tmp_path):
        """A top-level <base64> param must be decoded to bytes before dispatch."""
        image_data = b"\x89PNG\r\n\x1a\nfakeimage"
        body = _make_xmlrpc_body(
            "metaWeblog.newMediaObject",
            '<param><value><string>1</string></value></param>'
            '<param><value><string>user</string></value></param>'
            '<param><value><string>pass</string></value></param>'
            + _struct_with_base64("bits", image_data),
        )

        received = {}

        def fake_new_media(blogid, username, password, struct):
            received["bits"] = struct.get("bits")
            return {"url": "/static/images/uploads/test.png"}

        with patch("salasblog2.server.BloggerAPI") as MockAPI:
            instance = MagicMock()
            instance.metaweblog_newMediaObject.side_effect = fake_new_media
            MockAPI.return_value = instance

            response = client.post(
                "/xmlrpc",
                content=body,
                headers={"Content-Type": "text/xml"},
            )

        assert response.status_code == 200
        assert isinstance(received.get("bits"), bytes), "bits should be decoded to bytes"
        assert received["bits"] == image_data

    def test_struct_base64_member_decoded_to_bytes(self, client, tmp_path):
        """A <base64> value inside a struct member must be decoded to bytes."""
        image_data = b"fakepngdata"
        body = _make_xmlrpc_body(
            "metaWeblog.newMediaObject",
            '<param><value><string>1</string></value></param>'
            '<param><value><string>user</string></value></param>'
            '<param><value><string>pass</string></value></param>'
            + _struct_with_base64("bits", image_data, name="photo.jpg", mime="image/jpeg"),
        )

        received = {}

        def fake_new_media(blogid, username, password, struct):
            received["struct"] = struct
            return {"url": "/static/images/uploads/photo.jpg"}

        with patch("salasblog2.server.BloggerAPI") as MockAPI:
            instance = MagicMock()
            instance.metaweblog_newMediaObject.side_effect = fake_new_media
            MockAPI.return_value = instance

            response = client.post(
                "/xmlrpc",
                content=body,
                headers={"Content-Type": "text/xml"},
            )

        assert response.status_code == 200
        s = received.get("struct", {})
        assert isinstance(s.get("bits"), bytes), "struct bits should be bytes"
        assert s["bits"] == image_data
        assert s["name"] == "photo.jpg"
        assert s["type"] == "image/jpeg"
