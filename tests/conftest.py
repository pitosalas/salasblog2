#!/usr/bin/env python3
# conftest.py — Shared pytest fixtures for salasblog2 test suite
# Author: Pito Salas and Claude Code
# Open Source Under MIT license

from pathlib import Path
import pytest
from jinja2 import Environment, FileSystemLoader
from salasblog2.generator import SiteGenerator
from salasblog2.utils import format_date, group_posts_by_month, get_markdown_processor, process_markdown_to_html, slugify_tag

PROJECT_ROOT = Path(__file__).parent.parent


@pytest.fixture
def generator(tmp_path):
    """Return a SiteGenerator wired to tmp_path for output, real templates."""
    g = SiteGenerator()
    g.root_dir = PROJECT_ROOT
    g.templates_dir = PROJECT_ROOT / "templates"
    g.static_dir = PROJECT_ROOT / "static"
    g.output_dir = tmp_path / "output"
    g.output_dir.mkdir()
    g.jinja_env = Environment(loader=FileSystemLoader(g.templates_dir))
    g.jinja_env.filters['strftime'] = g.format_date
    g.jinja_env.filters['dd_mm_yyyy'] = lambda d: format_date(d, '%d-%m-%Y')
    g.jinja_env.filters['group_by_month'] = group_posts_by_month
    g.jinja_env.filters['markdown'] = g.markdown_to_html
    g.jinja_env.filters['slugify'] = slugify_tag
    return g
