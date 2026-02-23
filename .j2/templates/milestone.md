You are helping a developer close out a completed feature.

A milestone means the feature is done: implemented, tested, passing, and cleaned up.

The project coding rules define what "done" means. Check each one applies:

--- RULES BEGIN ---
{{rules}}
--- RULES END ---

Before writing the summary, check the task list below. If any task is `not started` or `in progress`, do NOT declare a milestone — list the incomplete tasks and stop.

--- FEATURE BEGIN ---
{{feature}}
--- FEATURE END ---

--- TASKS BEGIN ---
{{tasks}}
--- TASKS END ---

When all tasks are done, write a milestone summary:
1. **Feature completed** — which feature and what was built.
2. **Rules compliance** — confirm every rule is satisfied. List any that are not.
3. **Quality checklist** — cleanup, refactoring, loose ends.
4. **Updated feature status** — in a fenced code block:

```
## FXX — Feature Name
**Priority**: <priority>
**Status**: done | Tests written: yes | Tests passing: yes
**Description**: <existing description unchanged>
```

5. **What's next** — next feature or task.

If any rule is not satisfied, do NOT declare a milestone — list what must be done first.

When all checks pass and the milestone is granted:

**1. Archive the task file (if not already archived):**

Check whether `.j2/tasks/{{feature_id}}.md` exists. If it does, run:

```bash
mv .j2/tasks/{{feature_id}}.md .j2/tasks/done/{{feature_id}}.md
```

If already in `.j2/tasks/done/{{feature_id}}.md`, skip this step.

**2. Reorder the feature entry in `features.md`:**

The file has two sections (incomplete top, completed bottom), each sorted High → Medium → Low.

- Remove the feature's full entry block (from `## FXX —` through the closing `---`) from the incomplete section.
- Insert into the completed section at the correct priority position.
- If the completed section is empty, insert after the `<!-- ===== COMPLETED FEATURES ... -->` comment.

**3. Update `README.md`:**

Read the current `README.md` (if it exists), the spec files in `.j2/specs/`, and the completed feature list. Rewrite `README.md` to reflect the current state of the project — what it does, how to use it, and what has been built. The README should be open-source worthy: clear, accurate, and genuinely useful to someone encountering the project for the first time. Preserve any sections that are still accurate; improve or replace anything that is stale or incomplete.
