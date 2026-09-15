import pytest
import requests

from app.application.errors import AppError
from app.infrastructure import youtube_music as module


def item(video_id="ony539T074w"):
    return {"videoId": video_id, "title": "白日", "artists": [{"name": "King Gnu"}], "duration": "4:40"}


def test_normalization_rejects_invalid_urls_and_deduplicates():
    raw = [None, item("../../bad"), item(), item(), {"videoId": "abcdefghijk", "title": "No artist"}]
    result = module.normalize_results(raw, 8)
    assert len(result) == 1
    assert result[0]["media_uri"] == "https://music.youtube.com/watch?v=ony539T074w"
    assert result[0]["artist"] == "King Gnu"


def test_cache_is_bounded_and_does_not_share_mutable_results(monkeypatch):
    calls = []

    class FakeMusic:
        def __init__(self, **kwargs): pass
        def search(self, query, **kwargs):
            calls.append(query)
            return [item()]

    monkeypatch.setattr(module, "YTMusic", FakeMusic)
    provider = module.YouTubeMusicSearch()
    first = provider.search("King Gnu", "songs", 3)
    first[0]["title"] = "changed"
    assert provider.search("king gnu", "songs", 3)[0]["title"] == "白日"
    assert len(calls) == 1
    for i in range(70): provider.search(str(i), "songs", 3)
    assert len(provider.cache) == 64


@pytest.mark.parametrize("failure", [False, True])
def test_music_unavailable_falls_back_to_public_video_metadata(monkeypatch, failure):
    class FakeMusic:
        def __init__(self, **kwargs): pass
        def search(self, *args, **kwargs):
            if failure: raise requests.Timeout("upstream")
            return []

    monkeypatch.setattr(module, "YTMusic", FakeMusic)
    monkeypatch.setattr(module, "search_youtube", lambda q, n: [{"title": q, "source": "YouTube"}])
    assert module.YouTubeMusicSearch().search("King Gnu", "songs", 2)[0]["source"] == "YouTube"


def test_failure_is_sanitized_and_not_cached(monkeypatch):
    calls = []
    def fail(*args):
        calls.append(True)
        raise RuntimeError("private upstream details")
    monkeypatch.setattr(module, "search_youtube", fail)
    provider = module.YouTubeMusicSearch()
    for _ in range(2):
        with pytest.raises(AppError) as exc: provider.search("query", "videos", 3)
        assert exc.value.status_code == 502
        assert "private" not in exc.value.message
    assert len(calls) == 2 and not provider.cache


def test_video_search_cannot_download_or_trust_returned_urls(monkeypatch):
    class FakeVideo:
        def __init__(self, options):
            assert options["extract_flat"] is True and options["skip_download"] is True
            assert options["retries"] == 0 and options["playlistend"] == 2
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def extract_info(self, query, download):
            assert query == "ytsearch2:King Gnu" and download is False
            return {"entries": [{"id": "ony539T074w", "title": "King Gnu - 白日", "channel": "Uploader",
                                 "url": "javascript:alert(1)", "duration": 280}]}
    monkeypatch.setattr(module, "MetadataYoutubeDL", FakeVideo)
    result = module.search_youtube("King Gnu", 2)[0]
    assert result["youtube_url"] == "https://www.youtube.com/watch?v=ony539T074w"
    assert result["artist"] == "" and result["channel"] == "Uploader"
    assert result["duration"] == "4:40"


def test_search_budget_stops_network_work():
    with module.SearchSession() as session:
        session.remaining = 0
        with pytest.raises(requests.Timeout): session.get("https://music.youtube.com/")
