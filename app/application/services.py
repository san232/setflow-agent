"""Application handlers with no FastAPI or OpenAI dependency."""

import json
from dataclasses import asdict, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import cast

from app.application.errors import AppError
from app.application.ports import JsonObject, PlaylistRepository, SongRepository
from app.application.schemas import GeneratePlaylist, SongCreate, SongPatch
from app.domain.models import Song
from app.domain.optimizer import optimize


class SongService:
    """Create, read, edit and delete subjective song metadata."""

    def __init__(self, repository: SongRepository) -> None:
        self.repository = repository

    def list(self) -> list[Song]:
        return self.repository.list()

    def get(self, song_id: int) -> Song:
        song = self.repository.get(song_id)
        if song is None:
            raise AppError(f"곡 ID {song_id}을 찾을 수 없습니다.", 404)
        return song

    def add(self, command: SongCreate) -> Song:
        return self.repository.add(command.model_dump())

    def update(self, song_id: int, command: SongPatch) -> Song:
        current = self.get(song_id)
        values = command.model_dump(exclude_none=True)
        if values.get("media_uri") == "":
            values["media_uri"] = None
        return self.repository.update(replace(current, **values))

    def delete(self, song_id: int) -> None:
        self.get(song_id)
        self.repository.delete(song_id)

    def seed(self, path: Path) -> JsonObject:
        """Load sample metadata once per title/artist pair; do not overwrite edits."""
        sample = json.loads(path.read_text(encoding="utf-8"))
        existing = {(s.title, s.artist) for s in self.list()}
        added = 0
        for entry in sample["songs"]:
            command = SongCreate.model_validate(entry)
            key = (command.title, command.artist)
            if key not in existing:
                self.add(command)
                existing.add(key)
                added += 1
        return {"added": added, "total": len(self.list()), "notice": sample["notice"]}


class PlaylistService:
    """Generate and retrieve reproducible playlist snapshots."""

    def __init__(self, songs: SongService, repository: PlaylistRepository) -> None:
        self.songs = songs
        self.repository = repository

    def generate(self, command: GeneratePlaylist) -> JsonObject:
        songs = self.songs.list() if command.song_ids is None else [self.songs.get(i) for i in command.song_ids]
        try:
            result = optimize(songs, command.preset)
        except ValueError as error:
            raise AppError(str(error), 422) from error
        snapshot = cast(JsonObject, json.loads(json.dumps(asdict(result), ensure_ascii=False)))
        snapshot.update(name=command.name, created_at=datetime.now(timezone.utc).isoformat(), algorithm_version="1")
        return self.repository.save(snapshot)

    def get(self, playlist_id: int) -> JsonObject:
        result = self.repository.get(playlist_id)
        if result is None:
            raise AppError(f"Playlist ID {playlist_id}을 찾을 수 없습니다.", 404)
        return result

    def list(self) -> list[JsonObject]:
        return self.repository.list()

    def explain(self, playlist_id: int) -> JsonObject:
        snapshot = self.get(playlist_id)
        return {"id": playlist_id, "summary": snapshot["summary"], "cost": snapshot["cost"],
                "fit_score": snapshot["fit_score"], "items": snapshot["items"]}

