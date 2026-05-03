#!/usr/bin/env bash
# Installs the dair systemd-user timers and starts them.
# Idempotent — safe to re-run.

set -euo pipefail

UNITS_DIR="$HOME/.config/systemd/user"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$UNITS_DIR"

echo "Copying unit files to $UNITS_DIR ..."
for unit in dair-ingest.service dair-ingest.timer \
           dair-embed.service dair-embed.timer \
           dair-poll-authorities.service dair-poll-authorities.timer \
           dair-promote-arxiv.service dair-promote-arxiv.timer \
           dair-tag-engagements.service dair-tag-engagements.timer ; do
  cp "$SCRIPT_DIR/$unit" "$UNITS_DIR/$unit"
done

echo "Reloading systemd-user daemon ..."
systemctl --user daemon-reload

echo "Enabling + starting timers ..."
for t in dair-ingest.timer dair-embed.timer \
         dair-poll-authorities.timer dair-promote-arxiv.timer \
         dair-tag-engagements.timer ; do
  systemctl --user enable --now "$t"
done

echo
echo "Status:"
systemctl --user --type=timer --no-pager | grep dair- || true

echo
echo "Done. Tail logs with:"
echo "  journalctl --user-unit dair-ingest.service -f"
echo "  journalctl --user-unit dair-poll-authorities.service -f"
echo "  journalctl --user-unit dair-promote-arxiv.service -f"
echo
echo "Note: lingering must be enabled for timers to run when you're not"
echo "logged in. Run once: 'sudo loginctl enable-linger \$USER'"
