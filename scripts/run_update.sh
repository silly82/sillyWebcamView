#!/bin/sh
# POSIX-kompatibel für Dreamhost cron (dash/sh)
set -u
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$SCRIPT_DIR/.."
python3 scripts/fetch_webcam.py >> "$HOME/logs/webcam.log" 2>&1
python3 scripts/build_thumbs.py >> "$HOME/logs/webcam.log" 2>&1
python3 scripts/build_manifest.py >> "$HOME/logs/webcam.log" 2>&1
