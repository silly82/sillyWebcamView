#!/usr/bin/env python3
"""Build manifest: index.json + per-month JSONs from archive/. Atomic writes."""
import json
from collections import defaultdict
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
ARCHIVE, MANIFEST = DATA / "archive", DATA / "manifest"


def _atomic_write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj))
    tmp.replace(path)


def _extract_exif_sidecar(jpg: Path) -> dict:
    sidecar = jpg.with_suffix(".exif.json")
    if sidecar.exists():
        try:
            return json.loads(sidecar.read_text())
        except Exception:
            pass
    return {}


def build(archive: Path = ARCHIVE, manifest: Path = MANIFEST) -> None:
    frames_by_month = defaultdict(list)
    for jpg in sorted(archive.rglob("*.jpg")):
        # filename: 2026-07-25T07-03-04Z.jpg
        t = jpg.stem
        month = t[:7]  # 2026-07
        frame = {"t": t}
        exif = _extract_exif_sidecar(jpg)
        if exif:
            frame["exif"] = exif
        frames_by_month[month].append(frame)

    months = []
    total = 0
    for month in sorted(frames_by_month.keys()):
        frames = frames_by_month[month]
        total += len(frames)
        months.append({
            "key": month,
            "count": len(frames),
            "first": frames[0]["t"],
            "last": frames[-1]["t"],
        })
        _atomic_write_json(manifest / f"{month}.json", {
            "month": month,
            "frames": frames,
        })

    _atomic_write_json(manifest / "index.json", {
        "generated_at": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ"),
        "total": total,
        "months": months,
    })
    print(f"manifest: {total} frames across {len(months)} months")


if __name__ == "__main__":
    build()
