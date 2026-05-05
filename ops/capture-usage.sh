#!/usr/bin/env bash
# capture-usage.sh — usage-telemetry hook handler.
#
# Patch CC (2026-05-04): originally a Stop-hook handler.
# Patch JJ (2026-05-04): also fires on PostToolUse(Agent|Task) and SubagentStop
# so the snapshot updates mid-run. Without Patch JJ, Stop only fires at the end
# of the main turn — so usage_snapshot_end.json would mirror usage_snapshot_start.json
# whenever the deep-ai-research skill ran inside a single turn.
#
# Claude Code pipes a JSON payload to hooks (and to the statusLine command).
# That payload includes `rate_limits.five_hour.used_percentage` and
# `rate_limits.seven_day.used_percentage` — the only programmatic source for
# real plan-usage data on the Max plan ($200/mo). The slash command `/usage`
# is interactive-mode-only and cannot be reached from `claude -p`.
#
# This script reads that JSON from stdin and writes a normalized snapshot
# to a well-known state file. The deep-ai-research skill copies the file
# into a run's scratch dir at Stage 1 (as `usage_snapshot_start.json`) and
# again at Stage 9 (as `usage_snapshot_end.json`), so the synthesizer's
# Patch N step 7.5 can compute true 5h/7d deltas instead of file-size
# estimates.
#
# Defensive: if the payload doesn't include rate_limits (e.g. the user is
# on API-only billing rather than a Claude.ai subscription), the script
# writes `{}` and the synthesizer falls back to Tier-1 file-size estimation.
#
# Hook registration: `.claude/settings.local.json` hooks.PostToolUse,
# hooks.SubagentStop, and hooks.Stop arrays.

set -euo pipefail

# CLAUDE_PROJECT_DIR is set by the Claude Code hook runtime to the project's
# absolute path. Fallback to the parent of this script's directory (since
# this script lives at <project>/ops/) so the script works regardless of
# where the project is cloned.
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
project_dir="${CLAUDE_PROJECT_DIR:-$(cd "$script_dir/.." && pwd)}"
state_dir="$project_dir/.claude/state"
mkdir -p "$state_dir"

# Read the JSON payload from stdin. If stdin is empty (manual test), echo
# an empty JSON object so jq doesn't choke.
input="$(cat || true)"
if [[ -z "$input" ]]; then
  input='{}'
fi

# Build the snapshot. Use jq's `// null` so missing fields become explicit
# nulls instead of jq errors. Wrap in a `try` block — if jq itself fails
# (malformed input), fall through to `{}`.
snapshot="$(
  echo "$input" | jq -c '{
    ts: (now | todate),
    five_hour_pct: (.rate_limits.five_hour.used_percentage // null),
    seven_day_pct: (.rate_limits.seven_day.used_percentage // null),
    context_window_pct: (.context_window.used_percentage // null),
    context_used_tokens: (.context_window.used_tokens // null),
    model_id: (.model.id // null),
    session_id: (.session_id // null)
  }' 2>/dev/null || echo '{}'
)"

# Atomically replace the state file so readers never see a half-written file.
tmp="$(mktemp "$state_dir/.last_usage_snapshot.XXXXXX")"
echo "$snapshot" > "$tmp"
mv "$tmp" "$state_dir/last_usage_snapshot.json"

# Stop hooks are observation-only by default. Returning 0 silently lets
# Claude Code continue normally. Returning anything in stdout would be shown
# to the user, which we don't want for a passive telemetry capture.
exit 0
