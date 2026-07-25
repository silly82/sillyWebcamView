import pytest
from pathlib import Path
from scripts.build_thumbs import thumb_path_for, build_all

def test_thumb_path_mirrors_archive_structure():
    src = Path("/a/archive/2026/07-25/2026-07-25T07-03-04Z.jpg")
    assert thumb_path_for(Path("/a/archive"), Path("/a/thumbs"), src) == \
        Path("/a/thumbs/2026/07-25/2026-07-25T07-03-04Z.webp")

def test_build_all_creates_thumbs(tmp_path):
    pytest.importorskip("PIL")
    from PIL import Image
    arch = tmp_path/"archive"/"2026"/"07-25"
    arch.mkdir(parents=True)
    Image.new("RGB", (1600, 900), (10, 20, 30)).save(arch/"2026-07-25T07-03-04Z.jpg")
    n = build_all(tmp_path/"archive", tmp_path/"thumbs")
    assert n == 1
    outs = list((tmp_path/"thumbs").rglob("*"))
    assert len(outs) == 1 and outs[0].suffix in (".webp", ".jpg")
    # Idempotent: 2. Lauf baut nichts neu
    assert build_all(tmp_path/"archive", tmp_path/"thumbs") == 0
