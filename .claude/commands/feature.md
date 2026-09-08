---
allowed-tools: Read Write Glob
---
Create a new feature and its matching task file for: $ARGUMENTS

1. Read `02-doc/spec.md`. If the request contradicts or isn't covered by the
   spec, stop and say so instead of creating files.
2. Scan `03-features/{notdone,done,deferred}/` for existing `FNN-*.md` files and
   `04-tasks/{notdone,done,deferred}/` for `TFNN-*.md` files. Take the highest
   `NN` found across both, add 1, zero-pad to two digits. Start at `01` if none
   exist.
3. Pick a short kebab-case slug from the request.
4. Copy `templates/feature-template.md` to `03-features/notdone/FNN-<slug>.md`. Fill in
   the feature number, priority, description, and demo steps — do not leave
   template placeholders unfilled. Set `Tasks File Created: yes`.
5. Copy `templates/task_template.md` to `04-tasks/notdone/TFNN-<slug>.md`. Break the
   feature into concrete, testable steps per `.claude/process.md`'s tasks rules:
   every step gets a test where feasible (record why when not), include a
   dedicated test-writing task, and never include a "regenerate literate docs"
   task.

**Process gate:** After both files are created, stop and present the plan. Do
not write any code or content until the user gives explicit approval to
proceed.
