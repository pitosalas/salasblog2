# Code Review Checklist

Version: 4.1 — universal Python review guide.

`MUST` blocks unless waived in the task/PR. `SHOULD` = expected default.
`CONSIDER` = review prompt, not a mechanical rule. Prefer a linter/type-checker
for mechanical items (line length, imports, quotes, unused names) and spend
human review on the judgment items below.

## Process
- No code without a matching feature + task file; no task file without a feature.
- Update feature/task status when work completes or defers.
- Resolve or document mismatches between `02-doc/current.md` and the
  feature/task/issue files before relying on either.
- Run relevant tests; commit only when requested.
- Before a PR: regenerate `01-literate/<module>.md` for each changed source file.

## Errors — report, don't guess and "fix"
On something wrong or unexpected, raise or warn — never infer intent and
"correct" it. A guess-and-repair hides a real bug or invents new wrong
behavior; if the bad value is ours, fix it at the source.

**MUST**
- Don't compensate for a violated expectation by coercing, defaulting, or
  branching to "make it work".
- On a problem, raise with context; never return the bad value or a silent
  fallback; never swallow with `except: return None` / `continue`.
- Validate once at each boundary (user input, config, hardware, external APIs),
  then trust the value.
- No bare `except Exception:` or silent `except X: pass`.
- Bug fixes include a regression test unless the case is hardware-only.
- Persisted-format changes preserve old files or ship migration/defaults.

## Correctness
**MUST**
- No side effects at import time. No mutable default arguments.
- Keep pure logic free of framework/hardware imports; isolate those in adapters.
- Runtime-only, hardware, and physical-motion tests are marked manual and kept
  out of the plain test run.
- No secrets in code or config; sensitive values come from env/untracked config;
  logs never expose secrets or PII.

## Imports & packaging
**MUST**
- Absolute imports only; no relative imports; no wildcard or unused imports.
- Every `.py` starts with `#!/usr/bin/env python3`.

**SHOULD**
- All imports at the top, sorted consistently.
- Runtime deps declared in the right package metadata.

## Naming & style
**MUST**
- File header, in this order: module name and one-line description,
  `Author: <name>`, `Version: <n>`, `Created: <date>`, `Updated: <date>`,
  `Open Source Under MIT license`.

```python
#!/usr/bin/env python3
# ups_status — INA219 UPS driver and voltage-based state-of-charge estimator
# Author: Pito Salas
# Version: 3
# Created: 2026-04-12
# Updated: 2026-08-29
# Open Source Under MIT license
```

**Do not hand-edit `Version`, `Created`, or `Updated`.** The `.githooks/pre-commit`
hook stamps all three on every staged `.py` and re-stages the file, so a
hand-written value is overwritten at the next commit anyway. Writing a new file
without these three lines is fine — the hook inserts them below `Author`.

What the hook guarantees:

- `Version` is a **plain integer starting at 1**, incremented by exactly one per
  commit that changes the file — not per edit. Several edits before a single
  commit are one bump. It is *not* semver and carries no API-compatibility
  meaning.
- `Created` is written once, on the first commit that stamps the file, and never
  rewritten after — so it survives renames and moves.
- `Updated` is the date of the commit that last changed the file.
- Both dates are absolute ISO `YYYY-MM-DD` — never relative, never a bare year.
- A commit that does not touch a file leaves that file's header alone.
- A file with no `Author:` line is skipped with a warning, never guessed at.

`Version` and `Created` are carried forward from the file itself rather than
derived from `git rev-list`/`git log`, because neither follows renames reliably.
- No `from __future__ import annotations`.
- No leading-underscore prefix on any custom identifier.
- Line length <= 88 unless a longer line is materially clearer.
- Fields self-explanatory without surrounding code — no bare `xy`/`data`/`info`/
  `params`; spell out the meaning (`world_xy`, `map_data`, `tuning`).
- f-strings for formatting.

**SHOULD**
- Double quotes; single only when required.
- `X | None`, not `Optional[X]`.
- Booleans named `is_x` / `has_x` / `can_x`.
- No single-letter names except loop counters `i`, `j`.
- Put units in names (`dist_to_robot_m`, `clearance_cells`); document non-obvious
  encodings inline.
- `is` / `is not` for `None` / `True` / `False`; `enumerate()` over manual counters.

## Design
Numeric limits below are smells, not laws — they flag a function doing too much,
not a hard cap.

**MUST**
- Bias to less code. Before writing any, ask "is this needed?" — not writing it
  beats adding it. No speculative error handling, recovery, defaults, config, or
  abstraction the spec doesn't require; every guard must catch a real, reachable
  case.
- Functions <= ~50 lines, files <= ~300 lines where practical.
- Avoid if/else nesting > 1 deep and if-chains > 3 branches; extract helpers,
  return early, or use a lookup table. Extraction for branching or naming beats
  the "no tiny methods" rule.
- Avoid 1-2 line methods unless they are properties, protocol/boundary adapters,
  or genuinely improve naming.
- No duplicated logic (DRY): actively scan bodies for identical/near-identical
  method bodies, repeated 3+ line sequences, and repeated construction patterns;
  extract a helper when found.

**CONSIDER**
- <= 3 behavioral args; group travelling params into a dataclass/config.
- Defaults fine in dataclasses/config/CLI/public APIs; avoid hidden behavioral
  defaults in internal logic.
- Minimal public API; no god methods, feature envy, or unrelated responsibilities
  in one class.
- No features not required by the current spec.

## Web assets (CSS / JS / HTML)
Applies to any project with a UI layer (Streamlit, Flask, Dash, etc.).

**MUST**
- No inline CSS, JavaScript, or HTML template strings inside Python source
  files — CSS/JS/HTML live in their own files, loaded at runtime.
- Load asset files via `Path(__file__).parent / "filename"` and pass the
  content to the framework.

**SHOULD**
- One CSS file per module that needs custom styles; shared styles go in a
  shared asset file.

## Comments & types
**MUST**
- Any complicated/obscure function explains what it does and its inputs/outputs —
  in the docstring. That is the one place for a fuller explanation; it does not
  license narrative comment blocks in the body.
- No multi-line narrative comment blocks in code. A comment is a short "why",
  not prose; long rationale goes to the docstring or `01-literate/`.

**SHOULD**
- A module-level docstring below the file header states the file's purpose and
  its key algorithms/design (e.g. states, invariants, non-obvious decisions), so
  the file is understandable from the top without reading the code.
- Obvious methods need no docstring; complex ones explain why the mechanism
  exists and any non-obvious pre/postconditions.
- Comments explain why, not what; one or two lines each; no task/fix references.
- Annotate non-obvious parameter and return types; prefer simple annotations,
  precise collection types only when they prevent caller ambiguity.

## Tests
**SHOULD**
- Every public method has a test where practical; cover edge cases (empty, `None`,
  boundaries).
- Behavior explained by a comment has a test encoding it.
- Isolate/mock external APIs, hardware, filesystem, time, and runtime graph deps.
- Test output dirs are git-ignored; no commented-out tests.
- Manual test notes record command, setup, expected observation, actual result.

## Runtime quality
**MUST**
- No unreachable/commented-out code, debug prints, or breakpoints.

**SHOULD**
- Context managers for files/resources needing cleanup.
- Logging (not `print`) for runtime errors in library/service modules.
- No blocking I/O, model loading, or expensive setup in hot loops; avoid repeated
  large allocations there.
- Optional outputs skip work when no consumer is listening.
- Use the framework's concurrency model; make shutdown deterministic.
- Lifecycle components release threads, timers, pub/sub, and hardware cleanly.
