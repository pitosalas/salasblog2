---
allowed-tools: Read Edit Glob Bash(mv *)
---
Close out feature: $ARGUMENTS (an `NN` or `FNN`)

1. Find `03-features/notdone/FNN-*.md` and `04-tasks/notdone/TFNN-*.md` for that
   number. If either is missing, stop and report it.
2. Confirm every task in the `TFNN` file is marked done. If any are not, stop
   and list what's outstanding instead of closing.
3. Confirm a full test suite exists for the feature and run it. If tests are
   missing or failing, stop — per `.claude/process.md`, a feature is not closed
   until its full test suite exists and passes.
4. Move the task file from `04-tasks/notdone/` to `04-tasks/done/`.
5. On the feature file, set `Done: yes`, `Tests Written: yes`, `Test Passing: yes`.
6. Move the feature file from `03-features/notdone/` to `03-features/done/`.

Report what moved and what tests ran.
