# sillyWebcamView

Timelapse-Archiv für die [Bristenblick](https://bristenblick.ch) Webcam (Canon EOS 2000D DSLR mit Langzeitbelichtung nachts — Sterne, Lichtspuren, Mond).

**Live:** https://bristenblick.ch/timelapse/

## Features

- **Automatischer Bild-Abruf** alle 10 min via Server-Cron (SHA-256-Dedup, Cache-Buster)
- **Timelapse-Player** mit fps-Slider (0.5–8), Frame-Preloader, Datums-Range-Picker, Loop
- **Quality-Toggle**: WebP-Thumbs (150 KB, schnell) ↔ Original-JPG (5 MB, Detail)
- **EXIF-Overlay**: Belichtungszeit, Blende, ISO — bei Nacht-Frames oft 15–30s · ISO 1600–6400
- **Favoriten-Galerie** mit Notizen, Import/Export (localStorage + JSON)
- **Status-Anzeige**: 🟢/🔴 Cam online/offline, letzter Fetch, Frame-Count
- **Keyboard-Shortcuts**: Space = Play/Pause, ←/→ = Frame vor/zurück
- **Robuste Pipeline**: Korrupte/truncated Bilder werden übersprungen statt crash zu verursachen

## Architektur

```
Dreamhost Shared (Datenquelle + Web-Hosting)
  ├── Cron */10 * * * * → run_update.sh (POSIX-sh-kompatibel)
  │     ├── fetch_webcam.py     → data/archive/YYYY/MM-DD/*.jpg + .exif.json + status.json
  │     ├── build_thumbs.py     → data/thumbs/YYYY/MM-DD/*.webp (Pillow, korrupt-Tolerant)
  │     └── build_manifest.py   → data/manifest/index.json + YYYY-MM.json (atomar)
  ├── Originale: 30 Tage rollierend (~26 GB)
  ├── Thumbs: permanent (~8 GB/Jahr)
  └── Webroot: ~/bristenblick.ch/timelapse/ (index.html, favs.html, css/, js/, data/, .htaccess)

Mac (Dev-Maschine + Vollarchiv)
  ├── git clone → Entwicklung, Tests
  ├── dreamhost_deploy.sh → rsync code-only mit ssh_retry (3x, 10s Delay)
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

# Tests laufen lassen (9 Tests, 3 skipped falls Pillow fehlt)
python3 -m pytest tests/ -v

# Smoke-Test (lokaler HTTP-Server, validiert Asset-Referenzen)
python3 tests/smoke.py

# Manuell im Browser
python3 -m http.server -d . 8080
# → http://localhost:8080/web/
```

## Deploy auf Dreamhost

**Voraussetzung:** `DREAMHOST_REMOTE` Umgebungsvariable:

```bash
export DREAMHOST_REMOTE=user@yourserver.dreamhost.com
```

**Deploy:** Code-only (niemals `data/`!), mit ssh_retry (3 Versuche × 10s Pause):

```bash
./dreamhost_deploy.sh
```

**Einmalig auf dem Server (Pillow installieren, Verzeichnisse anlegen):**

```bash
ssh $DREAMHOST_REMOTE 'bash ~/bristenblick.ch/timelapse/scripts/server_setup.sh'
```

**Cronjob im Dreamhost-Panel** (User `silly82`):

```
*/10 * * * * bash -c "/home/silly82/bristenblick.ch/timelapse/scripts/run_update.sh"
```

**.htaccess anpassen** damit `/timelapse/` nicht nach `/weather/` umgeleitet wird (in `~/bristenblick.ch/.htaccess`):

```apache
RewriteCond %{REQUEST_URI} !^/timelapse/
```

**Originale auf den Mac spiegeln (wöchentlich):**

```bash
./scripts/sync_originals.sh
```

## Wichtige Hinweise

- **Kein Backfill möglich** — die Cam liefert nur das aktuelle Bild. Das Archiv beginnt mit dem ersten Cron-Lauf. Also direkt nach dem Deploy den Cron scharf schalten.
- **Originale nach 30 Tagen** werden serverseitig gelöscht (Retention-Policy). Das Vollarchiv liegt auf dem Mac (`~/bristenblick-archive`).
- **`data/` ist in `.gitignore`** — nur Code landet auf GitHub. Bilder, Manifeste, Status bleiben serverseitig.
- **Python 3.9+** — kein `X | None` Union-Syntax, `strptime` statt `fromisoformat`.
- **Dreamhost `max-age=2592000`** für JS/CSS wird durch eigene `.htaccess`-Regel im `web/`-Subtree auf `no-cache, must-revalidate` überschrieben — sonst laden Browser ewig die alte JS.
- **Safari Developer Remote Automation** muss in Safari Technology Preview aktiviert sein um die Seite via Safari MCP zu testen.

## Troubleshooting

| Problem | Lösung |
|---------|--------|
| Cam offline (🔴) | `data/logs/webcam.log` prüfen, `error`-Feld in `status.json` |
| WebP nicht verfügbar | `server_setup.sh` prüft Pillow-WebP-Support. Fallback ist JPEG-Thumbs |
| Original 404 nach 30 Tagen | Erwartetes Verhalten — Retention. Nutze `sync_originals.sh` für lokales Archiv |
| Tests schlagen fehl (PIL) | `python3 -m pip install --user pillow` |
| 403 Forbidden nach Deploy | `ssh_retry`-Logik im Deploy-Script setzt Permissions via SSH. Manuell: `chmod 755 . && chmod 644 *.html` |
| Player zeigt doppelte Frames | Siehe "Known Issues" unten |
| Browser lädt alte JS nach Update | Hard-Reload (Cmd+Shift+R) oder `location.reload(true)` |

## Known Issues / Bekannte Einschränkungen

### Frame-Duplikate im Player (Race Condition)

Wenn die Seite geladen wird, zeigt `alpine.frames.length` 2× die tatsächliche Anzahl. Das ist ein Race zwischen `x-init="init()"` und den `@change="loadRange()"`-Handlern der Date-Inputs, die per `x-model="rangeFrom"` / `x-model="rangeTo"` gebunden sind.

Aktueller Workaround: `_ready=true` Guard in `loadRange()`. Dieser verhindert einen Teil der Doppel-Loads, aber nicht alle — vermutlich zweiter Aufruf aus `@change`-Event parallel zum init.

Saubere Lösung (TODO): In `init()` den Range-Wert **erst nach** dem ersten `loadRange()` setzen, oder einen `_loading` Promise-Pattern verwenden der zweite Aufrufe awaited.

### Korrupte Bilder (truncated Downloads)

Wenn die Cam-Verbindung während des 5 MB Downloads abbricht, speichert `build_thumbs.py` einen Eintrag im Manifest und crasht. **Gefixt:** `build_thumbs.py` ignoriert truncated Bilder seit Commit `61f8bf0`. Bereits existierende kaputte Bilder (z.B. `2026-07-25T10-00-04Z`, `2026-07-25T11-00-04Z`, `2026-07-25T21-00-03Z`, `2026-07-26T11-00-04Z`) wurden manuell gelöscht.

### Frames mit abweichenden Sekunden-Werten

Manche Filenames haben Sekunden ≠ `04` (z.B. `2026-07-27T23-48-18Z`, `2026-07-28T16-30-02Z`). Diese entstehen wenn der Server mit Last zu kämpfen hat und die HTTP-Date-Header nicht zur tatsächlichen Cron-Zeit passen. Bilder werden trotzdem korrekt archiviert.

## Browser-Test Setup (Safari MCP)

Safari Technology Preview 27+ hat einen [MCP-Server für Webentwickler](https://webkit.org/blog/18136/introducing-the-safari-mcp-server-for-web-developers/). Integration in Hermes:

`~/.hermes/config.yaml`:
```yaml
mcp_servers:
  safari-stp:
    command: /Applications/Safari Technology Preview.app/Contents/MacOS/safaridriver
    args:
      - --mcp
    enabled: true
```

**Voraussetzung:** Safari Technology Preview → Settings → Advanced → "Show Develop menu in menu bar", dann Develop → "Allow Remote Automation".

MCP-Tools sind erst nach Session-Neustart (`Ctrl+C` → neue Session) verfügbar.

## Verifikation

Nach jedem signifikanten Change wurde mit ad-hoc Verify-Skripten geprüft:

| Komponente | Check | Ergebnis |
|------------|-------|----------|
| `.htaccess` | 4 Cache-Profile + WebP-MIME + IfModule-Guard | 12/12 PASS |
| `player.js` | Relative paths (kein `/data/`), alle Features | 6/6 PASS |
| `run_update.sh` | POSIX-sh, no bashisms, korrekte Logs | 7/7 PASS |
| `fetch_webcam.py` | Dedup, Cache-Buster, Status, Error-Path | 5/5 PASS |
| `dreamhost_deploy.sh` | ssh_retry, keine `--delete` auf web/, Permissions | 7/7 PASS |
| Gesamt | pytest | 9 passed, 3 skipped |

## Lizenz

MIT — siehe [LICENSE](LICENSE)
