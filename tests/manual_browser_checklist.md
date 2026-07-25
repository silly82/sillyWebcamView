# Browser-Test Checkliste

## Safari (zuerst)

- [ ] Kein Console-Error beim Laden
- [ ] Status-Zeile zeigt "🟢 letztes Bild vor X min"
- [ ] Zeitraum wählen → Frames laden → Zähler stimmt
- [ ] Play bei 4 fps: flüssig, kein Flackern (Preloader wirkt)
- [ ] fps-Wechsel im laufenden Betrieb
- [ ] Quality-Toggle: Thumb↔Original wechselt Bildquelle, Badge "Original (5 MB)" erscheint
- [ ] EXIF-Overlay zeigt "30s · f/2.8 · ISO 1600" unter Frames mit EXIF (Nacht-Frames)
- [ ] ★ setzen → Reload → ★ noch da → favs.html zeigt Bild
- [ ] Export → JSON geladen; Import in anderem Browser → Favs da
- [ ] iPhone Safari: Layout bricht nicht, Touch-Bedienelemente erreichbar

## Chrome

- [ ] Gleiche Checks wie Safari
- [ ] WebP-Thumbs laden korrekt (Chrome hat native WebP-Support)

## Edge Cases

- [ ] Original nach 30 Tagen → "Original nicht mehr verfügbar (30-Tage-Retention)"
- [ ] Cam offline → Status-Zeile zeigt 🔴
- [ ] Leere Datums-Range → "0 Frames"
