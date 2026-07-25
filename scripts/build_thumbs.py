#!/usr/bin/env python3
"""Generate 800px-wide thumbs from archive via Pillow (WebP, fallback JPEG)."""
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
ARCHIVE, THUMBS = DATA / "archive", DATA / "thumbs"
WIDTH, QUALITY = 800, 80


def thumb_path_for(archive: Path, thumbs: Path, src: Path) -> Path:
    return thumbs / src.relative_to(archive).with_suffix(".webp")


def _webp_supported() -> bool:
    from PIL import features
    return features.check("webp")


def make_thumb(src: Path, dst: Path) -> Path:
    from PIL import Image
    dst.parent.mkdir(parents=True, exist_ok=True)
    im = Image.open(src)
    im.thumbnail((WIDTH, WIDTH * 10))
    if _webp_supported():
        im.save(dst, "WEBP", quality=QUALITY, method=4)
        return dst
    out = dst.with_suffix(".jpg")
    im.convert("RGB").save(out, "JPEG", quality=QUALITY)
    return out


def build_all(archive: Path = ARCHIVE, thumbs: Path = THUMBS) -> int:
    count = 0
    for src in sorted(archive.rglob("*.jpg")):
        dst = thumb_path_for(archive, thumbs, src)
        if dst.exists() or dst.with_suffix(".jpg").exists():
            continue
        make_thumb(src, dst)
        count += 1
    print(f"built {count} thumbs")
    return count


if __name__ == "__main__":
    build_all()
