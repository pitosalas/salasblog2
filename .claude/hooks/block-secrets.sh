#!/usr/bin/env bash
# PreToolUse hook (Edit|Write): hard-block writes to secrets/credential
# files, independent of settings.json's permissions.deny list. That list is
# a prompt-level control; this exits nonzero and blocks unconditionally.

command -v jq >/dev/null 2>&1 || exit 0
input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')

case "$file_path" in
  *.env|*.env.*|*secrets/*|*credentials.json|*.pem|*id_rsa*)
    echo "Blocked: $file_path matches a secrets/credentials pattern. Never write to this file." >&2
    exit 2
    ;;
esac
exit 0
