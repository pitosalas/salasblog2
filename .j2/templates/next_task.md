Feature ID: {{default_feature}}

If the task file `.j2/tasks/{{default_feature}}.md` does not exist, output: "Error: No task file for {{default_feature}}. Run `/tasks-gen {{default_feature}}` first." and stop.

Read the task file at `.j2/tasks/{{default_feature}}.md` directly. Find the first task whose `**Status**` is `not started` and implement it. You must follow the coding principles below exactly.

--- PRINCIPLES BEGIN ---
{{rules}}
--- PRINCIPLES END ---

After writing the code:
1. Update that task's `**Status**` to `done` in the task file.
2. Check whether **all** tasks in the file are now `done`.
   - If yes: run `mv .j2/tasks/{{default_feature}}.md .j2/tasks/done/{{default_feature}}.md` to archive it.
3. Briefly state which feature and task you worked on and what you built.
4. State what the developer should do next: run tests, then `/task-next` again, or `/milestone {{default_feature}}` if the feature is complete.
