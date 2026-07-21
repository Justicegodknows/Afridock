#!/usr/bin/env bash
# PreToolUse hook (matcher: Write|Edit). Blocks edits/writes under apps/,
# packages/, or infra/ until progress.md has been read this session.
set -euo pipefail

ROOT="/Users/justice/Documents/Afridock"

input="$(cat)"
session_id="$(jq -r '.session_id // empty' <<<"$input")"
file_path="$(jq -r '.tool_input.file_path // empty' <<<"$input")"

case "$file_path" in
  "$ROOT"/apps/*|"$ROOT"/packages/*|"$ROOT"/infra/*)
    ;;
  *)
    exit 0
    ;;
esac

marker_dir="${TMPDIR:-/tmp}/claude-afridock-progress-read"
if [ -f "$marker_dir/$session_id" ]; then
  exit 0
fi

jq -n '{
  hookSpecificOutput: {
    hookEventName: "PreToolUse",
    permissionDecision: "deny",
    permissionDecisionReason: "progress.md has not been read yet this session. Read progress.md (project root) before writing or editing code under apps/, packages/, or infra/ — it is the mandatory pre-coding checkpoint. Then retry."
  }
}'

exit 0
