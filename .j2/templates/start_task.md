Feature ID: {{feature_id}}

If the task file `.j2/tasks/{{feature_id}}.md` does not exist, output: "Error: No task file for {{feature_id}}. Run `/tasks-gen {{feature_id}}` first." and stop.

Read the task file at `.j2/tasks/{{feature_id}}.md` directly. Find the first task whose `**Status**` is `not started` and implement it. You must follow the coding principles below exactly.

--- PRINCIPLES BEGIN ---
{{rules}}
--- PRINCIPLES END ---

After writing the code:
1. Update that task's `**Status**` to `done` in the task file.
2. Briefly explain what you implemented and any decisions you made.
3. State what the developer should do next (run tests, then `/task-start` again or `/milestone` if the feature is complete).
