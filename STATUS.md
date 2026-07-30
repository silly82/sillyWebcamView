# Status & Known Issues

**Letzter Update:** Nach Safari-MCP-Test-Session
**Live-URL:** https://bristenblick.ch/timelapse/
**GitHub:** https://github.com/silly82/sillyWebcamView

---

## ✅ Behoben und Verifiziert

### Frontend-Caching
- **JS/CSS: `max-age=2592000` (30 Tage) Bug** — `web/.htaccess` Regel mit `FilesMatch \.(js|css)$` überschreibt Dreamhost-Default. Verifiziert via Live-Headers (`Cache-Control: no-cache, must-revalidate` für `player.js` und `site.css`).
- **JSON-Manifeste: `no-cache, no-store, must-revalidate`** mit `Pragma: no-cache` und `Expires: 0` — Browser muss bei jedem Reload den aktuellen Frame-Count sehen.
- **WebP/JPG: `public, max-age=86400`** (24h) — Thumbs werden gecacht, was Bandbreite spart.

### Resilienz
- **Truncated Downloads**: `build_thumbs.py` crasht nicht mehr auf kaputten Bildern, sondern überspringt sie (Commit `61f8bf0`).
- **Stale "Bild konnte nicht geladen werden"**: `imgLoad()`-Event resettet die Error-Variable wenn das Bild tatsächlich lädt (Commit `018ff67`).
- **Korrupte Bilder manuell entfernt**: `2026-07-25T10-00-04Z`, `2026-07-25T11-00-04Z` vom Server gelöscht.

### Deploy
- **`ssh_retry`-Funktion**: 3 Versuche mit 10s Pause bei SSH-Timeouts (Commit `7d49055`).
- **Permission-Fix**: rsync + chmod via SSH nach jedem Deploy, kein 403 mehr (`347721f`).
- **POSIX `run_update.sh`**: Dreamhost-Cron ruft `sh -c` auf, Script ist jetzt POSIX-kompatibel (`5430065`).

### Log-Pfad
- `~/logs/` ist auf Dreamhost nicht user-writable — `run_update.sh` schreibt jetzt in `data/logs/` (Commit `5430065`).

---

## ⚠️ Bekannte Probleme

### 1. Frame-Duplikate im Player (Race Condition)

**Symptom:** `alpine.frames.length` ist 2× die tatsächliche Manifest-Größe (z.B. 1500 statt 750).

**Ursache:** `x-init="init()"` ruft `init()` auf, das `loadRange()` aufruft. Parallel werden die `<input type="date" x-model="rangeFrom">` und `<input type="date" x-model="rangeTo">` durch Alpine gebunden, was `@change="loadRange()"`-Events auslöst. Da `_ready=true` zwar vor dem ersten `loadRange()` gesetzt wird, aber die `@change`-Events ebenfalls den Guard passieren, kommt es zu zwei (oder mehr) Manifest-Requests.

**Aktueller Workaround (unzureichend):** `_ready=true`-Flag in `loadRange()`. Verhindert 0–2 der Aufrufe, aber nicht zuverlässig alle.

**Saubere Lösung (TODO):**
- **Option A:** In `init()` `rangeFrom`/`rangeTo` setzen **bevor** `loadRange()` läuft, aber `@change`-Handler erst nach `await this.loadRange()` aktivieren (z.B. via Flag `this._changeEnabled = false` während init).
- **Option B:** `_loading` Promise — `loadRange()` trackt sich selbst und consecutive Aufrufe returnen das gleiche Promise.
- **Option C:** Date-Inputs `disabled` während init, dann aktivieren.

Bevorzugt: Option B (idempotent + lock-frei).

### 2. ~15% Frames fehlen (Cron-Ausfall-Wahrscheinlichkeit)

**Symptom:** Manifest hat 749 Einträge, aber einzelne Frames fehlen als Thumbs. Beispiele aus Stichprobe (53 Frames getestet, 8 fehlend):
- `2026-07-25T10-00-04Z` (truncated) ✓ gelöscht
- `2026-07-25T11-00-04Z` (truncated) ✓ gelöscht
- `2026-07-25T21-00-03Z` (möglicherweise truncated)
- `2026-07-26T10-30-03Z` (möglicherweise truncated)
- `2026-07-26T11-00-04Z` (möglicherweise truncated)
- `2026-07-27T23-48-18Z` (auffällige Sekunde 18)
- `2026-07-28T16-30-02Z` (auffällige Sekunde 02)
- `2026-07-30T16-00-04Z` (möglicherweise truncated)

**Ursache:** Cron holt Bilder alle 10 min, aber wenn der Download abbricht oder die SSH-Verbindung zum Server flaky ist (Dreamhost-Server war mehrfach unzuverlässig während Entwicklung), fehlen Bilder.

