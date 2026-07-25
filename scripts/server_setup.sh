#!/usr/bin/env bash
set -euo pipefail
python3 -m pip install --user --quiet pillow
python3 -c "from PIL import features; print('webp:', features.check('webp'))"
mkdir -p ~/bristenblick.ch/timelapse/data/{archive,thumbs,manifest} ~/logs
echo "✓ setup done. Jetzt Cron einrichten (siehe README)."
echo "  Und .htaccess um 'RewriteCond %{REQUEST_URI} !^/timelapse/' erweitern"
