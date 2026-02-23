You are helping a developer save their current working context so they can resume later.

Write a concise `current.md` file capturing the state of the session. Include:

1. **What was just completed** — brief description of what was done since the last checkpoint or milestone.
2. **What is currently in progress** — the feature or task being actively worked on, and where things stand.
3. **What is next** — the immediate next steps when resuming.
4. **Open questions** — anything unresolved that needs a decision.
5. **Feature status summary** — a compact table of each feature's current status.

Keep it short enough to scan in under a minute. This is a working note, not documentation.
Output the content of `current.md` only — no explanation.

After outputting the content, write it to `.j2/current.md`, overwriting any existing file.

Before committing, sync feature statuses:

1. For each feature in `features.md` whose `**Status**` is not `done`, check its task file at `.j2/tasks/<feature-id>.md`.
2. If the task file exists and every task in it has `**Status**: done`, run `pytest` and update that feature's `**Status**` line in `features.md` to: `done | Tests written: yes | Tests passing: yes` (or `no` based on results).
3. If the task file has been archived to `.j2/tasks/done/<feature-id>.md`, treat all tasks as done and apply the same update.

Then commit and push all current changes:

1. Run `git add -A` to stage everything.
2. Run `git diff --cached --stat` to see what changed.
3. Write a one-line commit message that summarizes those changes (e.g. "implement F03 T02: add template rendering" or "fix load_spec warning for empty specs/"). Do not use generic messages like "checkpoint" or "wip".
4. Run `git commit -m "<your message>"`.
5. Run `git push`. If it fails because no upstream is set, run `git push --set-upstream origin $(git branch --show-current)` instead.

--- LAST STATE BEGIN ---
{{state}}
--- LAST STATE END ---

--- FEATURES BEGIN ---
{{features}}
--- FEATURES END ---
