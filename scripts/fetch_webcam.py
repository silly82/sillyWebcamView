#!/usr/bin/env python3
"""Fetch Bristenblick webcam image. Designed for server cron every 10 min."""
import hashlib, json, sys, time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.request import urlopen, Request

URL = "https://bristenblick.ch/imagebizi.jpg"
DATA = Path(__file__).resolve().parent.parent / "data"
ARCHIVE_ROOT = DATA / "archive"


def build_target_path(root: Path, iso: str) -> Path:
    dt = datetime.strptime(iso, "%Y-%m-%dT%H-%M-%SZ")
    return root / f"{dt.year:04d}" / f"{dt.month:02d}-{dt.day:02d}" / \
           f"{dt.strftime('%Y-%m-%dT%H-%M-%SZ')}.jpg"


def _load_hashes(db: Path) -> set:
    return set(json.loads(db.read_text())) if db.exists() else set()


def _atomic_write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj))
    tmp.replace(path)


def _update_status(path: Path, ok: bool, frame_count: int, error: str = "") -> None:
    _atomic_write_json(path, {
        "last_attempt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ"),
        "cam_ok": ok,
        "frame_count": frame_count,
        **({"error": error} if error else {}),
    })


def _count_frames(root: Path) -> int:
    return sum(1 for _ in root.rglob("*.jpg")) if root.exists() else 0


def _extract_exif(jpg_path: Path) -> dict:
    """Belichtungsdaten aus JPEG lesen. Pillow-only, kein exifread nötig."""
    try:
        from PIL import Image
        im = Image.open(jpg_path)
        raw = im.getexif()
        if not raw:
            return None
        exif = {}
        ifd = raw.get_ifd(0x8769) if hasattr(raw, "get_ifd") else {}
        def _frac(v):
            return float(v) if hasattr(v, "__float__") else None
        if 33434 in ifd:  # ExposureTime (rational)
            t = _frac(ifd[33434])
            exif["exposure_s"] = round(t, 4) if t else None
        if 33437 in ifd:  # FNumber
            f = _frac(ifd[33437])
            exif["aperture"] = round(f, 1) if f else None
        if 34855 in ifd:  # ISOSpeedRatings
            exif["iso"] = int(ifd[34855])
        if 36867 in ifd:  # DateTimeOriginal
            exif["shot_at"] = str(ifd[36867])
        if 271 in raw: exif["camera_make"] = str(raw[271])
        if 272 in raw: exif["camera_model"] = str(raw[272])
        return exif or None
    except Exception:
        return None


def fetch_and_save(archive_root: Path = ARCHIVE_ROOT,
                   status_path: Path = DATA / "status.json",
                   hash_db: Path = DATA / "hashes.json") -> Path:
    """Fetch image, save if new. Returns path, or None on duplicate/failure."""
    archive_root.mkdir(parents=True, exist_ok=True)
    try:
        # Cache-Buster: upstream sends bogus max-age=30d
        req = Request(f"{URL}?t={int(time.time())}",
                      headers={"User-Agent": "sillyWebcamView/1.0"})
        with urlopen(req, timeout=30) as resp:
            data = resp.read()
            last_mod = resp.headers.get("Last-Modified", "")
        if not data.startswith(b"\xff\xd8"):
            raise ValueError("not a JPEG")
    except Exception as e:
        _update_status(status_path, False, _count_frames(archive_root), str(e))
        print(f"fetch failed: {e}", file=sys.stderr)
        return None

    digest = hashlib.sha256(data).hexdigest()
    hashes = _load_hashes(hash_db)
    if digest in hashes:
        _update_status(status_path, True, _count_frames(archive_root))
        print("duplicate, skip", file=sys.stderr)
        return None

    if last_mod:
        dt = parsedate_to_datetime(last_mod).astimezone(timezone.utc)
        iso = dt.strftime("%Y-%m-%dT%H-%M-%SZ")
    else:
        iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    target = build_target_path(archive_root, iso)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    hashes.add(digest)
    _atomic_write_json(hash_db, sorted(hashes))

    # EXIF-Sidecar (Belichtungszeit/ISO/Blende — für Nacht-Langzeitbelichtung)
    exif = _extract_exif(target)
    if exif:
        _atomic_write_json(target.with_suffix(".exif.json"), exif)

    _update_status(status_path, True, _count_frames(archive_root))
    print(f"saved: {target} ({len(data)} bytes)")
    return target


if __name__ == "__main__":
    fetch_and_save()
