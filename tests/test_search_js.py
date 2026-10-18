#!/usr/bin/env python3
# test_search_js — Runs the site's search filter (static/js/script.js) under Node
# Author: Pito Salas and Claude Code
# Version: 1
# Created: 2026-10-18
# Updated: 2026-10-18

import json
import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPT_JS = Path(__file__).parents[1] / "static" / "js" / "script.js"
NODE = shutil.which("node")

HARNESS = """
const vm = require("vm");
const fs = require("fs");
const context = { document: { addEventListener() {} }, console };
vm.createContext(context);
vm.runInContext(fs.readFileSync(process.argv[1], "utf8"), context);
context.searchData = JSON.parse(process.argv[2]);
vm.runInContext("searchData = this.searchData", context);
const query = process.argv[3];
const found = vm.runInContext(`performSearch(${JSON.stringify(query)})`, context);
console.log(JSON.stringify(found.map(item => item.title)));
"""

ITEMS = [
    {"title": "Old post", "content": "About spreadsheets", "type": "wp"},
    {"title": "A link", "content": "Some article", "type": "drop"},
    {"title": "About", "content": "Who I am", "type": "page"},
    {"title": "Blogging tips", "content": "How to write", "type": "blog"},
]


def search(query: str) -> list[str]:
    result = subprocess.run(
        [NODE, "-e", HARNESS, str(SCRIPT_JS), json.dumps(ITEMS), query],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


pytestmark = pytest.mark.skipif(NODE is None, reason="node not installed")


@pytest.mark.parametrize("query", ["wp", "drop", "page"])
def test_type_only_query_matches_nothing(query):
    """Regression: queries used to match each item's content type."""
    assert search(query) == []


def test_title_match_still_found():
    assert search("blogging") == ["Blogging tips"]


def test_content_match_still_found():
    assert search("spreadsheet") == ["Old post"]


def test_query_under_two_chars_returns_nothing():
    assert search("a") == []
