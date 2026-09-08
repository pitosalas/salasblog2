#!/usr/bin/env bash
# SessionStart hook (startup|resume): surface 02-doc/current.md's ## Open
# section as context automatically, so orientation happens even if /start
# is never explicitly run. Silent no-op if the project hasn't been
# bootstrapped yet or has no ## Open section.

project_dir="${CLAUDE_PROJECT_DIR:-.}"
current_md="$project_dir/02-doc/current.md"

[[ -f "$current_md" ]] || exit 0

awk '
  /^## Open/ { flag=1 }
  flag && /^## / && !/^## Open/ { exit }
  flag { print }
' "$current_md"
exit 0
