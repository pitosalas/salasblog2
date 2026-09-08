#!/usr/bin/env bash
# PostToolUse hook (Edit|Write): run ruff on the file just touched, if it's
# Python and ruff is installed. Reports violations back to Claude via
# stderr; never blocks -- PostToolUse can't, the edit already happened.

command -v jq >/dev/null 2>&1 || exit 0
input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')

[[ "$file_path" == *.py ]] || exit 0
command -v ruff >/dev/null 2>&1 || exit 0

output=$(ruff check "$file_path" 2>&1; ruff format --check "$file_path" 2>&1)
if [[ -n "$output" ]]; then
  echo "$output" >&2
  exit 2
fi
exit 0
