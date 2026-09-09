# I02 VisitCounter has a read/write race and no cross-process file lock

* **Symptom**: none observed yet in production. Two latent issues in
  `src/salasblog2/stats.py`'s `VisitCounter`:

  1. A possible `RuntimeError: dictionary changed size during iteration` if a
     stats-page read happens at the same moment as a visit being recorded.
  2. If the app ever runs as more than one process sharing the same
     `stats.json` file (multiple Fly.io machines, multiple uvicorn workers),
     the last process to flush silently overwrites whatever another process
     already wrote — no data is merged, no error is raised.

* **What tests have already been done**: found via code review while
  regenerating `01-literate/02-stats.md` (2026-09-09), then confirmed
  directly against `src/salasblog2/stats.py`. Not reproduced under load —
  this requires a real concurrent-access race to trigger, which is timing-
  dependent and hasn't been observed live.

* **Latest theory**:

  `increment()` and `flush()` both take `self._lock` before touching
  `self._counts`:

  ```python
  def increment(self, path: str, visitor_type: str):
      with self._lock:
          if path not in self._counts:
              self._counts[path] = {}
          ...

  def flush(self):
      with self._lock:
          if not self._dirty:
              return
          self.stats_file.write_text(json.dumps(self._counts, indent=2), ...)
  ```

  But `get()` and `get_all()` — used to render the stats page — iterate
  `self._counts` **without** taking the lock:

  ```python
  def get(self, path: str) -> int:
      return sum(len(v) for v in self._counts.get(path, {}).values())

  def get_all(self, period: str | None = None) -> list[tuple[str, dict]]:
      ...
      for path, types in self._counts.items():
          ...
  ```

  `increment()` runs on every page visit, potentially from a different
  request-handling thread/task than whatever renders the stats page. If
  `increment()` adds a brand-new `path` key to `self._counts` (a first-ever
  visit to some URL) at the same moment `get_all()` is iterating
  `self._counts.items()`, Python raises `RuntimeError: dictionary changed
  size during iteration`. This is a classic unguarded-read-while-writing
  race — the fix is either taking `self._lock` in `get()`/`get_all()` too,
  or iterating over a snapshot (`dict(self._counts)`) instead of the live
  dict.

  Separately, `flush()` writes `stats.json` with a plain `Path.write_text()`
  — no `flock`/advisory file lock, and no read-merge-write cycle. This is
  fine for a single long-lived process (the current deployment, per
  `current.md`), but would silently lose data under any future multi-process
  or multi-machine deployment, since each process holds its own independent
  in-memory `self._counts` and the last one to flush simply clobbers the
  file.
