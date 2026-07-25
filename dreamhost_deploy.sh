#!/usr/bin/env bash
set -euo pipefail

REMOTE="${DREAMHOST_REMOTE:?set DREAMHOST_REMOTE=user@host}"
DEST="${DREAMHOST_DEST:-bristenblick.ch/timelapse/}"

cd "$(dirname "$0")"

# 1. Scripts + LICENSE deployen
rsync -avz \
  --exclude='.git/' \
  --exclude='.hermes/' \
  --exclude='data/' \
  --exclude='tests/' \
  --exclude='*.md' \
  --exclude='.gitignore' \
  --exclude='__pycache__/' \
  --exclude='.pytest_cache/' \
  --exclude='.DS_Store' \
  scripts/ "$REMOTE:$DEST/scripts/"

# 2. web/ flach in den DocumentRoot (ohne --delete, sonst wird data/ geloescht!)
rsync -avz \
  --exclude='.DS_Store' \
  web/ "$REMOTE:$DEST"

echo "✓ deployed. Einmalig nötig: ssh $REMOTE 'bash $DEST/scripts/server_setup.sh'"
echo "  Dann Cron im Dreamhost-Panel: */10 * * * * \$HOME/bristenblick.ch/timelapse/scripts/run_update.sh"
echo "  Und .htaccess um 'RewriteCond %{REQUEST_URI} !^/timelapse/' erweitern"
