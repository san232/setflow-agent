from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    settings = Settings(db_path=tmp_path / "test.db", demo_mode=True)
    with TestClient(create_app(settings)) as test_client:
        yield test_client


def payload(energy: int = 50) -> dict[str, object]:
    return dict(title="시험 곡", artist="시연", energy=energy, valence=50,
                tension=50, density=50, closure=80, media_uri=None)


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["mode"] == "demo"


def test_song_crud_and_validation(client: TestClient) -> None:
    assert client.post("/api/songs", json=payload(101)).status_code == 422
    created = client.post("/api/songs", json=payload())
    assert created.status_code == 201
    song_id = created.json()["id"]
    assert client.patch(f"/api/songs/{song_id}", json={"tension": 60}).json()["tension"] == 60
    assert len(client.get("/api/songs").json()) == 1
    assert client.delete(f"/api/songs/{song_id}").status_code == 204
    assert client.patch(f"/api/songs/{song_id}", json={"energy": 20}).status_code == 404
    assert client.delete(f"/api/songs/{song_id}").status_code == 404


def test_seed_playlist_exports_and_snapshot(client: TestClient) -> None:
    assert client.post("/api/sample-data").status_code == 200
    songs = client.get("/api/songs").json()
    assert len(songs) == 43
    assert {s["artist"] for s in songs} == {"King Gnu"}
    client.post("/api/sample-data")
    assert len(client.get("/api/songs").json()) == len(songs)
    created = client.post("/api/playlists/generate", json={
        "song_ids": [s["id"] for s in songs], "preset": "mid_peak", "name": "시연 플리"})
    assert created.status_code == 201
    playlist = created.json()
    playlist_id = playlist["id"]
    assert len(playlist["items"]) == len(songs)
    assert client.get(f"/api/playlists/{playlist_id}/explanation").status_code == 200
    exported = client.post(f"/api/playlists/{playlist_id}/export", json={"format": "json"})
    assert exported.json()["id"] == playlist_id
    m3u = client.post(f"/api/playlists/{playlist_id}/export", json={"format": "m3u"})
    assert m3u.text.startswith("#EXTM3U")
    assert "MISSING_MEDIA" in m3u.text
    first = playlist["items"][0]["song"]
    client.patch(f"/api/songs/{first['id']}", json={"title": "변경된 제목"})
    client.delete(f"/api/songs/{first['id']}")
    assert client.get(f"/api/playlists/{playlist_id}").json() == playlist


def test_demo_tools_and_follow_up(client: TestClient) -> None:
    client.post("/api/sample-data")
    listed = client.post("/api/agent/chat", json={"message": "현재 등록된 곡을 보여줘."}).json()
    assert listed["mode"] == "demo"
    assert listed["tool_calls"][0]["tool_name"] == "list_songs"
    conversation_id = listed["conversation_id"]
    generated = client.post("/api/agent/chat", json={"message": "중반 절정형으로 플레이리스트를 만들어줘.",
        "conversation_id": conversation_id}).json()
    assert generated["tool_calls"][-1]["tool_name"] == "generate_playlist"
    exported = client.post("/api/agent/chat", json={"message": "방금 만든 플리를 M3U로 내보내줘.",
        "conversation_id": conversation_id}).json()
    assert exported["tool_calls"][0]["tool_name"] == "export_playlist"
    assert exported["tool_calls"][0]["success"]
    assert client.get(exported["download_url"]).status_code == 200
    logs = client.get("/api/tool-logs").json()
    assert all("arguments" in log and "created_at" in log for log in logs)


def test_catalog_provenance_and_reseed_preserve_user_edits(client: TestClient) -> None:
    catalog = client.get("/api/catalog/king-gnu")
    assert catalog.status_code == 200
    original = catalog.json()
    assert len(original["profiles"]) == 43
    assert len(original["concerts"]) == 7
    assert all(p["source_ids"] for p in original["profiles"])
    assert client.post("/api/sample-data").json()["added"] == 43
    song = client.get("/api/songs").json()[0]
    changed = (song["energy"] + 1) % 101
    assert client.patch(f"/api/songs/{song['id']}", json={"energy": changed}).status_code == 200
    other = client.post("/api/songs", json=payload()).json()
    reseed = client.post("/api/sample-data").json()
    assert reseed["added"] == 0 and reseed["total"] == 44
    by_id = {s["id"]: s for s in client.get("/api/songs").json()}
    assert by_id[song["id"]]["energy"] == changed
    assert by_id[other["id"]] == other
    assert client.get("/api/catalog/king-gnu").json() == original


def test_partial_add_and_ambiguous_mutation(client: TestClient) -> None:
    response = client.post("/api/agent/chat", json={"message": "아이유의 라일락을 에너지 75, 밝기 85로 등록해줘."}).json()
    assert response["needs_input"]
    assert client.get("/api/songs").json() == []
    added = client.post("/api/agent/chat", json={"message": "긴장도 30, 밀도 70, 마무리 적합도 60",
        "conversation_id": response["conversation_id"]}).json()
    assert added["tool_calls"][-1]["tool_name"] == "add_song"
    assert client.get("/api/songs").json()[0]["energy"] == 75
    ambiguous = client.post("/api/agent/chat", json={"message": "이 곡 삭제해줘"}).json()
    assert ambiguous["needs_input"]
    assert len(client.get("/api/songs").json()) == 1
