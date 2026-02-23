Feature ID: {{feature_id}}

Output ONLY the following line and nothing else, then stop and wait for the user's input:

`Refinement request: `

Once you have the request, read the task file at `.j2/tasks/{{feature_id}}.md` and apply the requested changes.

The project coding rules are below. Ensure the updated task list stays consistent with these rules (e.g. if rules require tests, there must be at least one test task).

--- RULES BEGIN ---
{{rules}}
--- RULES END ---

The full feature list is below for context.

--- FEATURES BEGIN ---
{{features}}
--- FEATURES END ---

Apply the developer's requested changes and output the complete updated task list in the same format. Preserve the `**Status**` field on each task exactly as it appears. Do not make changes beyond what was requested.
