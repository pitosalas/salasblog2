## Directory Layout
- Mirror the source tree: `test/foo/test_bar.py` corresponds to `src/foo/bar.py`.
- Use predictable names: `test_<module>.py` for unit tests; `<module>_integration_test.py` for integration tests.
- Keep shared utilities in `test/support/` or `test/conftest.py`.
- Separate integration tests into `test/integration/`.
## Test Naming and Structure
- Name tests by behavior, not implementation: `test_rejects_invalid_email()`.
- Follow Arrange–Act–Assert in every test.
- Keep each test focused on one behavior; multiple asserts allowed only when describing one conceptual outcome.
- Prefer pytest-style function tests over classes unless grouping is meaningful.
## Fixtures and Test Data
- Use pytest fixtures for setup; avoid deep fixture chains.
- Keep fixtures explicit and local unless widely reused.
- Use factories for complex objects; avoid large hardcoded dicts.
- Keep test data minimal and relevant to the behavior under test.
## Refactoring Rules
- Remove duplication aggressively: repeated setup → fixture; repeated assertions → helper.
- Extract intent-revealing helpers such as `assert_valid_user(user)`.
- Avoid mocks that expose implementation details; mock only external boundaries.
- Use parametrization for repeated input/output variations.
- Avoid over-abstraction; tests must remain concrete and readable.
## Determinism and Isolation
- Do not rely on external services; use mocks or local fakes.
- Control randomness with seeded RNGs or deterministic generators.
- Freeze time when needed using a time provider or library.
- Clean up side effects: temp dirs, environment variables, monkeypatches.
## Style and Readability
- Prefer direct assertions: `assert result == 3`.
- Keep tests short and intention-revealing.
- Inline small helpers when they improve clarity.
- Avoid cleverness; tests should read like documentation of behavior.
## Coverage and Intent
- Test public API only; private helpers are covered indirectly.
- Treat coverage as a signal, not a target.
- Add regression tests for every bug fix with a clear comment referencing the issue.
## Integration Tests
- Keep integration tests separate from unit tests.
- Use real components except for external boundaries.
- Keep integration tests fewer and targeted.
## Linting and Tooling
- Enable pytest-specific linting (e.g., ruff, flake8-pytest-style).
- Run tests in parallel to detect hidden statefulness.
- Use coverage reports to identify untested behavior.
