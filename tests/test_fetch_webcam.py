from pathlib import Path
from unittest.mock import patch, MagicMock
from scripts.fetch_webcam import fetch_and_save, build_target_path

def test_build_target_path_uses_iso_timestamp():
    p = build_target_path(Path("/tmp/x"), "2026-07-25T07-03-04Z")
    assert p == Path("/tmp/x/2026/07-25/2026-07-25T07-03-04Z.jpg")

def _mock_response(data: bytes, last_mod: str):
    m = MagicMock()
    m.read.return_value = data
    m.headers.get.return_value = last_mod
    return m

def test_fetch_saves_new_image(tmp_path):
    with patch("scripts.fetch_webcam.urlopen") as mock:
        mock.return_value.__enter__.return_value = _mock_response(
            b"\xff\xd8\xff\xe0img1", "Sat, 25 Jul 2026 07:03:04 GMT")
        p = fetch_and_save(tmp_path, status_path=tmp_path/"status.json",
                           hash_db=tmp_path/"hashes.json")
        assert p is not None and p.exists()
        assert p.read_bytes() == b"\xff\xd8\xff\xe0img1"

def test_fetch_skips_duplicate_and_returns_none(tmp_path):
    with patch("scripts.fetch_webcam.urlopen") as mock:
        mock.return_value.__enter__.return_value = _mock_response(
            b"\xff\xd8\xff\xe0img1", "Sat, 25 Jul 2026 07:03:04 GMT")
        fetch_and_save(tmp_path, status_path=tmp_path/"status.json",
                       hash_db=tmp_path/"hashes.json")
        p2 = fetch_and_save(tmp_path, status_path=tmp_path/"status.json",
                            hash_db=tmp_path/"hashes.json")
        assert p2 is None

def test_status_json_written_on_success(tmp_path):
    import json
    with patch("scripts.fetch_webcam.urlopen") as mock:
        mock.return_value.__enter__.return_value = _mock_response(
            b"\xff\xd8\xff\xe0img1", "Sat, 25 Jul 2026 07:03:04 GMT")
        fetch_and_save(tmp_path, status_path=tmp_path/"status.json",
                       hash_db=tmp_path/"hashes.json")
    s = json.loads((tmp_path/"status.json").read_text())
    assert s["cam_ok"] is True
    assert "last_attempt" in s

def test_status_json_marks_failure(tmp_path):
    import json
    with patch("scripts.fetch_webcam.urlopen", side_effect=OSError("timeout")):
        fetch_and_save(tmp_path, status_path=tmp_path/"status.json",
                       hash_db=tmp_path/"hashes.json")
    s = json.loads((tmp_path/"status.json").read_text())
    assert s["cam_ok"] is False
    assert "error" in s
