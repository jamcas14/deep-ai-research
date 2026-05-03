#!/usr/bin/env bash
# Install thedeep-ai-research (deep-ai-research) skill + agents at user level so
# /deep-ai-research is invokable from any directory.
#
# Uses symlinks so future updates in the project directory propagate
# automatically. Idempotent.

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL_SRC="$PROJECT_ROOT/.claude/skills/deep-ai-research"
SKILL_DST="$HOME/.claude/skills/deep-ai-research"
AGENTS_SRC="$PROJECT_ROOT/.claude/agents"
AGENTS_DST="$HOME/.claude/agents"

mkdir -p "$HOME/.claude/skills" "$HOME/.claude/agents"

echo "Installing skill: $SKILL_DST"
if [ -L "$SKILL_DST" ] || [ -e "$SKILL_DST" ]; then
  rm -rf "$SKILL_DST"
fi
ln -s "$SKILL_SRC" "$SKILL_DST"

echo "Installing agents:"
for f in "$AGENTS_SRC"/deep-ai-research-*.md; do
  name="$(basename "$f")"
  target="$AGENTS_DST/$name"
  if [ -L "$target" ] || [ -e "$target" ]; then
    rm -f "$target"
  fi
  ln -s "$f" "$target"
  echo "  $target -> $f"
done

echo
echo "Verifying:"
ls -la "$SKILL_DST" "$AGENTS_DST"/deep-ai-research-*.md 2>&1 | head -20

cat <<'INFO'

Done. /deep-ai-research is now invokable from any directory in any
Claude Code session.

Note about the corpus-server MCP: it's currently registered project-level
in .mcp.json. The orchestrator needs corpus search + authority queries
to work properly. Two options for global use:

  1. Always start `claude` from the project directory:
       cd /home/jamie/code/projects/deep-ai-research && claude
     This makes the project's .mcp.json discoverable.

  2. Register the MCP server at user level (harder; modifies ~/.claude.json).
     If you want this, run: bash ops/register-user-mcp.sh

For most personal-use, option 1 is simpler.
INFO
