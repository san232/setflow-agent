import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.tools.handlers import ToolContext
from app.tools.registry import ToolRegistry


def test_every_handler_executes_its_use_case(tmp_path: Path) -> None:
    with TestClient(create_app(Settings(db_path=tmp_path / "tools.db", demo_mode=True))) as client:
        services = client.app.state.services
        context = ToolContext(services.songs, services.playlists)
        registry = ToolRegistry()
        added = registry.invoke("add_song", {"title": "실제 handler", "artist": "테스트", "energy": 50,
            "valence": 50, "tension": 50, "density": 50, "closure": 50}, context)
        sid = added["id"]
        assert registry.invoke("list_songs", {}, context)["songs"][0]["id"] == sid
        assert registry.invoke("update_song", {"song_id": sid, "changes": {"energy": 80}}, context)["energy"] == 80
        playlist = registry.invoke("generate_playlist", {"song_ids": [sid], "preset": "auto"}, context)
        pid = playlist["id"]
        assert registry.invoke("get_playlist", {"playlist_id": pid}, context) == playlist
        assert registry.invoke("explain_playlist", {"playlist_id": pid}, context)["items"]
        assert "download_url" in registry.invoke("export_playlist", {"playlist_id": pid, "format": "json"}, context)
        registry.invoke("delete_song", {"song_id": sid}, context)
        assert registry.invoke("list_songs", {}, context)["songs"] == []


def test_api_rejects_invalid_inputs_and_returns_real_exports(tmp_path: Path) -> None:
    with TestClient(create_app(Settings(db_path=tmp_path / "api.db", demo_mode=True))) as client:
        data = {"title": "Test", "artist": "Test", "energy": 20, "valence": 50, "tension": 50, "density": 50, "closure": 80}
        for bad in (True, 2.5, "30", -1, 101):
            assert client.post("/api/songs", json={**data, "energy": bad}).status_code == 422
        assert client.post("/api/songs", json={**data, "extra": "bad"}).status_code == 422
        assert client.post("/api/songs", json={**data, "media_uri": "https://example.com/a\n#EXTINF:1,b"}).status_code == 422
        song = client.post("/api/songs", json={**data, "media_uri": "https://example.com/track.mp3"}).json()
        assert client.patch(f"/api/songs/{song['id']}", json={}).status_code == 422
        assert client.post("/api/playlists/generate", json={"song_ids": []}).status_code == 422
        assert client.post("/api/playlists/generate", json={"song_ids": [song['id'], song['id']]}).status_code == 422
        assert client.post("/api/playlists/generate", json={"song_ids": [999]}).status_code == 404
        playlist = client.post("/api/playlists/generate", json={"preset": "auto"}).json()
        exported = client.post(f"/api/playlists/{playlist['id']}/export", json={"format": "m3u"})
        assert "https://example.com/track.mp3" in exported.text
        assert exported.headers["x-setflow-missing-media"] == "false"
        assert client.post(f"/api/playlists/{playlist['id']}/export", json={"format": "youtube"}).status_code == 422
        assert client.get("/api/playlists/999").status_code == 404
        assert client.get("/api/tool-logs?limit=1000").status_code == 422
        assert client.get("/docs").status_code == 200
        schema = client.get("/openapi.json").json()
        assert "/api/agent/chat" in schema["paths"]
        assert len(client.get("/api/tools").json()) == 8


def test_playlist_and_chat_context_survive_restart(tmp_path: Path) -> None:
    settings = Settings(db_path=tmp_path / "persistent.db", demo_mode=True)
    with TestClient(create_app(settings)) as client:
        client.post("/api/sample-data")
        reply = client.post("/api/agent/chat", json={"message": "중반 절정형으로 만들어줘"}).json()
    with TestClient(create_app(settings)) as client:
        followup = client.post("/api/agent/chat", json={"message": "왜 이 순서인지 설명해줘", "conversation_id": reply["conversation_id"]}).json()
        assert followup["tool_calls"][0]["tool_name"] == "explain_playlist"
        assert followup["playlist_id"] == reply["playlist_id"]
        assert len(client.get("/api/songs").json()) == 43


def test_presets_show_distinct_targets_and_multiple_sample_orders(tmp_path: Path) -> None:
    with TestClient(create_app(Settings(db_path=tmp_path / "presets.db", demo_mode=True))) as client:
        client.post("/api/sample-data")
        orders = []
        targets = []
        for preset in client.get("/api/presets").json():
            result = client.post("/api/playlists/generate", json={"preset": preset["id"]}).json()
            orders.append(tuple(i["song"]["id"] for i in result["items"]))
            targets.append(tuple(i["target_energy"] for i in result["items"]))
        # Two monotonic presets can legitimately select the same song permutation.
        assert len(set(targets)) == 5
        assert len(set(orders)) >= 3