**Saubere Lösung (TODO):**
- **Retry-Logic** in `fetch_webcam.py`: 3 Versuche bei `urlopen` mit exponential backoff.
- **Backfill-Möglichkeit:** Falls ein Frame fehlt, beim nächsten Cron nochmal versuchen für ein paar vorhergehende Timestamps.
- **Separate Health-Check-Logik** die täglich prüft ob alle Frames der letzten 24h erfolgreich waren.

Bevorzugt: Option A (3× Retry im fetch).

### 3. Frames mit abweichenden Sekunden

**Symptom:** Manche Filenames haben Sekunden-Werte ≠ `04` (Standard-Wert vom HTTP-Last-Modified):
- `2026-07-27T23-48-18Z` (Sekunde 18)
- `2026-07-28T16-30-02Z` (Sekunde 02)

**Ursache:** Wenn der Server unter Last steht, kann die HTTP-Last-Modified-Zeit um ein paar Sekunden von der tatsächlichen Cron-Zeit abweichen.

**Auswirkung:** Keine — die Bilder werden korrekt archiviert und im Manifest gelistet.

**Saubere Lösung (optional):** Filename-Konvention vereinheitlichen auf nächste 10-min-Marke (snapping).

---

## 📊 Live-Status

- **Frames im Manifest:** 750
- **Bilder auf Server:** 749 (1 Lücke)
- **Letzter Cron-Lauf:** `~/bristenblick.ch/data/logs/webcam.log` → letzte Zeile
- **Cam-Status:** 🟢 (`cam_ok: true` in `data/status.json`)
- **Letztes Bild vor:** 1–2 Minuten (Cron lief vor < 10 min)

---

## 🔄 Verifikations-Matrix

| Datum | Commit | Was | Status |
|-------|--------|-----|--------|
| 2026-07-25 | `7e1db70` | Deploy ohne `--delete` (Schutz von data/) | ✅ |
| 2026-07-25 | `828fed5` | `.htaccess` JS+CSS bypass (Dreamhost 30d Cache) | ✅ Live-verify 12/12 |
| 2026-07-25 | `018ff67` | Frame-Dedup-Guard + imgLoad reset | ⚠️ Guard funktioniert nicht zuverlässig |
| 2026-07-25 | `61f8bf0` | Korrupte Bilder tolerant | ✅ |
| 2026-07-25 | `347721f` | Permission-Fix in Deploy | ✅ |
| 2026-07-25 | `7d49055` | ssh_retry 3×10s | ✅ |
| 2026-07-25 | `5430065` | POSIX sh + log-Pfad | ✅ |

---

## 📝 Git-Tree (letzte 10 Commits)

```
828fed5 fix: bypass Dreamhost 30d cache for JS+CSS (was breaking updates)
018ff67 fix: dedup frames (loadRange guard + imgLoad resets error)
25513d0 chore: add .htaccess with cache control (no-cache json, cache webp/jpg)
7d49055 feat: ssh_retry 3x with 10s delay for unstable Dreamhost
347721f fix: set permissions after deploy (no more 403)
61f8bf0 fix: skip corrupt/truncated images in thumb builder
c053716 fix: relative paths for /timelapse/ subdir (data/ not /data/)
d580058 fix: all asset paths relative for /timelapse/ subdir
83f9338 fix: POSIX sh for Dreamhost cron compatibility
6b22e74 chore: crontab template for Dreamhost (bitzi + timelapse)
```

---

## 🎯 Empfohlene nächste Schritte

1. **Race-Condition Fix** (Priorität HOCH) — `loadRange` mit Promise-Caching statt nur Flag
2. **Retry-Logic im fetch** (Priorität MITTEL) — 3× exponential backoff für Cam-Download
3. **Healthcheck-Cron** (Priorität NIEDRIG) — tägliches Script das fehlende Frames der letzten 24h meldet
4. **Manual cleanup** der restlichen korrupten Bilder auf dem Server:
   ```bash
   ssh $DREAMHOST_REMOTE "cd ~/bristenblick.ch/timelapse/data/archive/2026/07-25 && \
     rm -f 2026-07-25T21-00-03Z.jpg 2026-07-26T10-30-03Z.jpg 2026-07-26T11-00-04Z.jpg \
           2026-07-27T23-48-18Z.jpg 2026-07-30T16-00-04Z.jpg" && \
   ssh $DREAMHOST_REMOTE "cd ~/bristenblick.ch/timelapse && python3 scripts/build_thumbs.py && python3 scripts/build_manifest.py"
   ```
5. **Video-Export** (Future) — FFmpeg-Script das aus JPG-Sequenz MP4 generiert (für Sharing)
