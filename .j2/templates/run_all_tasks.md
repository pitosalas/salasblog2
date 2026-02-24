Feature ID: {{feature_id}}

If the task file `.j2/tasks/{{feature_id}}.md` does not exist, output: "Error: No task file for {{feature_id}}. Run `/tasks-gen {{feature_id}}` first." and stop.

Read the task file at `.j2/tasks/{{feature_id}}.md`. Implement every task whose `**Status**` is `not started`, in order. For each task:
1. Write the code following the principles below.
2. Update that task's `**Status**` to `done` in the task file.
3. Move immediately to the next not-started task.

After all tasks are done, run `pytest` and report results. Do not modify `features.md`, `state.md`, or `README.md`. End with a summary of what was implemented and suggest running `/milestone {{feature_id}}`.

--- PRINCIPLES BEGIN ---
{{rules}}
--- PRINCIPLES END ---
