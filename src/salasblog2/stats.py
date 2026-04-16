#!/usr/bin/env python3
# stats.py — Visit counter persisting per-path, per-visitor-type counts to JSON
# Author: Pito Salas and Claude Code
# Open Source Under MIT license

import json
import logging
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


def _period_start(period: str | None) -> datetime | None:
    """Return the UTC datetime at the start of the requested period, or None for all-time."""
    if period is None:
        return None
    now = datetime.now(timezone.utc)
    if period == "today":
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    if period == "this_week":
        return (now - __import__('datetime').timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    if period == "this_month":
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if period == "this_year":
        return now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    return None


FLUSH_INTERVAL_SECONDS = 60

class VisitCounter:
    def __init__(self):
        data_dir = Path("/data")
        if data_dir.exists() and data_dir.is_dir():
            self.stats_file = data_dir / "stats.json"
        else:
            self.stats_file = Path("stats.json")
        self._counts: dict = self._load()
        self._dirty = False
        self._lock = threading.Lock()
        self._start_flush_thread()

    def _load(self) -> dict:
        """Load counts from file, migrating old formats if needed.

        Storage format:
          { path: { visitor_type: [ iso_timestamp, ... ], ... }, ... }

        Legacy formats accepted:
          { path: int }                         -> migrated to {"human": []}
          { path: { visitor_type: int } }       -> migrated to {"visitor_type": []}
        """
        try:
            if self.stats_file.exists():
                raw = json.loads(self.stats_file.read_text(encoding="utf-8"))
                migrated = {}
                for path, val in raw.items():
                    if isinstance(val, int):
                        # oldest format: bare count
                        migrated[path] = {"human": ["migrated"] * val}
                    elif isinstance(val, dict):
                        upgraded = {}
                        for vtype, vval in val.items():
                            if isinstance(vval, int):
                                # middle format: {type: count}
                                upgraded[vtype] = ["migrated"] * vval
                            else:
                                upgraded[vtype] = vval
                        migrated[path] = upgraded
                    else:
                        migrated[path] = val
                return migrated
        except Exception as e:
            logger.warning(f"Could not load stats file: {e}")
        return {}

    def _start_flush_thread(self):
        """Start background thread that flushes dirty stats to disk periodically."""
        def flush_loop():
            while True:
                time.sleep(FLUSH_INTERVAL_SECONDS)
                self.flush()
        t = threading.Thread(target=flush_loop, daemon=True)
        t.start()

    def flush(self):
        """Write stats to disk if there are pending changes."""
        with self._lock:
            if not self._dirty:
                return
            try:
                self.stats_file.write_text(
                    json.dumps(self._counts, indent=2), encoding="utf-8"
                )
                self._dirty = False
            except Exception as e:
                logger.warning(f"Could not save stats: {e}")

    def _save(self):
        """Mark stats as dirty — actual write happens in background flush thread."""
        self._dirty = True

    def increment(self, path: str, visitor_type: str):
        """Record a visit for path and visitor type with current UTC timestamp."""
        with self._lock:
            if path not in self._counts:
                self._counts[path] = {}
            if visitor_type not in self._counts[path]:
                self._counts[path][visitor_type] = []
            self._counts[path][visitor_type].append(
                datetime.now(timezone.utc).isoformat()
            )
            self._dirty = True

    def get(self, path: str) -> int:
        """Return total visit count across all visitor types for path."""
        return sum(len(v) for v in self._counts.get(path, {}).values())

    def get_all(self, period: str | None = None) -> list[tuple[str, dict]]:
        """Return all paths with their type breakdown, sorted by total count descending.

        If period is given (today/this_week/this_month/this_year) only visits
        on or after the period start are counted.  period=None means all-time.

        Returns list of (path, {visitor_type: count}) tuples.
        """
        cutoff = _period_start(period)

        result = []
        for path, types in self._counts.items():
            counts = {}
            for vtype, timestamps in types.items():
                if cutoff is None:
                    counts[vtype] = len(timestamps)
                else:
                    counts[vtype] = sum(
                        1 for ts in timestamps
                        if ts != "migrated" and _parse_ts(ts) >= cutoff
                    )
            total = sum(counts.values())
            if total > 0:
                result.append((path, counts))

        return sorted(result, key=lambda x: sum(x[1].values()), reverse=True)


def _parse_ts(ts: str) -> datetime:
    """Parse an ISO timestamp string into an aware datetime."""
    try:
        return datetime.fromisoformat(ts)
    except Exception:
        return datetime.min.replace(tzinfo=timezone.utc)


_counter: VisitCounter | None = None


def get_counter() -> VisitCounter:
    global _counter
    if _counter is None:
        _counter = VisitCounter()
    return _counter
