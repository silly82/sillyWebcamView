# sillyWebcamView

Timelapse-Archiv für die [Bristenblick](https://bristenblick.ch) Webcam (Canon EOS 2000D DSLR mit Langzeitbelichtung nachts — Sterne, Lichtspuren, Mond).

## Features

- **Automatischer Bild-Abruf** alle 10 min via Server-Cron (SHA-256-Dedup, Cache-Buster)
- **Timelapse-Player** mit fps-Slider (0.5–8), Frame-Preloader, Datums-Range-Picker, Loop
- **Quality-Toggle**: WebP-Thumbs (150 KB, schnell) ↔ Original-JPG (5 MB, Detail)
- **EXIF-Overlay**: Belichtungszeit, Blende, ISO — bei Nacht-Frames oft 15–30s · ISO 1600–6400
- **Favoriten-Galerie** mit Notizen, Import/Export (localStorage + JSON)
- **Status-Anzeige**: 🟢/🔴 Cam online/offline, letzter Fetch, Frame-Count
- **Keyboard-Shortcuts**: Space = Play/Pause, ←/→ = Frame vor/zurück

## Architektur

```
Dreamhost Shared (Datenquelle + Web-Hosting)
  ├── Cron */10 * * * * → run_update.sh
  │     ├── fetch_webcam.py     → data/archive/YYYY/MM-DD/*.jpg + .exif.json + status.json
  │     ├── build_thumbs.py     → data/thumbs/YYYY/MM-DD/*.webp (Pillow)
  │     └── build_manifest.py   → data/manifest/index.json + YYYY-MM.json
  ├── Originale: 30 Tage rollierend (~26 GB)
  ├── Thumbs: permanent (~8 GB/Jahr)
  └── Webroot: web/ (index.html, favs.html, css/, js/)

Mac (Dev-Maschine + Vollarchiv)
  ├── git clone → Entwicklung, Tests
  ├── dreamhost_deploy.sh → rsync code-only nach Dreamhost
  └── sync_originals.sh → spiegelt Originale lokal (~263 GB/Jahr)

Browser
  └── Alpine.js 3.x + Tailwind CSS via CDN, statisch, kein Build-Step
```

## Lokal entwickeln

```bash
git clone https://github.com/silly82/sillyWebcamView.git
cd sillyWebcamView

# Python-Deps (nur Pillow für Thumbs/EXIF)
python3 -m pip install --user pillow pytest

# Tests laufen lassen
python3 -m pytest tests/ -v

# Smoke-Test (lokaler HTTP-Server)
python3 tests/smoke.py

# Manuell im Browser (ohne data/ — nur UI-Test)
python3 -m http.server -d . 8080
# → http://localhost:8080/web/
```

## Deploy auf Dreamhost

**Voraussetzung:** `DREAMHOST_REMOTE` Umgebungsvariable setzen (z.B. in `~/.zshrc`):

```bash
export DREAMHOST_REMOTE=user@yourserver.dreamhost.com
```

**Deploy (code-only, niemals data/):**

```bash
./dreamhost_deploy.sh
```

**Einmalig auf dem Server (Pillow installieren, Verzeichnisse anlegen):**

```bash
ssh $DREAMHOST_REMOTE 'bash ~/bristenblick.ch/scripts/server_setup.sh'
```

**Cronjob im Dreamhost-Panel einrichten:**

```
*/10 * * * * $HOME/bristenblick.ch/scripts/run_update.sh
```

**Originale auf den Mac spiegeln (wöchentlich, z.B. via launchd):**

```bash
./scripts/sync_originals.sh
```

## Wichtige Hinweise

- **Kein Backfill möglich** — die Cam liefert nur das aktuelle Bild. Das Archiv beginnt mit dem ersten Cron-Lauf. Also direkt nach dem Deploy den Cron scharf schalten.
- **Originale nach 30 Tagen** werden serverseitig gelöscht (Retention-Policy). Das Vollarchiv liegt auf dem Mac (`~/bristenblick-archive`).
- **`data/` ist in `.gitignore`** — nur Code landet auf GitHub. Bilder, Manifeste, Status bleiben serverseitig.
- **Python 3.9+** — kein `X | None` Union-Syntax, `strptime` statt `fromisoformat`.

## Troubleshooting

| Problem | Lösung |
|---------|--------|
| Cam offline (🔴) | `status.json` prüfen, `error`-Feld. Cron-Log unter `~/logs/webcam.log` |
| WebP nicht verfügbar | `server_setup.sh` prüft Pillow-WebP-Support. Fallback ist JPEG-Thumbs |
| Original 404 nach 30 Tagen | Erwartetes Verhalten — Retention. Nutze `sync_originals.sh` für lokales Archiv |
| Tests schlagen fehl (PIL) | `python3 -m pip install --user pillow` |

## Lizenz

MIT — siehe [LICENSE](LICENSE)
