#!/bin/sh
# POSIX-kompatibel für Dreamhost cron (dash/sh)
set -u
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$SCRIPT_DIR/.."
mkdir -p data/logs
python3 scripts/fetch_webcam.py >> "data/logs/webcam.log" 2>&1
python3 scripts/build_thumbs.py >> "data/logs/webcam.log" 2>&1
python3 scripts/build_manifest.py >> "data/logs/webcam.log" 2>&1
