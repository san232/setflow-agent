from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def test_hosted_catalog_survives_restart_without_overwriting_edits(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.config.load_dotenv", lambda *args: None)
    monkeypatch.delenv("SETFLOW_AUTO_SEED", raising=False)
    monkeypatch.setenv("SETFLOW_DB_PATH", str(tmp_path / "hosted.db"))
    monkeypatch.setenv("SETFLOW_PUBLIC_DEMO", "true")
    settings = Settings.from_env()
    assert settings.auto_seed is True
    with TestClient(create_app(settings)) as client:
        songs = client.get("/api/songs").json()
        assert len(songs) == 43
        assert {song["artist"] for song in songs} == {"King Gnu"}
        song_id = songs[0]["id"]
        assert client.patch(f"/api/songs/{song_id}", json={"energy": 1}).status_code == 200
    with TestClient(create_app(settings)) as client:
        songs = client.get("/api/songs").json()
        assert len(songs) == 43
        assert next(song for song in songs if song["id"] == song_id)["energy"] == 1


def test_public_demo_uses_real_tools_without_external_calls(tmp_path: Path) -> None:
    class NoExternalCalls:
        def respond(self, *args: object, **kwargs: object) -> None:
            raise AssertionError("Public demo must not call an external model")

    settings = Settings(db_path=tmp_path / "public.db", api_key="offline-test-placeholder",
                        model="test-model", auto_seed=True, public_demo=True)
    with TestClient(create_app(settings, gateway=NoExternalCalls())) as client:
        health = client.get("/health").json()
        assert health["mode"] == "demo" and health["public_demo"] is True
        result = client.post("/api/agent/chat", json={"message": "중반 절정형으로 플레이리스트를 만들어줘."})
        assert result.status_code == 200
        reply = result.json()
        assert reply["tool_calls"][0]["tool_name"] == "generate_playlist"
        playlist_id = reply["playlist_id"]
        playlist = client.get(f"/api/playlists/{playlist_id}").json()
        assert len(playlist["items"]) == 43
        download = client.get(f"/api/playlists/{playlist_id}/download?format=json")
        assert download.status_code == 200
        assert "attachment" in download.headers["content-disposition"]


def test_hosting_environment_flags_are_read(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SETFLOW_AUTO_SEED", "true")
    monkeypatch.setenv("SETFLOW_PUBLIC_DEMO", "true")
    settings = Settings.from_env()
    assert settings.auto_seed is True and settings.public_demo is True
    assert settings.mode == "demo"
