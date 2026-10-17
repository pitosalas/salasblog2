#!/usr/bin/env python3
# test_legacy_redirects — Tests for 301 redirects from pre-salasblog2 URLs
# Author: Pito Salas and Claude Code
# Version: 1
# Created: 2026-10-17
# Updated: 2026-10-17

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from salasblog2.server import app, config

TARGETS = {
    "/weblogs/archives/000522.html": "/blog/2004-11-29-why-improv.html",
    "/2008/02/18/about-amzn": "/blog/2008-02-18-about-amzn.html",
    "/blog/2012/5/6/field-of-dreams.html": "/blog/2012-05-06-field-of-dreams.html",
}


@pytest.fixture
def client(tmp_path):
    (tmp_path / "index.html").write_text("home")
    (tmp_path / "blog").mkdir()
    (tmp_path / "blog" / "2004-11-29-why-improv.html").write_text("post")
    with (
        patch.dict(config, {"output_dir": tmp_path}),
        patch("salasblog2.server.legacy_redirect_targets", return_value=TARGETS),
    ):
        yield TestClient(app, follow_redirects=False)


@pytest.mark.parametrize(
    "legacy_url, new_url",
    [
        ("/weblogs/archives/000522.html", "/blog/2004-11-29-why-improv.html"),
        ("/2008/02/18/about-amzn/", "/blog/2008-02-18-about-amzn.html"),
        ("/2008/02/18/about-amzn", "/blog/2008-02-18-about-amzn.html"),
        (
            "/blog/2012/5/6/field-of-dreams.html",
            "/blog/2012-05-06-field-of-dreams.html",
        ),
    ],
)
def test_mapped_legacy_url_redirects_permanently(client, legacy_url, new_url):
    response = client.get(legacy_url)
    assert response.status_code == 301
    assert response.headers["location"] == new_url


def test_head_request_also_redirects(client):
    response = client.head("/weblogs/archives/000522.html")
    assert response.status_code == 301


def test_unmapped_legacy_url_is_404(client):
    assert client.get("/weblogs/archives/000999.html").status_code == 404


def test_existing_routes_still_resolve(client):
    assert client.get("/").status_code == 200
    assert client.get("/blog/2004-11-29-why-improv.html").text == "post"
    assert client.get("/no-such-page.html").status_code == 404
