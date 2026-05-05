#!/usr/bin/env bash
# Installs the deep-ai-research systemd-user timers and starts them.
# Idempotent — safe to re-run.
#
# The .service files in this directory contain the placeholder
# __DAIR_PROJECT_DIR__ for their WorkingDirectory. This script detects
# the project's actual absolute path (the parent of ops/, where this
# script lives) and substitutes it on copy, so the project can be
# cloned anywhere — not just ~/projects/deep-ai-research.

set -euo pipefail

UNITS_DIR="$HOME/.config/systemd/user"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Allow override via env var (useful for CI / containerized installs).
PROJECT_DIR="${DAIR_PROJECT_DIR:-$PROJECT_DIR}"

if [[ ! -d "$PROJECT_DIR" ]]; then
  echo "ERROR: detected project dir '$PROJECT_DIR' does not exist." >&2
  exit 1
fi

mkdir -p "$UNITS_DIR"

echo "Project dir:  $PROJECT_DIR"
echo "Units dir:    $UNITS_DIR"
echo "Copying unit files and substituting __DAIR_PROJECT_DIR__ ..."
for unit in deep-ai-research-ingest.service deep-ai-research-ingest.timer \
           deep-ai-research-embed.service deep-ai-research-embed.timer \
           deep-ai-research-poll-authorities.service deep-ai-research-poll-authorities.timer \
           deep-ai-research-promote-arxiv.service deep-ai-research-promote-arxiv.timer \
           deep-ai-research-tag-engagements.service deep-ai-research-tag-engagements.timer \
           deep-ai-research-digest.service deep-ai-research-digest.timer \
           deep-ai-research-podcasts.service deep-ai-research-podcasts.timer ; do
  # Use a sed delimiter that won't appear in the path (| works for any
  # absolute filesystem path). Substitute placeholder → real project dir.
  sed "s|__DAIR_PROJECT_DIR__|$PROJECT_DIR|g" \
    "$SCRIPT_DIR/$unit" > "$UNITS_DIR/$unit"
done

echo "Reloading systemd-user daemon ..."
systemctl --user daemon-reload

echo "Enabling + starting timers ..."
for t in deep-ai-research-ingest.timer deep-ai-research-embed.timer \
         deep-ai-research-poll-authorities.timer deep-ai-research-promote-arxiv.timer \
         deep-ai-research-tag-engagements.timer \
         deep-ai-research-digest.timer \
         deep-ai-research-podcasts.timer ; do
  systemctl --user enable --now "$t"
done

echo
echo "Note: The podcasts timer requires the [podcasts] optional dependency:"
echo "  cd $PROJECT_DIR && uv sync --extra podcasts"
echo "Without it, the service will log a warning and exit cleanly."

echo
echo "Status:"
systemctl --user --type=timer --no-pager | grep deep-ai-research- || true

echo
echo "Done. Tail logs with:"
echo "  journalctl --user-unit deep-ai-research-ingest.service -f"
echo "  journalctl --user-unit deep-ai-research-poll-authorities.service -f"
echo "  journalctl --user-unit deep-ai-research-promote-arxiv.service -f"
echo
echo "Note: lingering must be enabled for timers to run when you're not"
echo "logged in. Run once: 'sudo loginctl enable-linger \$USER'"
