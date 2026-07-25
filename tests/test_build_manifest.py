import json
import pytest
from pathlib import Path
from scripts.build_manifest import build

def test_build_splits_by_month(tmp_path):
    pytest.importorskip("PIL")
    from PIL import Image
    for month, days in [("2026-06", ["06-30"]), ("2026-07", ["07-01", "07-02"])]:
        for d in days:
            p = tmp_path/"archive"/month[:4]/d
            p.mkdir(parents=True)
            Image.new("RGB",(100,60)).save(p/f"{d}T12-00-00Z.jpg")
    build(tmp_path/"archive", tmp_path/"manifest")
    idx = json.loads((tmp_path/"manifest"/"index.json").read_text())
    assert idx["total"] == 3
    assert [m["key"] for m in idx["months"]] == ["2026-06", "2026-07"]
    july = json.loads((tmp_path/"manifest"/"2026-07.json").read_text())
    assert len(july["frames"]) == 2

def test_exif_sidecar_merged_into_frame(tmp_path):
    pytest.importorskip("PIL")
    from PIL import Image
    p = tmp_path/"archive"/"2026"/"07-25"
    p.mkdir(parents=True)
    jpg = p/"2026-07-25T07-03-04Z.jpg"
    Image.new("RGB",(100,60)).save(jpg)
    jpg.with_suffix(".exif.json").write_text(json.dumps({
        "exposure_s": 30.0, "aperture": 2.8, "iso": 1600}))
    build(tmp_path/"archive", tmp_path/"manifest")
    july = json.loads((tmp_path/"manifest"/"2026-07.json").read_text())
    assert july["frames"][0]["exif"]["exposure_s"] == 30.0
    assert july["frames"][0]["exif"]["iso"] == 1600
