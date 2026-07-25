# sillyWebcamView

Timelapse-Archiv für die [Bristenblick](https://bristenblick.ch) Webcam (Canon EOS 2000D DSLR mit Langzeitbelichtung nachts).

## Features

- Automatischer Bild-Abruf alle 10 min (Server-Cron)
- Timelapse-Player mit fps-Slider, Preloader, Datums-Range
- Quality-Toggle: WebP-Thumbs (schnell) ↔ Original-JPG (Detail)
- EXIF-Overlay (Belichtungszeit, Blende, ISO) — besonders bei Nacht-Langzeitbelichtung
- Favoriten-Galerie mit Import/Export (localStorage)
- Status-Anzeige (Cam online/offline, letzter Fetch)

## Architektur

```
Dreamhost Shared (Datenquelle)
  ├── Cron */10 * * * * → run_update.sh
  │     ├── fetch_webcam.py     → data/archive/YYYY/MM-DD/*.jpg + .exif.json + status.json
  │     ├── build_thumbs.py     → data/thumbs/YYYY/MM-DD/*.webp (Pillow)
  │     └── build_manifest.py   → data/manifest/index.json + YYYY-MM.json
  ├── Originale: 30 Tage rollierend (~26 GB)
  └── Thumbs: permanent (~8 GB/Jahr)

Mac (Dev + Vollarchiv)
  ├── rsync Deploy (code-only, niemals data/)
  └── sync_originals.sh → spiegelt Originale lokal (~263 GB/Jahr)

Browser
  └── Alpine.js + Tailwind CDN, statisch, kein Build
```

## Lokal entwickeln

```bash
python3 -m pip install --user pillow pytest
python3 scripts/fetch_webcam.py       # 1× Bild holen
python3 scripts/build_thumbs.py       # Thumbs generieren
python3 scripts/build_manifest.py     # Manifest bauen
python3 -m pytest tests/ -v           # Tests
python3 -m http.server -d . 8080      # http://localhost:8080/web/
```

## Deploy auf Dreamhost

```bash
export DREAMHOST_REMOTE=user@yourserver.com
./dreamhost_deploy.sh
ssh $DREAMHOST_REMOTE 'bash ~/bristenblick.ch/scripts/server_setup.sh'
# Cron im Dreamhost-Panel: */10 * * * * $HOME/bristenblick.ch/scripts/run_update.sh
```

## Wichtig

- **Kein Backfill möglich** — die Cam liefert nur das aktuelle Bild. Archiv beginnt mit dem ersten Cron-Lauf.
- **Originale nach 30 Tagen** nur noch lokal auf dem Mac (Retention-Policy).
- `data/` ist in `.gitignore` — nur Code landet auf GitHub.
