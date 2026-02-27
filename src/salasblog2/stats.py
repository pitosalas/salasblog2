#!/usr/bin/env python3
# stats.py — Visit counter persisting per-path, per-visitor-type counts to JSON
# Author: Pito Salas and Claude Code
# Open Source Under MIT license

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class VisitCounter:
    def __init__(self):
        data_dir = Path("/data")
        if data_dir.exists() and data_dir.is_dir():
            self.stats_file = data_dir / "stats.json"
        else:
            self.stats_file = Path("stats.json")
        self._counts: dict = self._load()

    def _load(self) -> dict:
        """Load counts from file, migrating old int-per-path format if needed."""
        try:
            if self.stats_file.exists():
                raw = json.loads(self.stats_file.read_text(encoding="utf-8"))
                return {
                    path: ({"human": val} if isinstance(val, int) else val)
                    for path, val in raw.items()
                }
        except Exception as e:
            logger.warning(f"Could not load stats file: {e}")
        return {}

    def _save(self):
        self.stats_file.write_text(
            json.dumps(self._counts, indent=2), encoding="utf-8"
        )

    def increment(self, path: str, visitor_type: str):
        """Increment visit count for path and visitor type."""
        if path not in self._counts:
            self._counts[path] = {}
        self._counts[path][visitor_type] = self._counts[path].get(visitor_type, 0) + 1
        self._save()

    def get(self, path: str) -> int:
        """Return total visit count across all visitor types for path."""
        return sum(self._counts.get(path, {}).values())

    def get_all(self) -> list[tuple[str, dict]]:
        """Return all paths with their type breakdown, sorted by total count descending."""
        return sorted(
            self._counts.items(),
            key=lambda x: sum(x[1].values()),
            reverse=True,
        )


_counter: VisitCounter | None = None


def get_counter() -> VisitCounter:
    global _counter
    if _counter is None:
        _counter = VisitCounter()
    return _counter
