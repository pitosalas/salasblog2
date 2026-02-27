"""
Simple visit counter that persists page counts to a JSON file.
Uses /data/stats.json in production (Fly.io volume), stats.json locally.
"""
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
        try:
            if self.stats_file.exists():
                return json.loads(self.stats_file.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning(f"Could not load stats file: {e}")
        return {}

    def _save(self):
        try:
            self.stats_file.write_text(
                json.dumps(self._counts, indent=2), encoding="utf-8"
            )
        except Exception as e:
            logger.warning(f"Could not save stats file: {e}")

    def increment(self, path: str):
        self._counts[path] = self._counts.get(path, 0) + 1
        self._save()

    def get(self, path: str) -> int:
        return self._counts.get(path, 0)

    def get_all(self) -> list[tuple[str, int]]:
        """Return all counts sorted by visit count descending."""
        return sorted(self._counts.items(), key=lambda x: x[1], reverse=True)


_counter: VisitCounter | None = None


def get_counter() -> VisitCounter:
    global _counter
    if _counter is None:
        _counter = VisitCounter()
    return _counter
