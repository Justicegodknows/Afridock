#!/usr/bin/env bash
# PostToolUse hook (matcher: Read). Marks this session as having read
# progress.md, so require-progress-read.sh can allow subsequent code edits.
set -euo pipefail

input="$(cat)"
session_id="$(jq -r '.session_id // empty' <<<"$input")"
file_path="$(jq -r '.tool_input.file_path // empty' <<<"$input")"

[ -z "$session_id" ] && exit 0

case "$file_path" in
  */progress.md|progress.md)
    marker_dir="${TMPDIR:-/tmp}/claude-afridock-progress-read"
    mkdir -p "$marker_dir"
    touch "$marker_dir/$session_id"
    ;;
esac

exit 0
