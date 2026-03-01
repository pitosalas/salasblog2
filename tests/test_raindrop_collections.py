#!/usr/bin/env python3
# test_raindrop_collections.py — Tests for raindrop collection filtering
# Author: Pito Salas and Claude Code
# Open Source Under MIT license

import pytest
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from salasblog2.utils import extract_unique_collections, slugify_collection, format_date
from salasblog2.generator import SiteGenerator


def _make_template_env(templates_dir):
    env = Environment(loader=FileSystemLoader(templates_dir))
    env.filters['slugify'] = lambda x: x.lower().replace(' ', '-')
    env.filters['strftime'] = lambda d, fmt: format_date(d, fmt)
    env.filters['dd_mm_yyyy'] = lambda d: format_date(d, '%d-%m-%Y')
    env.filters['truncate'] = lambda s, n, killwords=False, end='...': (s[:n] + end) if s and len(s) > n else (s or '')
    return env


def test_extract_unique_collections_returns_sorted_list():
    raindrops = [
        {'collection': 'Reading'},
        {'collection': 'Tools'},
        {'collection': 'Reading'},
        {'collection': 'Articles'},
    ]
    result = extract_unique_collections(raindrops)
    assert result == ['Articles', 'Reading', 'Tools']


def test_extract_unique_collections_ignores_empty_values():
    raindrops = [
        {'collection': 'Reading'},
        {'collection': ''},
        {'collection': None},
        {'collection': '   '},
    ]
    result = extract_unique_collections(raindrops)
    assert result == ['Reading']


def test_extract_unique_collections_missing_field():
    raindrops = [
        {'title': 'Post 1'},
        {'collection': 'Tools'},
        {'title': 'Post 2'},
    ]
    result = extract_unique_collections(raindrops)
    assert result == ['Tools']


def test_extract_unique_collections_empty_list():
    result = extract_unique_collections([])
    assert result == []


@pytest.mark.parametrize("input_str,expected", [
    ('Reading', 'reading'),
    ('TOOLS', 'tools'),
    ('My Collection', 'my-collection'),
    ('Web  Dev', 'web-dev'),
    ('Tools & Utilities', 'tools-utilities'),
    ('C++', 'c'),
    ('-Reading-', 'reading'),
])
def test_slugify_collection(input_str, expected):
    assert slugify_collection(input_str) == expected


def test_collection_buttons_render_in_template():
    root_dir = Path.cwd()
    templates_dir = root_dir / "templates"
    env = _make_template_env(templates_dir)

    template = env.get_template("raindrops_list.html")
    context = {
        'posts': [],
        'collections': ['Reading', 'Tools'],
        'collection_counts': {'Reading': 3, 'Tools': 1},
        'pagination': None,
        'navigation': [],
        'total_posts': 0,
    }
    html = template.render(context)
    assert 'Reading' in html
    assert 'Tools' in html
    assert '/raindrops/reading' in html
    assert '/raindrops/tools' in html


def test_collection_buttons_show_all_link():
    root_dir = Path.cwd()
    templates_dir = root_dir / "templates"
    env = _make_template_env(templates_dir)

    template = env.get_template("raindrops_list.html")
    context = {
        'posts': [],
        'collections': ['Reading'],
        'collection_counts': {'Reading': 2},
        'pagination': None,
        'navigation': [],
        'total_posts': 0,
    }
    html = template.render(context)
    assert '/raindrops/reading' in html
    assert 'Reading' in html


def test_collection_filtered_pages_generated(tmp_path):
    generator = SiteGenerator()
    raindrops = [
        {
            'title': 'Post 1',
            'collection': 'Reading',
            'date': '2024-01-15',
            'url': '/raindrops/post1.html',
        },
        {
            'title': 'Post 2',
            'collection': 'Tools',
            'date': '2024-01-14',
            'url': '/raindrops/post2.html',
        },
        {
            'title': 'Post 3',
            'collection': 'Reading',
            'date': '2024-01-13',
            'url': '/raindrops/post3.html',
        },
    ]
    collections = ['Reading', 'Tools']

    generator.output_dir = tmp_path / "output"
    generator.output_dir.mkdir(exist_ok=True)

    generator.generate_collection_filtered_pages(raindrops, collections)

    # Check that collection directories were created
    assert (generator.output_dir / "raindrops" / "reading" / "index.html").exists()
    assert (generator.output_dir / "raindrops" / "tools" / "index.html").exists()

    # Check that Reading page has 2 posts
    reading_html = (generator.output_dir / "raindrops" / "reading" / "index.html").read_text()
    assert 'Post 1' in reading_html
    assert 'Post 3' in reading_html
    assert 'Post 2' not in reading_html

    # Check that Tools page has 1 post
    tools_html = (generator.output_dir / "raindrops" / "tools" / "index.html").read_text()
    assert 'Post 2' in tools_html
    assert 'Post 1' not in tools_html
    assert 'Post 3' not in tools_html
