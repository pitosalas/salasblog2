Output ONLY the following line and nothing else, then stop and wait for the user's input:

`Refinement request: `

After the user responds, apply their requested changes to the feature list following the instructions below.

The project coding rules are below. When applying changes, ensure the result stays consistent with these rules (e.g. if rules require tests, every feature must be testable).

--- RULES BEGIN ---
{{rules}}
--- RULES END ---

The current feature list is below. The developer may ask you to:
- Add a new feature
- Remove a feature
- Change the priority of a feature
- Split a feature into two
- Merge two features into one
- Rewrite a feature description

Apply the requested changes and output the complete updated feature list in the same format.
Preserve the status values legend at the top of the output exactly as it appears in the input.
Do not make changes beyond what was requested.

**Two-section invariant**: Always write `features.md` with exactly two sections in this order:
1. Incomplete features (status `not started` or `in progress`), sorted High → Medium → Low priority.
2. Completed features (status `done`), sorted High → Medium → Low priority.
Use the HTML comment markers `<!-- ===== INCOMPLETE FEATURES (High → Medium → Low) ===== -->` and `<!-- ===== COMPLETED FEATURES (High → Medium → Low) ===== -->` to delimit the sections. This ordering must be maintained on every write regardless of what was changed.

**Auto-task-gen**: After outputting the updated feature list, compare the new feature IDs against those in `--- CURRENT FEATURES BEGIN ---` below. For each feature ID that is newly added (not present in the current list), generate a task file at `.j2/tasks/<FID>.md` using the same format and rules as `/tasks-gen`: concrete actionable tasks, T01/T02/… IDs, all statuses `not started`, consistent with the coding rules. Write each file directly — do not display the task list in the console, just confirm with one line per file: `Written: .j2/tasks/<FID>.md (N tasks)`. If no new features were added, skip this step entirely.

--- CURRENT FEATURES BEGIN ---
{{features}}
--- CURRENT FEATURES END ---
