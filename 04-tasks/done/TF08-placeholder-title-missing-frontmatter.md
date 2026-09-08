# TF08 — Placeholder Title for Missing Frontmatter
**Date Created:** 2026-02-22

## TF08.0 — Fix test API mismatch: remove theme kwarg from SiteGenerator calls
**Status**: done

**Description**: All tests in `test_placeholder_title.py` and `test_verify_placeholder_fix.py` call `SiteGenerator(theme="test")` but `SiteGenerator.__init__()` takes no parameters. Remove the `theme="test"` argument from every test call so instantiation succeeds. The placeholder title logic already exists in `generator.py` at line 90.

## TF08.1 — Verify placeholder title logic handles all test cases
**Status**: done

**Description**: After fixing the constructor call, run `uv run pytest tests/test_placeholder_title.py -v` and confirm all 5 tests pass. Check that `load_posts` returns `"placeholder title: <Title Cased Filename>"` when `title` is absent from frontmatter, and the real title when it is present.

## TF08.2 — Fix test_verify_placeholder_fix and confirm all F08 tests green
**Status**: done

**Description**: Run `uv run pytest tests/test_placeholder_title.py tests/test_verify_placeholder_fix.py -v` and confirm all 6 tests pass. Update features.md to mark F08 done.
