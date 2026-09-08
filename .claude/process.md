# General
* **No code without a task.**
* **No task without a feature.**
* **No feature contradicting the spec.**
* **After creating a feature + task file, stop and present the plan — no code until approved.**
* An unapproved feature parked after that stop does not block unrelated work elsewhere in the project — it just sits in `notdone/` until it's explicitly picked up.
* **Don't close a feature until its full test suite exists and passes.**
* Exception: simple bug fixes/refactors (no spec/behavior change) skip the feature/task pair — log as a chore.
* Any bug fix or regression gets a test.
* Switching between task/feature/chore: stop and ask permission first.
* Fix visible, low-risk follow-on inconsistencies from a change in the same pass — an unfilled template placeholder, a stale cross-reference, mismatched numbering — rather than pausing to ask permission for each one separately.

# chores
* One running file, `04-tasks/chores.md`: `- [ ] <what and why>` → `- [x]` when applied.

# features
* `FNN-<slug>.md` in `03-features/{notdone,done,deferred}/`.
* A mini-spec — scope/intent, not task detail.
* `Tasks File Created: yes` only once a matching `04-tasks/TFNN-*.md` exists. `template.md` shows the format.
* `Date Created:` in the header, absolute ISO `YYYY-MM-DD`, set when the file is first written and never changed afterwards — not even when the feature moves between `notdone`/`done`/`deferred`.

# tasks
* Full task list before any design/code.
* `TFNN-<slug>.md` (`NN` matches the feature) in `04-tasks/{notdone,done,deferred}/`.
* `template.md` shows the format.
* Each step is numbered `TFNN.N`, matching the file's own `TFNN` (e.g. `TF03.0`, `TF03.1`, ...), starting at `.0` — not a bare `T0N`.
* Each step's `**Status**` and `**Description**` are on separate lines, with a blank line between them.
* `Date Created:` in the header, absolute ISO `YYYY-MM-DD`, set when the file is first written and never changed afterwards.
* It is the task file's own creation date, which may be later than its feature's.
* Every step gets a test where feasible (else record why).
* Every feature gets a dedicated test-writing task.
* Task lists must never include a "regenerate literate docs" task — literate docs are refreshed later, at checkpoint, not as part of a feature's task list.
* Last task done → move the task file to `done/`, set the feature's Done/Tests Written/Test Passing to yes, move the feature file to `done/`.
* A repo-wide convention change (a new required header field, a renumbering scheme) applies retroactively to `done/`-archived feature and task files too, not just active `notdone/` ones, so the whole history stays on one convention.

# issues
* `05-issues/{open,closed,deferred}/`, numbered, follow the template.
* New → `open/`.
* Resolved or absorbed into a feature/task → `closed/`.
* Explicitly deferred → `deferred/`.

# writing .md files
* Applies to `03-features/`, `04-tasks/`, `05-issues/`, and any hand-written doc — not `01-literate/` (own prompt in `literate.md`).
* Blank line between paragraphs, always.
* Short paragraphs.
* Bullets for anything enumerable.
* **Bold** for key decisions.
* *Italics* for emphasis or naming a pattern.
* Several short, headed subsections beat one block.
* Each bullet is one statement, on its own line — don't join multiple rules with semicolons or periods into a single bullet.
* Applies every time a file is rewritten, not just on first authoring.
* Applies everywhere I write markdown in this project, even if this project's own copy of `.claude/` predates or omits a rule the canonical `j3` kit has since gained — a stale local copy is not license to write worse markdown.

# agent model selection
* Default subagent dispatch to haiku; upgrade only when the task needs judgment, not just data-gathering.
* **haiku** — file/log discovery, "where is X defined", dependency-closure scans, counting, formatting. Use the `explorer` agent (`.claude/agents/explorer.md`).
* **sonnet** — analysis, code review, writing, moderate reasoning, synthesis across subagent findings. Use the `reviewer` agent (`.claude/agents/reviewer.md`).
* **opus** — architecture decisions, novel debugging, cross-cutting design tradeoffs. Use the `architect` agent (`.claude/agents/architect.md`).

# bootstrap
* `.claude/bootstrap.md` is the scaffold spec.
* Run `/bootstrap` to bootstrap a new project — don't follow it ad hoc from a mention in conversation.
* Never copy `settings.local.json` when copying `.claude/` into a new project — it's machine-local and gitignored, and its permission entries (paths, per-machine allowances) don't generalize.
* If a project's `.claude/` predates the canonical `j3` kit's current state, flag it as stale and offer to sync, rather than silently working from the old copy.

# github
* Literate docs: apply `.claude/literate.md`'s prompt to each changed Python module, save as `01-literate/<module>.md`.
* Run tests and regenerate literate docs before committing/pushing.
* File headers stamp themselves: `.githooks/pre-commit` sets `Version`/`Created`/`Updated` on every staged `.py`.
* Never hand-edit those three fields — see the file-header rule in `.claude/style_guide.md`.
* The hook is only active once per clone: `git config core.hooksPath .githooks`.
* Without it headers silently stop updating, so check it after cloning.
* **No pull requests.**
* Single-developer repo: run the tests, commit, push.
* No review branch, no PR.
* That sequence belongs to `/checkpoint`, which runs tests and ruff, updates `current.md`, refreshes changed literate docs, then commits and pushes.
* Prefer it over doing the steps by hand.
* Commit or push only when asked, with a good message.
