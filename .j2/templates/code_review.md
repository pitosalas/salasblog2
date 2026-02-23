You are performing a code review of this project against its coding rules.

--- RULES BEGIN ---
{{rules}}
--- RULES END ---

Read every source file listed below, then check each against every rule above.

**Files to review:**
- `.j2/runner.py`
- `scaffold/install.sh`
- `tests/test_runner.py`
- `tests/test_commands.py`
- All files in `.claude/commands/`
- All files in `scaffold/.claude/commands/`

For each violation found, output one task in this exact format:

### T## — <short title>
**File**: `<relative path>`
**Rule**: <exact rule text that is violated>
**Fix**: <specific change required — be concrete, name the function/line if possible>

Group violations by file. Number tasks sequentially starting from T01.

If a file has no violations, skip it.

After all violations, output a one-line summary: how many files reviewed, how many violations found.

Do not suggest changes beyond what the rules require. Do not flag style opinions not covered by the rules.
