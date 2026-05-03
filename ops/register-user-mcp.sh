#!/usr/bin/env bash
# Register the deep-ai-research-corpus MCP server at user scope (~/.claude.json).
# After this, the corpus is searchable from any Claude Code session, even
# when not started from the project directory.
#
# Idempotent — safe to re-run. Removes any prior registration first.

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NAME="deep-ai-research-corpus"

# Resolve uv binary
UV="$(command -v uv || true)"
if [ -z "$UV" ]; then
  UV="$HOME/.local/bin/uv"
fi
if [ ! -x "$UV" ]; then
  echo "uv not found; install it (https://docs.astral.sh/uv/) before running this." >&2
  exit 1
fi

echo "Removing prior registration of $NAME (if any) ..."
claude mcp remove "$NAME" --scope user 2>/dev/null || true

echo "Registering MCP server '$NAME' at user scope ..."
claude mcp add "$NAME" --scope user -- \
  "$UV" --directory "$PROJECT_ROOT" run --extra embed python -m corpus_server.server

echo
echo "Verifying:"
claude mcp list --scope user | grep -i deep-ai-research || true

cat <<INFO

Done. The corpus MCP server is now available globally. From any Claude Code
session, the deep-ai-research subagents can call corpus_search /
find_by_authority / recent / fetch_detail / benchmark_* without needing
to cd to the project directory first.

Note: the MCP server still loads the corpus from the absolute project path
($PROJECT_ROOT). If you move the project, re-run this script.
INFO
