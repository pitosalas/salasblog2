#!/usr/bin/env python3
# test_stats.py — Tests for F25/F26/F32 visit statistics
# Author: Pito Salas and Claude Code
# Open Source Under MIT license

import json
import pytest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from salasblog2.stats import VisitCounter


def _make_counter(tmp_path):
    counter = VisitCounter()
    counter.stats_file = tmp_path / "stats.json"
    counter._counts = {}
    return counter


class TestVisitCounter:
    def test_get_returns_zero_for_unseen_path(self, tmp_path):
        counter = _make_counter(tmp_path)
        assert counter.get("/") == 0

    def test_increment_increases_total_count(self, tmp_path):
        counter = _make_counter(tmp_path)
        counter.increment("/", "human")
        assert counter.get("/") == 1

    def test_increment_multiple_times(self, tmp_path):
        counter = _make_counter(tmp_path)
        for _ in range(5):
            counter.increment("/raindrops/", "human")
        assert counter.get("/raindrops/") == 5

    def test_increment_persists_to_file(self, tmp_path):
        counter = _make_counter(tmp_path)
        counter.increment("/", "human")
        counter.increment("/raindrops/", "ai_bot")
        counter.flush()

        data = json.loads((tmp_path / "stats.json").read_text())
        assert len(data["/"]["human"]) == 1
        assert len(data["/raindrops/"]["ai_bot"]) == 1

    def test_load_restores_counts(self, tmp_path):
        stats_file = tmp_path / "stats.json"
        now = datetime.now(timezone.utc).isoformat()
        stats_file.write_text(json.dumps({
            "/": {"human": [now, now]},
            "/raindrops/": {"search_engine": [now] * 7},
        }))

        counter = VisitCounter()
        counter.stats_file = stats_file
        counter._counts = counter._load()

        assert counter.get("/") == 2
        assert counter.get("/raindrops/") == 7

    def test_load_migrates_old_int_format(self, tmp_path):
        stats_file = tmp_path / "stats.json"
        stats_file.write_text(json.dumps({"/": 15}))

        counter = VisitCounter()
        counter.stats_file = stats_file
        counter._counts = counter._load()

        assert counter.get("/") == 15

    def test_load_migrates_old_type_count_format(self, tmp_path):
        stats_file = tmp_path / "stats.json"
        stats_file.write_text(json.dumps({"/": {"human": 5, "ai_bot": 3}}))

        counter = VisitCounter()
        counter.stats_file = stats_file
        counter._counts = counter._load()

        assert counter.get("/") == 8

    def test_get_all_sorted_by_total_descending(self, tmp_path):
        counter = _make_counter(tmp_path)
        now = datetime.now(timezone.utc).isoformat()
        counter._counts = {
            "/": {"human": [now] * 3},
            "/raindrops/": {"human": [now] * 8, "ai_bot": [now] * 2},
            "/pages/about.html": {"human": [now]},
        }
        result = counter.get_all()
        totals = [sum(t.values()) for _, t in result]
        assert totals == sorted(totals, reverse=True)

    def test_get_all_returns_all_entries(self, tmp_path):
        counter = _make_counter(tmp_path)
        now = datetime.now(timezone.utc).isoformat()
        counter._counts = {"/": {"human": [now]}, "/raindrops/": {"ai_bot": [now, now]}}
        assert len(counter.get_all()) == 2

    def test_missing_file_returns_empty(self, tmp_path):
        counter = VisitCounter()
        counter.stats_file = tmp_path / "nonexistent.json"
        assert counter._load() == {}

    def test_independent_counts_per_path(self, tmp_path):
        counter = _make_counter(tmp_path)
        counter.increment("/", "human")
        counter.increment("/raindrops/", "human")
        counter.increment("/raindrops/", "ai_bot")
        assert counter.get("/") == 1
        assert counter.get("/raindrops/") == 2

    def test_counts_split_by_visitor_type(self, tmp_path):
        counter = _make_counter(tmp_path)
        counter.increment("/", "human")
        counter.increment("/", "human")
        counter.increment("/", "ai_bot")
        types = counter._counts["/"]
        assert len(types["human"]) == 2
        assert len(types["ai_bot"]) == 1


class TestVisitCounterPeriodFiltering:
    def test_get_all_no_period_returns_all(self, tmp_path):
        counter = _make_counter(tmp_path)
        old_ts = (datetime.now(timezone.utc) - timedelta(days=400)).isoformat()
        now_ts = datetime.now(timezone.utc).isoformat()
        counter._counts = {"/": {"human": [old_ts, now_ts]}}
        result = counter.get_all(period=None)
        assert len(result) == 1
        assert result[0][1]["human"] == 2

    def test_get_all_today_excludes_old_visits(self, tmp_path):
        counter = _make_counter(tmp_path)
        yesterday = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        today = datetime.now(timezone.utc).isoformat()
        counter._counts = {"/": {"human": [yesterday, yesterday, today]}}
        result = counter.get_all(period="today")
        assert len(result) == 1
        assert result[0][1]["human"] == 1

    def test_get_all_today_empty_when_no_recent_visits(self, tmp_path):
        counter = _make_counter(tmp_path)
        old = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
        counter._counts = {"/": {"human": [old, old]}}
        result = counter.get_all(period="today")
        assert result == []

    def test_get_all_this_week_includes_recent(self, tmp_path):
        counter = _make_counter(tmp_path)
        today = datetime.now(timezone.utc)
        same_day = today.replace(hour=0, minute=1).isoformat()   # definitely today = this week
        last_year = (today - timedelta(days=400)).isoformat()    # definitely not this week
        counter._counts = {"/blog/post.html": {"human": [same_day, last_year]}}
        result = counter.get_all(period="this_week")
        assert len(result) == 1
        assert result[0][1]["human"] == 1

    def test_get_all_this_month_includes_this_month(self, tmp_path):
        counter = _make_counter(tmp_path)
        now = datetime.now(timezone.utc)
        this_month = now.replace(day=1, hour=12).isoformat()
        last_year = (now - timedelta(days=400)).isoformat()
        counter._counts = {"/": {"human": [this_month, last_year]}}
        result = counter.get_all(period="this_month")
        assert len(result) == 1
        assert result[0][1]["human"] == 1

    def test_get_all_this_year_includes_this_year(self, tmp_path):
        counter = _make_counter(tmp_path)
        now = datetime.now(timezone.utc)
        this_year = now.replace(month=1, day=2, hour=12).isoformat()
        last_year = (now - timedelta(days=400)).isoformat()
        counter._counts = {"/": {"human": [this_year, last_year]}}
        result = counter.get_all(period="this_year")
        assert len(result) == 1
        assert result[0][1]["human"] == 1

    def test_get_all_sorted_within_period(self, tmp_path):
        counter = _make_counter(tmp_path)
        now = datetime.now(timezone.utc).isoformat()
        counter._counts = {
            "/": {"human": [now]},
            "/blog/a.html": {"human": [now, now, now]},
            "/raindrops/b.html": {"human": [now, now]},
        }
        result = counter.get_all(period="today")
        totals = [sum(t.values()) for _, t in result]
        assert totals == sorted(totals, reverse=True)

    def test_migrated_entries_excluded_from_period_filter(self, tmp_path):
        stats_file = tmp_path / "stats.json"
        stats_file.write_text(json.dumps({"/": {"human": 10}}))
        counter = VisitCounter()
        counter.stats_file = stats_file
        counter._counts = counter._load()
        # Migrated entries have no real timestamp — should not appear in today's filter
        result = counter.get_all(period="today")
        assert result == []
