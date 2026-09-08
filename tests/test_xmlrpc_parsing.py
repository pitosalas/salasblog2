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


def _struct_with_base64(
    key: str, data: bytes, name: str = "image.png", mime: str = "image/png"
) -> str:
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
            "<param><value><string>1</string></value></param>"
            "<param><value><string>user</string></value></param>"
            "<param><value><string>pass</string></value></param>"
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
        assert isinstance(received.get("bits"), bytes), (
            "bits should be decoded to bytes"
        )
        assert received["bits"] == image_data

    def test_struct_base64_member_decoded_to_bytes(self, client, tmp_path):
        """A <base64> value inside a struct member must be decoded to bytes."""
        image_data = b"fakepngdata"
        body = _make_xmlrpc_body(
            "metaWeblog.newMediaObject",
            "<param><value><string>1</string></value></param>"
            "<param><value><string>user</string></value></param>"
            "<param><value><string>pass</string></value></param>"
            + _struct_with_base64(
                "bits", image_data, name="photo.jpg", mime="image/jpeg"
            ),
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


def _struct_param(members_xml: str) -> str:
    return f"<param><value><struct>{members_xml}</struct></value></param>"


class TestArrayAndDateTimeParsing:
    """The old hand-rolled parser had no handling for <array> or <dateTime.iso8601>
    — both silently fell through to an empty string. These are exactly the types
    MarsEdit sends for categories/keywords and dateCreated, which is why it never
    worked. xmlrpc.client.loads() must handle both correctly."""

    @pytest.fixture
    def client(self, tmp_path):
        from fastapi.testclient import TestClient
        from salasblog2.server import app, config

        config["output_dir"] = tmp_path / "output"
        (tmp_path / "output").mkdir()
        return TestClient(app)

    def test_struct_array_member_decoded_to_list(self, client):
        """mt_keywords sent as an <array> must arrive as a Python list, not ''."""
        body = _make_xmlrpc_body(
            "metaWeblog.newPost",
            "<param><value><string>1</string></value></param>"
            "<param><value><string>user</string></value></param>"
            "<param><value><string>pass</string></value></param>"
            + _struct_param(
                "<member><name>title</name><value><string>Test Post</string></value></member>"
                "<member><name>description</name><value><string>Body text</string></value></member>"
                "<member><name>mt_keywords</name><value><array><data>"
                "<value><string>python</string></value>"
                "<value><string>testing</string></value>"
                "</data></array></value></member>"
            )
            + "<param><value><boolean>1</boolean></value></param>",
        )

        received = {}

        def fake_new_post(
            blogid, username, password, struct, publish, background_tasks=None
        ):
            received["struct"] = struct
            return "test-post.md"

        with patch("salasblog2.server.BloggerAPI") as MockAPI:
            instance = MagicMock()
            instance.metaweblog_newPost.side_effect = fake_new_post
            MockAPI.return_value = instance

            response = client.post(
                "/xmlrpc", content=body, headers={"Content-Type": "text/xml"}
            )

        assert response.status_code == 200
        struct = received.get("struct", {})
        assert struct.get("mt_keywords") == ["python", "testing"]

    def test_struct_datetime_member_not_silently_dropped(self, client):
        """dateCreated sent as <dateTime.iso8601> must decode to a real value, not
        an empty string (the old bug — none of the old parser's type checks matched
        dateTime.iso8601, so it fell through to the empty <value> text)."""
        body = _make_xmlrpc_body(
            "metaWeblog.newPost",
            "<param><value><string>1</string></value></param>"
            "<param><value><string>user</string></value></param>"
            "<param><value><string>pass</string></value></param>"
            + _struct_param(
                "<member><name>title</name><value><string>Test</string></value></member>"
                "<member><name>description</name><value><string>Body</string></value></member>"
                "<member><name>dateCreated</name>"
                "<value><dateTime.iso8601>20260908T10:00:00</dateTime.iso8601></value></member>"
            )
            + "<param><value><boolean>1</boolean></value></param>",
        )

        received = {}

        def fake_new_post(
            blogid, username, password, struct, publish, background_tasks=None
        ):
            received["struct"] = struct
            return "test-post.md"

        with patch("salasblog2.server.BloggerAPI") as MockAPI:
            instance = MagicMock()
            instance.metaweblog_newPost.side_effect = fake_new_post
            MockAPI.return_value = instance

            response = client.post(
                "/xmlrpc", content=body, headers={"Content-Type": "text/xml"}
            )

        assert response.status_code == 200
        date_created = received.get("struct", {}).get("dateCreated")
        assert date_created is not None and str(date_created) != "", (
            "dateCreated must not be silently dropped to an empty string"
        )


class TestNonBlockingRegeneration:
    """blogger.newPost/editPost/deletePost (and their MetaWeblog aliases) must be
    called with background_tasks so site regeneration doesn't block the XML-RPC
    response — mirrors the async-save pattern already used for the web admin form.
    Read-only methods must not receive it at all."""

    @pytest.fixture
    def client(self, tmp_path):
        from fastapi.testclient import TestClient
        from salasblog2.server import app, config

        config["output_dir"] = tmp_path / "output"
        (tmp_path / "output").mkdir()
        return TestClient(app)

    def test_new_post_receives_background_tasks(self, client):
        from starlette.background import BackgroundTasks

        body = _make_xmlrpc_body(
            "metaWeblog.newPost",
            "<param><value><string>1</string></value></param>"
            "<param><value><string>user</string></value></param>"
            "<param><value><string>pass</string></value></param>"
            "<param><value><string>Hello</string></value></param>"
            "<param><value><boolean>1</boolean></value></param>",
        )

        received = {}

        def fake_new_post(*args, **kwargs):
            received["background_tasks"] = kwargs.get("background_tasks")
            return "test-post.md"

        with patch("salasblog2.server.BloggerAPI") as MockAPI:
            instance = MagicMock()
            instance.metaweblog_newPost.side_effect = fake_new_post
            MockAPI.return_value = instance

            response = client.post(
                "/xmlrpc", content=body, headers={"Content-Type": "text/xml"}
            )

        assert response.status_code == 200
        assert isinstance(received.get("background_tasks"), BackgroundTasks)

    def test_get_recent_posts_not_given_background_tasks(self, client):
        body = _make_xmlrpc_body(
            "metaWeblog.getRecentPosts",
            "<param><value><string>1</string></value></param>"
            "<param><value><string>user</string></value></param>"
            "<param><value><string>pass</string></value></param>"
            "<param><value><int>5</int></value></param>",
        )

        received = {}

        def fake_get_recent(*args, **kwargs):
            received["kwargs"] = kwargs
            return []

        with patch("salasblog2.server.BloggerAPI") as MockAPI:
            instance = MagicMock()
            instance.metaweblog_getRecentPosts.side_effect = fake_get_recent
            MockAPI.return_value = instance

            response = client.post(
                "/xmlrpc", content=body, headers={"Content-Type": "text/xml"}
            )

        assert response.status_code == 200
        assert "background_tasks" not in received.get("kwargs", {})


class TestFaultHandling:
    """The response/fault builders now use xmlrpc.client.dumps(); the endpoint must
    surface a Fault's own code (not a hardcoded one) and never 500 on bad input."""

    @pytest.fixture
    def client(self, tmp_path):
        from fastapi.testclient import TestClient
        from salasblog2.server import app, config

        config["output_dir"] = tmp_path / "output"
        (tmp_path / "output").mkdir()
        return TestClient(app)

    def test_malformed_request_returns_fault_not_500(self, client):
        response = client.post(
            "/xmlrpc",
            content=b"not even xml",
            headers={"Content-Type": "text/xml"},
        )
        assert response.status_code == 200
        assert "<fault>" in response.text
        assert "<int>400</int>" in response.text

    def test_fault_raised_by_method_preserves_its_own_code(self, client):
        """A Fault raised inside a BloggerAPI method (e.g. 404) must come back with
        its own code — the old code hardcoded 403 for any 'Authentication failed'
        substring match and let everything else fall through to an unhandled 500."""
        from xmlrpc.client import Fault

        body = _make_xmlrpc_body(
            "blogger.getPost",
            "<param><value><string>appkey</string></value></param>"
            "<param><value><string>missing.md</string></value></param>"
            "<param><value><string>user</string></value></param>"
            "<param><value><string>pass</string></value></param>",
        )

        with patch("salasblog2.server.BloggerAPI") as MockAPI:
            instance = MagicMock()
            instance.blogger_getPost.side_effect = Fault(
                404, "Post 'missing.md' not found."
            )
            MockAPI.return_value = instance

            response = client.post(
                "/xmlrpc", content=body, headers={"Content-Type": "text/xml"}
            )

        assert response.status_code == 200
        assert "<int>404</int>" in response.text
        assert "not found" in response.text

    def test_response_content_type_declares_utf8_charset(self, client):
        """Regression: an explicit `headers={"Content-Type": "text/xml"}` on the
        Response(...) call overrides Starlette's automatic charset suffix,
        producing a bare `text/xml` header with no charset — even though the
        body bytes are UTF-8. A client that defaults to a non-UTF-8 encoding
        when no charset is declared (observed: MarsEdit failing with "XMLRPC
        Response Parsing Failed: (null)" on posts containing curly quotes /
        non-ASCII characters) then can't decode the body at all. Every XML-RPC
        response path must rely on media_type alone, not a duplicate header.
        """
        with patch("salasblog2.server.BloggerAPI") as MockAPI:
            instance = MagicMock()
            instance.blogger_getUsersBlogs.return_value = [
                {"blogid": "salasblog2", "blogName": "Salas Blog", "url": "/"}
            ]
            MockAPI.return_value = instance

            body = _make_xmlrpc_body(
                "blogger.getUsersBlogs",
                "<param><value><string>appkey</string></value></param>"
                "<param><value><string>user</string></value></param>"
                "<param><value><string>pass</string></value></param>",
            )
            response = client.post(
                "/xmlrpc", content=body, headers={"Content-Type": "text/xml"}
            )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/xml; charset=utf-8"

    def test_fault_response_content_type_declares_utf8_charset(self, client):
        """Same charset regression, for the fault-response path."""
        response = client.post(
            "/xmlrpc",
            content=b"not even xml",
            headers={"Content-Type": "text/xml"},
        )
        assert response.headers["content-type"] == "text/xml; charset=utf-8"
