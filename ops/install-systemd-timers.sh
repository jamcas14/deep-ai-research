#!/usr/bin/env bash
# Installs the deep-ai-research systemd-user timers and starts them.
# Idempotent — safe to re-run.

set -euo pipefail

UNITS_DIR="$HOME/.config/systemd/user"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$UNITS_DIR"

echo "Copying unit files to $UNITS_DIR ..."
for unit in deep-ai-research-ingest.service deep-ai-research-ingest.timer \
           deep-ai-research-embed.service deep-ai-research-embed.timer \
           deep-ai-research-poll-authorities.service deep-ai-research-poll-authorities.timer \
           deep-ai-research-promote-arxiv.service deep-ai-research-promote-arxiv.timer \
           deep-ai-research-tag-engagements.service deep-ai-research-tag-engagements.timer \
           deep-ai-research-digest.service deep-ai-research-digest.timer ; do
  cp "$SCRIPT_DIR/$unit" "$UNITS_DIR/$unit"
done

echo "Reloading systemd-user daemon ..."
systemctl --user daemon-reload

echo "Enabling + starting timers ..."
for t in deep-ai-research-ingest.timer deep-ai-research-embed.timer \
         deep-ai-research-poll-authorities.timer deep-ai-research-promote-arxiv.timer \
         deep-ai-research-tag-engagements.timer \
         deep-ai-research-digest.timer ; do
  systemctl --user enable --now "$t"
done

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
