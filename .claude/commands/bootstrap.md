---
allowed-tools: Read Write Bash(mkdir *) Bash(chmod *) Glob
---
Bootstrap a new project scaffold in the current directory:

1. Read and follow @.claude/bootstrap.md exactly — it is the full scaffold spec (folder structure, file-by-file instructions, template sources).
2. Confirm the `.claude/` folder itself is present and correct before creating anything else.
3. Create every file and folder listed in bootstrap.md's "Folder structure to create" section, using the template files it points to.
4. Run bootstrap.md's "After scaffolding" checklist and prompt the user for each item (spec content, `current.md` init, `notes.md`, placeholder replacement).

**Process gate:** Stop after scaffolding and the after-scaffolding prompts. Do not define the first feature, write a task file, or write any application code — that needs its own explicit user approval per `.claude/process.md`.
