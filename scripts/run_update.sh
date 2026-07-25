#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "$0")/.."
python3 scripts/fetch_webcam.py >> "$HOME/logs/webcam.log" 2>&1
python3 scripts/build_thumbs.py >> "$HOME/logs/webcam.log" 2>&1
python3 scripts/build_manifest.py >> "$HOME/logs/webcam.log" 2>&1
