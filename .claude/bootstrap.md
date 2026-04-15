# j3 Bootstrap Scaffold

When bootstrapping a new project with j3, assume that you are inside the directory of the target. Check that the .j3 folder is there and correct. Then create the following files and folders exactly as specified below.

## Folder structure to create

```
LICENSE
README.md
.gitignore
process/
  spec.md
  features/
    template.md
    notdone/
    done/
  tasks/
    template.md
    notdone/
    done/
```

## File contents

### process/spec.md
```
# Spec for <APP NAME>
* <Describe what the app does in a few bullet points>
```

### process/features/template.md
```
# Feature description for feature Fxx
## Fxx — description
**Priority**: High | Medium | Low
**Done:** yes | no
**Tests Written:** yes | no
**Test Passing:** yes | no
**Description**: description here.
```

### process/tasks/template.md
```
# Tasks for Feature Fxx

## T01 — task 01 is described
**Status**: done | not done
**Description**: What the task is

## T02 — task 02 is described
**Status**: done | not done
**Description**: what this task is

and so on
```

### LICENSE
Copy from `.j3/LICENSE.template` and replace `<YEAR>` and `<AUTHOR NAME>`.

### README.md
Copy from `.j3/README.md.template` and replace `<APP NAME>` and other placeholders.

### .gitignore
Copy from `.j3/.gitignore.template` as-is.

### CLAUDE.md
```
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Read and follow all rules in the `.j3/` folder:
- `.j3/method.md` — development workflow and feature/task tracking rules
- `.j3/coding.md` — coding standards and style rules

We are developing an app called <APP NAME>. Read the files in the process/ folder to understand the development.
```

## After scaffolding

Prompt the user to:
1. Fill in `process/spec.md` with the app description
2. Replace `<APP NAME>` in `CLAUDE.md`, `README.md`, and `LICENSE` with the actual app name, author, and year
3. Define the first feature before writing any code
