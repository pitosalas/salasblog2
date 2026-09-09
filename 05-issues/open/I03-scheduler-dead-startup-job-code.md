# I03 Scheduler's "run once at startup" job machinery is dead code

* **Symptom**: none user-visible — this is unreachable code, not a bug that
  causes incorrect behavior. `Scheduler._cleanup_startup_job()` and the
  `is_startup=True` branch of `_sync_wrapper()`/`_handle_sync_result()` are
  never actually invoked.

* **What tests have already been done**: found via code review while
  regenerating `01-literate/09-scheduler.md` (2026-09-09), then confirmed
  directly against `src/salasblog2/scheduler.py` with a grep across the
  whole package for any caller passing `is_startup=True`. None found.

* **Latest theory**:

  `_sync_wrapper()` accepts an `is_startup` flag and, when true, calls
  `_cleanup_startup_job()` in its `finally` block:

  ```python
  def _sync_wrapper(self, sync_type: str, is_startup: bool = False):
      ...
      finally:
          if is_startup:
              self._cleanup_startup_job(sync_type, operation)
  ```

  `_handle_sync_result()` also branches on `is_startup` purely to change a
  log message (`"Startup" if is_startup else "Scheduled"`). But
  `start_scheduler()` — the only place that schedules recurring calls to
  `_sync_wrapper()` — always passes `False`:

  ```python
  schedule.every(git_minutes).minutes.do(
      lambda: self._sync_wrapper("git", False)
  ).tag("git_sync")

  schedule.every(raindrop_minutes).minutes.do(
      lambda: self._sync_wrapper("raindrop", False)
  ).tag("raindrop_sync")
  ```

  Nothing else in the package calls `_sync_wrapper()`, `_handle_sync_result()`,
  or `_cleanup_startup_job()` at all. This suggests a "run the sync jobs once
  immediately at startup, then on the regular schedule" feature was
  designed (the parameter, the cleanup hook, the distinct log label all
  exist) but never wired up — `start_scheduler()` only ever registers the
  recurring jobs, so a fresh deploy waits for the first full interval
  (`git_sync_hours`/`raindrop_sync_hours`, currently 12h/12h per
  `fly.toml`) before the first sync ever runs.

  Two ways to resolve this: either wire up an actual startup-run call (if
  that was the intent), or delete `_cleanup_startup_job()` and the
  `is_startup` parameter entirely (if it's just aspirational and not
  wanted). Worth checking with the project owner which was intended before
  touching it, since removing it is a bigger call than it looks — it's the
  only piece of the sync path that runs any job immediately rather than
  waiting for the first scheduled interval.
