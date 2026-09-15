from app.exporters.formats import JsonExporter, M3UExporter
from app.application.ports import JsonObject


def test_m3u_real_references_preserve_order_and_escape_titles() -> None:
    playlist: JsonObject = {"id": 7, "name": "한글 목록", "items": [
        {"position": 1, "song": {"title": "첫 곡\n#EXTINF:99,injection", "artist": "가수", "media_uri": "C:\\Music\\first.mp3"}},
        {"position": 2, "song": {"title": "마지막 곡", "artist": "가수", "media_uri": "https://example.com/music/last.mp3"}}]}
    exported = M3UExporter().export(playlist)
    lines = exported.content.decode("utf-8").splitlines()
    assert lines[0] == "#EXTM3U"
    assert [line for line in lines if not line.startswith("#")] == ["C:\\Music\\first.mp3", "https://example.com/music/last.mp3"]
    assert sum(line.startswith("#EXTINF:") for line in lines) == 2
    assert not exported.warnings


def test_json_uses_utf8() -> None:
    assert "한글".encode() in JsonExporter().export({"id": 1, "name": "한글"}).content

