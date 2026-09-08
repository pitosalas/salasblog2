---
description: Run tests, update docs, commit and push
allowed-tools: Bash(git add *) Bash(git commit *) Bash(git push *) Bash(ruff *) Read Edit Write Glob
---
Run a full checkpoint in this order:

- Run all tests
- Run `ruff check . && ruff format --check .`; fix any violations before continuing
- Update current.md's `## Open` section with your latest context; move any
  newly-completed items out to `02-doc/history.md` instead of appending to
  current.md
- Review changed code against judgment rules in @.claude/style_guide.md (design, error handling, naming semantics)
- Update any changed literate md files
- Create a commit (no need for a pull request)
- Push to github