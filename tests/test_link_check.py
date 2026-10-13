#!/usr/bin/env python3
# test_link_check — Tests for the dead self-link checker
# Author: Pito Salas and Claude Code

import pytest

from salasblog2.link_check import DeadLink, find_dead_self_links


@pytest.fixture
def site(tmp_path):
    output = tmp_path / "output"
    (output / "blog").mkdir(parents=True)
    (output / "blog" / "good.html").write_text("ok")
    (output / "tags" / "lotus").mkdir(parents=True)
    (output / "tags" / "lotus" / "index.html").write_text("ok")
    (output / "about.html").write_text("ok")
    content = tmp_path / "content" / "blog"
    content.mkdir(parents=True)
    return content, output


def test_reports_only_dead_self_links(site):
    content, output = site
    (content / "post.md").write_text(
        "[good](/blog/good.html) [tag](/tags/lotus/) [about](/about) "
        "[abs](https://www.salas.com/blog/good.html) "
        "[mapped](/weblogs/archives/000522.html) "
        "[unmapped](/weblogs/archives/000999.html) "
        "[dead](/blog/missing.html) [external](https://example.com/missing) "
        "[protocol-relative](//en.wikipedia.org/wiki/X)"
    )
    redirects = {"/weblogs/archives/000522.html": "/blog/good.html"}
    assert find_dead_self_links([content], output, redirects) == [
        DeadLink("post.md", "/weblogs/archives/000999.html"),
        DeadLink("post.md", "/blog/missing.html"),
    ]


def test_missing_output_dir_raises(tmp_path):
    with pytest.raises(FileNotFoundError, match="Generated site not found"):
        find_dead_self_links([tmp_path], tmp_path / "nope", {})
