#!/usr/bin/env python3
# test_stats.py — Tests for F25/F26 visit statistics
# Author: Pito Salas and Claude Code
# Open Source Under MIT license

import json
import pytest
from pathlib import Path
from salasblog2.stats import VisitCounter


class TestVisitCounter:
    def test_get_returns_zero_for_unseen_path(self, tmp_path):
        counter = VisitCounter()
        counter.stats_file = tmp_path / "stats.json"
        counter._counts = {}
        assert counter.get("/") == 0

    def test_increment_increases_total_count(self, tmp_path):
        counter = VisitCounter()
        counter.stats_file = tmp_path / "stats.json"
        counter._counts = {}
        counter.increment("/", "human")
        assert counter.get("/") == 1

    def test_increment_multiple_times(self, tmp_path):
        counter = VisitCounter()
        counter.stats_file = tmp_path / "stats.json"
        counter._counts = {}
        for _ in range(5):
            counter.increment("/raindrops/", "human")
        assert counter.get("/raindrops/") == 5

    def test_increment_persists_to_file(self, tmp_path):
        counter = VisitCounter()
        counter.stats_file = tmp_path / "stats.json"
        counter._counts = {}
        counter.increment("/", "human")
        counter.increment("/raindrops/", "ai_bot")

        data = json.loads((tmp_path / "stats.json").read_text())
        assert data["/"]["human"] == 1
        assert data["/raindrops/"]["ai_bot"] == 1

    def test_load_restores_counts(self, tmp_path):
        stats_file = tmp_path / "stats.json"
        stats_file.write_text(json.dumps({"/": {"human": 42}, "/raindrops/": {"search_engine": 7}}))

        counter = VisitCounter()
        counter.stats_file = stats_file
        counter._counts = counter._load()

        assert counter.get("/") == 42
        assert counter.get("/raindrops/") == 7

    def test_load_migrates_old_int_format(self, tmp_path):
        stats_file = tmp_path / "stats.json"
        stats_file.write_text(json.dumps({"/": 15}))

        counter = VisitCounter()
        counter.stats_file = stats_file
        counter._counts = counter._load()

        assert counter.get("/") == 15

    def test_get_all_sorted_by_total_descending(self, tmp_path):
        counter = VisitCounter()
        counter.stats_file = tmp_path / "stats.json"
        counter._counts = {
            "/": {"human": 3},
            "/raindrops/": {"human": 8, "ai_bot": 2},
            "/pages/about.html": {"human": 1},
        }
        result = counter.get_all()
        totals = [sum(t.values()) for _, t in result]
        assert totals == sorted(totals, reverse=True)

    def test_get_all_returns_all_entries(self, tmp_path):
        counter = VisitCounter()
        counter.stats_file = tmp_path / "stats.json"
        counter._counts = {"/": {"human": 1}, "/raindrops/": {"ai_bot": 2}}
        assert len(counter.get_all()) == 2

    def test_missing_file_returns_empty(self, tmp_path):
        counter = VisitCounter()
        counter.stats_file = tmp_path / "nonexistent.json"
        assert counter._load() == {}

    def test_independent_counts_per_path(self, tmp_path):
        counter = VisitCounter()
        counter.stats_file = tmp_path / "stats.json"
        counter._counts = {}
        counter.increment("/", "human")
        counter.increment("/raindrops/", "human")
        counter.increment("/raindrops/", "ai_bot")
        assert counter.get("/") == 1
        assert counter.get("/raindrops/") == 2

    def test_counts_split_by_visitor_type(self, tmp_path):
        counter = VisitCounter()
        counter.stats_file = tmp_path / "stats.json"
        counter._counts = {}
        counter.increment("/", "human")
        counter.increment("/", "human")
        counter.increment("/", "ai_bot")
        types = counter._counts["/"]
        assert types["human"] == 2
        assert types["ai_bot"] == 1
