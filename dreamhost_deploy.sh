#!/usr/bin/env bash
set -euo pipefail

REMOTE="${DREAMHOST_REMOTE:?set DREAMHOST_REMOTE=user@host}"
DEST="${DREAMHOST_DEST:-bristenblick.ch/timelapse/}"

# SSH mit Retry: 3 Versuche, 10s Pause bei Fehler
ssh_retry() {
  local max=3 delay=10 i
  for i in $(seq 1 $max); do
    if ssh -o ConnectTimeout=10 -o IdentitiesOnly=yes -o IdentityFile=~/.ssh/hermes_dreamhost -o PasswordAuthentication=no -o BatchMode=yes "$@"; then
      return 0
    fi
    echo "SSH attempt $i/$max failed, waiting ${delay}s..." >&2
    sleep $delay
  done
  echo "SSH failed after $max attempts" >&2
  return 1
}

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
  --chmod=Du=rwx,Dgo=rx,Fu=rw,Fgo=r \
  web/ "$REMOTE:$DEST"

# 3. Berechtigungen auf dem Server setzen (mit Retry)
ssh_retry "$REMOTE" "cd $DEST && chmod 755 . && chmod 644 index.html favs.html 2>/dev/null; chmod 755 css js data 2>/dev/null; chmod 644 css/* js/* 2>/dev/null; chmod 755 data/* 2>/dev/null; true"

echo "✓ deployed. Einmalig nötig: ssh $REMOTE 'bash $DEST/scripts/server_setup.sh'"
echo "  Dann Cron im Dreamhost-Panel: */10 * * * * \$HOME/bristenblick.ch/timelapse/scripts/run_update.sh"
echo "  Und .htaccess um 'RewriteCond %{REQUEST_URI} !^/timelapse/' erweitern"
