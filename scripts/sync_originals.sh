#!/usr/bin/env bash
# Originale Server → Mac spiegeln, dann serverseitig >30 Tage löschen
set -euo pipefail
REMOTE="${DREAMHOST_REMOTE:?}"
LOCAL_ARCHIVE="$HOME/bristenblick-archive"
mkdir -p "$LOCAL_ARCHIVE"
rsync -avz "$REMOTE:~/bristenblick.ch/data/archive/" "$LOCAL_ARCHIVE/"
ssh "$REMOTE" 'find ~/bristenblick.ch/data/archive -name "*.jpg" -mtime +30 -delete; \
               find ~/bristenblick.ch/data/archive -type d -empty -delete'
echo "✓ synced, server cleaned (>30d)"
