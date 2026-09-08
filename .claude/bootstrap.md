# Bootstrap Scaffold

When bootstrapping a new project, assume that you are inside the directory of the target. Check .claude folder is there and correct. Then create the following files and folders exactly as specified below.

## Folder structure to create

```
LICENSE
README.md
.gitignore
CLAUDE.md
Makefile
01-literate/
02-doc/
  spec.md
  current.md
  history.md
  notes.md
03-features/
  notdone/
  done/
  deferred/
  template.md
04-tasks/
  notdone/
  done/
  deferred/
  chores.md
  template.md
05-issues/
  open/
  closed/
  deferred/
  template.md
.githooks/
  pre-commit
```
### LICENSE
Copy from `.claude/templates/LICENSE.template` and replace `<YEAR>` and `<AUTHOR NAME>`.

### README.md
Copy from `.claude/templates/README.md.template` and replace `<APP NAME>` and other placeholders.

### .gitignore
Copy from `.claude/templates/.gitignore.template` as-is.

### CLAUDE.md
Copy from `.claude/templates/CLAUDE.md.template` and replace `<APP NAME>`.

### Makefile
Copy from `.claude/templates/Makefile.template` and replace `<APP NAME>` in
the header comment and `<RUN COMMAND>` in the `run` target with the app's
actual run command (e.g. `uv run bg server`, `npm start`). Provides
`make setup|fmt|lint|test|check|run` as the standard entrypoints — `setup`
runs `uv sync`, `test` runs `uv run pytest`, `fmt`/`lint` run `uv run ruff`
scoped to changed files only (see the template's own header for why), `check`
is `fmt`+`lint`+`test`, and `run` execs the app directly — no separate script,
the command lives in the Makefile itself. README.md.template and
CLAUDE.md.template both point here rather than spelling out raw commands, so
this is the one place the actual invocations live.

### .githooks/pre-commit
Copy from `.claude/templates/pre-commit.template` as-is, then
`chmod +x .githooks/pre-commit`. It stamps `Version`/`Created`/`Updated` into
the header of every staged `.py`, as required by the file-header rule in
`.claude/style_guide.md`.

Git will not use it until the repo is pointed at the directory — see step 1 of
"After scaffolding". `.git/hooks` is not version controlled, which is why the
hook is tracked here instead.

## After scaffolding

Prompt the user to:
1. Activate the header-stamping hook — a one-time local config, needed once per
   clone, that nothing else will do automatically:

   ```bash
   git config core.hooksPath .githooks
   ```

   Without it the hook is inert and headers silently stop updating, with no
   error to notice.
2. Fill in `02-doc/spec.md` with the app description
3. Initialize `02-doc/current.md` as the session handoff file — keep it to just
   an `## Open` section (what's in progress/next); when work is marked done,
   move that entry out of `current.md` into `02-doc/history.md` rather than
   letting it accumulate in the always-read file
4. Create `02-doc/history.md` with a one-line header (e.g. "# History") — it
   starts empty and only grows as work is marked done
5. Add any durable architecture notes to `02-doc/notes.md`
6. Replace `<APP NAME>` in `CLAUDE.md`, `README.md`, `Makefile`, and `LICENSE`
   with the actual app name, author, and year; replace `<RUN COMMAND>` in
   `Makefile` with the app's actual run command
7. Fill in `settings.json`'s `autoMode.environment` block with the real project
   purpose, package manager, the `make test`/`make run` commands, and source
   control location
8. Define the first feature and matching task file before writing any code
