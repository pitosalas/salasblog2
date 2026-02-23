You are adopting an existing project into the j2 framework. Perform all 6 steps below in order.

--- RULES BEGIN ---
{{rules}}
--- RULES END ---

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

## Step 5 — Merge .claude/ config

Add j2 slash commands to `.claude/commands/` without overwriting existing user files. If `.claude/CLAUDE.md` exists, append the j2 instructions block; otherwise create it. Do not remove any existing content.

## Step 6 — Leave README untouched

Do not modify README.md or any existing documentation files.

After all steps, report what was created/modified and suggest running `/refresh` next.
