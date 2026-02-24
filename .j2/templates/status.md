Report the current project health. Use the context below. Be concise — no raw file dumps.

--- FEATURES BEGIN ---
{{features}}
--- FEATURES END ---

--- MISSING TASKS ---
{{missing_tasks}}
--- END ---

--- STATE BEGIN ---
{{state}}
--- STATE END ---

## Output format

Print exactly this structure (fill in the counts):

Project Status
==============
Specs:      <count .j2/specs/*.md files>
Features:   <done count> done / <in progress count> in progress / <not started count> not started
Missing task files: <list feature IDs, or "none">
Pending tasks: <count tasks with status `not started` across all .j2/tasks/*.md files>
Last completed: <completed: line from state>
Next:       <next: line from state>

To count pending tasks, read each file in `.j2/tasks/` (not `done/`) and count lines containing `**Status**: not started`.
To count specs, list files matching `.j2/specs/*.md`.
