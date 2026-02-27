You are adopting an existing project into the j2 framework.

--- RULES BEGIN ---
{{rules}}
--- RULES END ---

## Re-run Detection

Before doing anything else, check whether `.j2/runner.py`, `.j2/config/`, and `.j2/templates/` all exist in the project root.

**If all three exist** → j2 is already installed. Switch to **surgical update mode** (steps A–C below) and skip steps 1–6.

**If any are missing** → j2 is not yet installed. Proceed with the normal **first-run steps 1–6** below.

---

## Surgical Update Mode (re-run only)

Run these three steps, then output a summary and stop.

### A — Update infrastructure files

Copy `.j2/runner.py` from the j2 dev repo's master copy over the project's existing `.j2/runner.py`.
Run `rsync -a --update .j2/templates/ <project>/.j2/templates/` and `rsync -a --update .j2/config/ <project>/.j2/config/` to bring templates and config up to date without overwriting newer local files.

### B — Merge new slash commands

For each `.md` file in `.claude/commands/`, copy it to the project's `.claude/commands/` only if that file does not already exist there. Never overwrite existing command files.

### C — Output update summary

List exactly which files were updated or added, and confirm that `specs/`, `features/`, `tasks/`, `rules.md`, and `README.md` were left untouched. Suggest running `/refresh` to re-orient.

---

## First-Run Steps (new adoption only)

Perform all 6 steps below in order.

## Step 1 — Scan and configure settings.yaml

Scan the project root for marker files (package.json, Cargo.toml, pyproject.toml, CMakeLists.txt, go.mod, etc.) to detect language, platform, and project name. Write or update `.j2/config/settings.yaml` with the detected values. Create `.j2/config/`, `.j2/specs/`, `.j2/features/`, `.j2/tasks/`, and `.j2/templates/` directories if missing.

## Step 2 — Generate draft spec

Scan source files, README, and any existing docs. Generate a draft spec at `.j2/specs/<project-name>.md` describing what the project does, its architecture, dependencies, and key modules. Present the spec in a fenced code block for review.

## Step 3 — Generate features.md

Analyze existing code to identify implemented features. Generate `.j2/features/features.md` using the standard format. Mark features with working code and passing tests as `done`. Run `python3 -m pytest tests/ -v 2>&1 || true` to detect test status. Features without tests: `Tests written: no`.

## Step 4 — Merge .gitignore

Read the project's `.gitignore` (create if missing). Append j2 entries if not already present:
```
# j2 framework
.j2/state.md
.coverage
```

## Step 5 — Merge .claude/CLAUDE.md

Slash commands are already installed by `install.sh`. Only handle CLAUDE.md: if `.claude/CLAUDE.md` already exists, append the j2 instructions block below (only if not already present); otherwise create it with that content. Do not touch `.claude/commands/` or any other existing `.claude/` files.

j2 instructions block:
```
This project uses the j2 framework. Run `/refresh` to get oriented, or `/continue` to pick up where you left off.

Coding rules are in `.j2/rules.md`. Project spec is in `.j2/specs/`. Current state is in `.j2/state.md`.
```

## Step 6 — Leave README untouched

Do not modify README.md or any existing documentation files.

After all steps, report what was created/modified and suggest running `/refresh` next.
