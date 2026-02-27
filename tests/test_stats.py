#!/usr/bin/env python3
# test_stats.py — Tests for F25 visit statistics
# Author: Pito Salas and Claude Code
# Open Source Under MIT license

import json
import pytest
from pathlib import Path
from salasblog2.stats import VisitCounter


class TestVisitCounter:
    def test_increment_starts_at_zero(self, tmp_path):
        counter = VisitCounter()
        counter.stats_file = tmp_path / "stats.json"
        counter._counts = {}
        assert counter.get("/") == 0

    def test_increment_increases_count(self, tmp_path):
        counter = VisitCounter()
        counter.stats_file = tmp_path / "stats.json"
        counter._counts = {}
        counter.increment("/")
        assert counter.get("/") == 1

    def test_increment_multiple_times(self, tmp_path):
        counter = VisitCounter()
        counter.stats_file = tmp_path / "stats.json"
        counter._counts = {}
        for _ in range(5):
            counter.increment("/raindrops/")
        assert counter.get("/raindrops/") == 5

    def test_increment_persists_to_file(self, tmp_path):
        counter = VisitCounter()
        counter.stats_file = tmp_path / "stats.json"
        counter._counts = {}
        counter.increment("/")
        counter.increment("/raindrops/")

        data = json.loads((tmp_path / "stats.json").read_text())
        assert data["/"] == 1
        assert data["/raindrops/"] == 1

    def test_load_restores_counts(self, tmp_path):
        stats_file = tmp_path / "stats.json"
        stats_file.write_text(json.dumps({"/": 42, "/raindrops/": 7}))

        counter = VisitCounter()
        counter.stats_file = stats_file
        counter._counts = counter._load()

        assert counter.get("/") == 42
        assert counter.get("/raindrops/") == 7

    def test_get_all_sorted_by_count_descending(self, tmp_path):
        counter = VisitCounter()
        counter.stats_file = tmp_path / "stats.json"
        counter._counts = {"/": 3, "/raindrops/": 10, "/pages/about.html": 1}

        result = counter.get_all()
        counts = [c for _, c in result]
        assert counts == sorted(counts, reverse=True)

    def test_get_all_returns_all_entries(self, tmp_path):
        counter = VisitCounter()
        counter.stats_file = tmp_path / "stats.json"
        counter._counts = {"/": 1, "/raindrops/": 2}

        assert len(counter.get_all()) == 2

    def test_missing_file_returns_empty(self, tmp_path):
        counter = VisitCounter()
        counter.stats_file = tmp_path / "nonexistent.json"
        result = counter._load()
        assert result == {}

    def test_independent_counts_per_path(self, tmp_path):
        counter = VisitCounter()
        counter.stats_file = tmp_path / "stats.json"
        counter._counts = {}
        counter.increment("/")
        counter.increment("/raindrops/")
        counter.increment("/raindrops/")
        assert counter.get("/") == 1
        assert counter.get("/raindrops/") == 2
