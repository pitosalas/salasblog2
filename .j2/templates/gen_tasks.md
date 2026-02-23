Feature ID: {{feature_id}}

Generate or update the task list for this feature following the instructions below.

You must follow these coding principles when generating tasks:

--- PRINCIPLES BEGIN ---
{{rules}}
--- PRINCIPLES END ---

Read the feature description and generate or update the task list.

If a current task list is provided below (not marked "not yet available"), treat this as an update run:
- Preserve the ID and **Status** of every existing task exactly as it appears.
- Add any tasks needed to fully implement the feature that are not already present, assigning new IDs continuing from the highest existing ID.
- Do not remove tasks that are `in progress` or `done`.
- Do not change the description or status of existing tasks unless the feature description has changed in a way that makes a task obsolete.

If no current task list exists, generate one from scratch: assign IDs starting at T01, set all statuses to `not started`.

Each task should be:
- Concrete and actionable (a developer knows exactly what to do)
- Small enough to complete in one focused session
- Listed in a logical implementation order
- Consistent with the principles above (e.g. if principles require tests, include test tasks)

For each task include:
- A short ID (T01, T02, ...)
- A one-line title
- A brief description (2-4 sentences) of what to implement and any important details

Format each task as:

### T01 — Task Title
**Status**: not started
**Description**: ...

--- SPEC BEGIN ---
{{spec}}
--- SPEC END ---

--- FEATURES BEGIN ---
{{features}}
--- FEATURES END ---

--- CURRENT TASKS BEGIN ---
{{tasks}}
--- CURRENT TASKS END ---

Generate the task list and write it directly to `.j2/tasks/{{feature_id}}.md`. Do not display the task list in the console — just confirm the file was written with a single line like: "Written: .j2/tasks/{{feature_id}}.md (N tasks)"
