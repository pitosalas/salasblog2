Deploy mode: {{deploy_mode}}
Target directory: {{target}}

---

## If deploy_mode is "dev-repo"

Run the following commands to bootstrap a fresh j2 project:

```bash
mkdir -p "{{target}}" && bash scaffold/install.sh "{{target}}"
```

If the commands succeed, report:
- The full output from install.sh
- The absolute path of the new project directory
- The next step: `cd <directory>` then open Claude Code and run `/refresh`

If any command fails, report the error output and stop — do not attempt partial recovery.

The directory may already exist — install.sh uses `--ignore-existing` and will not overwrite user files.

---

## If deploy_mode is "export"

Run the following commands to create a clean standalone copy of this project with all j2 infrastructure removed:

```bash
mkdir -p "{{target}}" && rsync -a \
  --exclude='.j2' \
  --exclude='scaffold' \
  --exclude='.claude' \
  --exclude='.coverage' \
  . "{{target}}/" && rm -f "{{target}}/runner.py"
```

After running, verify that the target directory:
- Contains the project source files in working form
- Does NOT contain `.j2/`, `scaffold/`, `.claude/`, or `runner.py`

Report:
- The absolute path of the exported directory
- A brief list of what was copied (source files, tests, config)
- Confirmation that no j2 artifacts remain

If any command fails, report the error and stop.
