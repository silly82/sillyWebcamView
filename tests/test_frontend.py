from pathlib import Path

WEB = Path(__file__).resolve().parent.parent / "web"

def test_index_references_required_assets():
    html = (WEB/"index.html").read_text()
    assert "alpinejs" in html.lower()
    assert "tailwindcss" in html.lower()
    assert "/js/player.js" in html

def test_player_has_core_features():
    js = (WEB/"js"/"player.js").read_text()
    for feat in ["preloadAround", "fps", "keyHandler",
                 "toggleFav", "exportFavs", "statusLine", "exifLine",
                 "frameUrl", "originalUrl", "imgError"]:
        assert feat in js, f"missing: {feat}"

def test_css_has_cloak():
    css = (WEB/"css"/"site.css").read_text()
    assert "[x-cloak]" in css
