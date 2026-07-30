function playerApp() {
  return {
    index: null,            // manifest index.json
    frames: [],             // geladene Frames der Range
    pos: 0,
    fps: 4,
    playing: false,
    timer: null,
    loop: true,
    quality: 'thumb',       // 'thumb' (WebP 800px, schnell) | 'original' (JPG 5MB, Detail)
    rangeFrom: '', rangeTo: '',
    favs: [],
    status: null,
    error: '',
    preloadCache: new Map(),

    async init() {
      this.favs = JSON.parse(localStorage.getItem('sillywc.favs') || '[]');
      [this.index, this.status] = await Promise.all([
        fetch('data/manifest/index.json').then(r => r.json()),
        fetch('data/status.json').then(r => r.json()).catch(() => null),
      ]);
      const keys = this.index.months.map(m => m.key);
      this.rangeFrom = keys[0] + '-01';
      this.rangeTo = new Date().toISOString().slice(0, 10);
      this._ready = true;
      await this.loadRange();
    },

    async loadRange() {
      // Skip until init has set rangeFrom/rangeTo (avoids double-load on mount)
      if (!this._ready) return;
      this.frames = [];
      const fromM = this.rangeFrom.slice(0, 7), toM = this.rangeTo.slice(0, 7);
      for (const m of this.index.months) {
        if (m.key < fromM || m.key > toM) continue;
        const month = await fetch(`data/manifest/${m.key}.json`).then(r => r.json());
        for (const f of month.frames) {
          const day = f.t.slice(0, 10);
          if (day >= this.rangeFrom && day <= this.rangeTo) this.frames.push(f);
        }
      }
      this.pos = 0;
      this.preloadAround(0);
    },

    get visibleFrames() {
      return this.frames;
    },

    utcDate(t) {  // "2026-07-25T07-03-04Z" → Date
      return new Date(t.replace(/T(\d{2})-(\d{2})-(\d{2})Z/, 'T$1:$2:$3Z'));
    },

    thumbUrl(t) {
      return `data/thumbs/${t.slice(0,4)}/${t.slice(5,10)}/${t}.webp`;
    },

    originalUrl(t) {
      return `data/archive/${t.slice(0,4)}/${t.slice(5,10)}/${t}.jpg`;
    },

    frameUrl(t) {
      return this.quality === 'original' ? this.originalUrl(t) : this.thumbUrl(t);
    },

    // EXIF-Readout: "30s · f/2.8 · ISO 1600" oder null
    exifLine(f) {
      if (!f?.exif) return null;
      const parts = [];
      if (f.exif.exposure_s) parts.push(f.exif.exposure_s >= 1
        ? `${f.exif.exposure_s}s` : `1/${Math.round(1/f.exif.exposure_s)}s`);
      if (f.exif.aperture) parts.push(`f/${f.exif.aperture}`);
      if (f.exif.iso) parts.push(`ISO ${f.exif.iso}`);
      return parts.length ? parts.join(' · ') : null;
    },

    get currentFrame() { return this.visibleFrames[this.pos]; },

    // Preloader — nächste 30 Frames vorab laden, sonst ruckelt's.
    // Bei quality='original' nur 5 vorladen (5 MB pro Frame).
    preloadAround(p) {
      const vf = this.visibleFrames;
      const ahead = this.quality === 'original' ? 5 : 30;
      for (let i = p; i < Math.min(p + ahead, vf.length); i++) {
        const url = this.frameUrl(vf[i].t);
        if (!this.preloadCache.has(url)) {
          const img = new Image();
          img.src = url;
          this.preloadCache.set(url, img);
        }
      }
      if (this.preloadCache.size > 200) {  // Cache begrenzen
        const keep = new Set(Array.from({length: 40},
          (_, i) => vf[p + i] && this.frameUrl(vf[p + i].t)).filter(Boolean));
        for (const k of this.preloadCache.keys())
          if (!keep.has(k)) this.preloadCache.delete(k);
      }
    },

    play() {
      this.playing = true;
      this.timer = setInterval(() => this.step(1), 1000 / this.fps);
    },
    stop() { this.playing = false; clearInterval(this.timer); },
    togglePlay() { this.playing ? this.stop() : this.play(); },
    setFps(v) { this.fps = v; if (this.playing) { this.stop(); this.play(); } },

    step(d) {
      const n = this.visibleFrames.length;
      if (!n) return;
      let next = this.pos + d;
      if (next >= n) { if (!this.loop) return this.stop(); next = 0; }
      if (next < 0) next = n - 1;
      this.pos = next;
      this.error = '';
      this.preloadAround(next);
    },

    // Keyboard: Space=Play/Pause, ←/→=Frame
    keyHandler(e) {
      if (e.key === ' ') { e.preventDefault(); this.togglePlay(); }
      else if (e.key === 'ArrowRight') this.step(1);
      else if (e.key === 'ArrowLeft') this.step(-1);
    },

    imgError(e) {
      // Only set error if image truly failed (not stale error from initial load)
      if (this.quality === 'original') {
        this.error = 'Original nicht mehr verfügbar (30-Tage-Retention)';
      } else {
        this.error = 'Bild konnte nicht geladen werden';
      }
    },

    imgLoad(e) {
      // Clear error when image actually loads successfully
      this.error = '';
    },

    isFav(f) { return f && this.favs.some(x => x.t === f.t); },
    toggleFav() {
      const f = this.currentFrame; if (!f) return;
      const i = this.favs.findIndex(x => x.t === f.t);
      i >= 0 ? this.favs.splice(i, 1) : this.favs.push({ t: f.t, note: '' });
      localStorage.setItem('sillywc.favs', JSON.stringify(this.favs));
    },
    exportFavs() {
      const blob = new Blob([JSON.stringify(this.favs, null, 2)],
        { type: 'application/json' });
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = `bristenblick-favs-${Date.now()}.json`;
      a.click();
    },

    statusLine() {
      if (!this.status) return '…';
      const ago = Math.round((Date.now() - this.utcDate(this.status.last_attempt)) / 60000);
      return `${this.status.cam_ok ? '🟢' : '🔴'} letztes Bild vor ${ago} min · ${this.status.frame_count} Frames`;
    },
  };
}
