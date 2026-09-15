from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.application.errors import AppError
from app.config import Settings
from app.main import create_app


class FakeSearch:
    def __init__(self):
        self.calls = []
        self.fail = False

    def search(self, query, kind, limit):
        self.calls.append((query, kind, limit))
        if self.fail:
            raise AppError("검색 연결 실패", 502)
        return [{"video_id": "ony539T074w", "title": "白日", "artist": "King Gnu", "source": "YouTube Music",
                 "media_uri": "https://music.youtube.com/watch?v=ony539T074w"}]


def test_search_is_read_only_then_selected_link_can_be_saved_and_exported(tmp_path: Path):
    provider = FakeSearch()
    with TestClient(create_app(Settings(db_path=tmp_path / "test.db", auto_seed=True), music_provider=provider)) as client:
        before = client.get("/api/songs").json()
        result = client.get("/api/music/search", params={"query": " King Gnu 白日 ", "kind": "songs", "limit": 3})
        assert result.status_code == 200
        assert provider.calls == [("King Gnu 白日", "songs", 3)]
        assert client.get("/api/songs").json() == before
        song = next(s for s in before if s["title"] == "白日")
        uri = result.json()["results"][0]["media_uri"]
        saved = client.patch(f"/api/songs/{song['id']}", json={"media_uri": uri}).json()
        assert saved == {**song, "media_uri": uri}
        assert len(client.get("/api/songs").json()) == 43
        playlist = client.post("/api/playlists/generate", json={"song_ids": [song["id"]]}).json()
        export = client.get(f"/api/playlists/{playlist['id']}/download?format=m3u")
        assert uri in export.text
        assert export.headers["X-SetFlow-Missing-Media"] == "false"
        assert export.headers["X-SetFlow-Webpage-Links"] == "true"


@pytest.mark.parametrize("params", [{"query": " "}, {"query": "x" * 201}, {"query": "x", "limit": 11},
                                   {"query": "x", "kind": "uploads"}, {"query": "x", "limit": 0}])
def test_invalid_search_never_calls_provider(tmp_path: Path, params):
    provider = FakeSearch()
    with TestClient(create_app(Settings(db_path=tmp_path / "test.db"), music_provider=provider)) as client:
        assert client.get("/api/music/search", params=params).status_code == 422
        assert not provider.calls


def test_agent_selects_search_tool_and_records_failure_without_writes(tmp_path: Path):
    provider = FakeSearch()
    with TestClient(create_app(Settings(db_path=tmp_path / "test.db"), music_provider=provider)) as client:
        reply = client.post("/api/agent/chat", json={"message": "유튜브에서 King Gnu 白日 검색해줘."}).json()
        trace = reply["tool_calls"][0]
        assert trace["tool_name"] == "search_music" and trace["success"]
        assert trace["arguments"]["query"] == "King Gnu 白日"
        assert len(trace["result"]["results"]) == 1
        assert client.get("/api/songs").json() == []
        provider.fail = True
        failure = client.post("/api/agent/chat", json={"message": "유튜브에서 역몽 찾아줘"}).json()
        assert not failure["tool_calls"][0]["success"]
        assert "검색 연결 실패" in failure["message"]
        assert client.get("/api/tool-logs").json()[0]["success"] is False
        assert client.get("/api/music/search?query=x").status_code == 502


def test_empty_or_negated_search_does_not_access_network(tmp_path: Path):
    provider = FakeSearch()
    with TestClient(create_app(Settings(db_path=tmp_path / "test.db"), music_provider=provider)) as client:
        for message in ("유튜브에서 검색해줘", "King Gnu 검색하지 마"):
            reply = client.post("/api/agent/chat", json={"message": message}).json()
            assert reply["needs_input"] and not reply["tool_calls"]
        assert not provider.calls
