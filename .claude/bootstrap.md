# Bootstrap Scaffold

When bootstrapping a new project, assume that you are inside the directory of the target. Check .claude folder is there and correct. Then create the following files and folders exactly as specified below.

## Folder structure to create

```
LICENSE
README.md
.gitignore
process/
  spec.md
  features/
    notdone/
    done/
    deferred/
  tasks/
    notdone/
    done/
    deferred/
  bugs/
    found/
    fixed/
```
### LICENSE
Copy from `.claude/templates/LICENSE.template` and replace `<YEAR>` and `<AUTHOR NAME>`.

### README.md
Copy from `.claude/templates/README.md.template` and replace `<APP NAME>` and other placeholders.

### .gitignore
Copy from `.claude/templates/.gitignore.template` as-is.

### CLAUDE.md
```
We are developing an app called <APP NAME>. Read the files in the process/ folder to understand the development.
```

## After scaffolding

Prompt the user to:
1. Fill in `process/spec.md` with the app description
2. Replace `<APP NAME>` in `CLAUDE.md`, `README.md`, and `LICENSE` with the actual app name, author, and year
3. Define the first feature before writing any code
