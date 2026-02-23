You are launching parallel background agents to implement multiple features concurrently.

--- RULES BEGIN ---
{{rules}}
--- RULES END ---

--- FEATURES BEGIN ---
{{features}}
--- FEATURES END ---

## Instructions

1. Scan the features above for all entries that are **not** `done`.
2. For each, check whether `.j2/tasks/<feature-id>.md` exists. Skip any feature without a task file.
3. For each eligible feature, launch a **background Task agent** using the Task tool with `run_in_background: true` and `subagent_type: "general-purpose"`. Give each agent this prompt:

   > Read `.j2/rules.md` for coding principles. Read the task file at `.j2/tasks/<feature-id>.md`. Implement every task whose `**Status**` is `not started`, in order. For each task: write the code, update that task's `**Status**` to `done` in the task file, then move to the next. After all tasks are done, run `pytest`. Do not modify `features.md`, `state.md`, or `README.md`.

4. After launching all agents, report:
   - Which features were launched and their agent IDs
   - Remind the user to run `/milestone <FID>` for each feature after agents complete
