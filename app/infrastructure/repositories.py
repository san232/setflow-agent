"""Concrete SQLite repositories, mapping ORM rows to plain domain values."""

from dataclasses import asdict

from sqlalchemy import select

from app.application.errors import AppError
from app.application.ports import JsonObject
from app.domain.models import Song
from app.infrastructure.database import ConversationRow, Database, LogRow, PlaylistRow, SongRow


def to_song(row: SongRow) -> Song:
    return Song(row.id, row.title, row.artist, row.energy, row.valence, row.tension,
                row.density, row.closure, row.media_uri)


class SqlSongRepository:
    """Persist songs in small transactions."""

    def __init__(self, database: Database) -> None:
        self.database = database

    def list(self) -> list[Song]:
        with self.database.sessions() as session:
            return [to_song(row) for row in session.scalars(select(SongRow).order_by(SongRow.id))]

    def get(self, song_id: int) -> Song | None:
        with self.database.sessions() as session:
            row = session.get(SongRow, song_id)
            return to_song(row) if row else None

    def add(self, values: JsonObject) -> Song:
        with self.database.sessions.begin() as session:
            row = SongRow(**values)
            session.add(row)
            session.flush()
            return to_song(row)

    def update(self, song: Song) -> Song:
        with self.database.sessions.begin() as session:
            row = session.get(SongRow, song.id)
            if row is None:
                raise AppError(f"곡 ID {song.id}을 찾을 수 없습니다.", 404)
            for key, value in asdict(song).items():
                setattr(row, key, value)
        return song

    def delete(self, song_id: int) -> None:
        with self.database.sessions.begin() as session:
            row = session.get(SongRow, song_id)
            if row is None:
                raise AppError(f"곡 ID {song_id}을 찾을 수 없습니다.", 404)
            session.delete(row)


class SqlPlaylistRepository:
    """Save results once, return the same snapshot after source-song edits."""

    def __init__(self, database: Database) -> None:
        self.database = database

    def save(self, snapshot: JsonObject) -> JsonObject:
        with self.database.sessions.begin() as session:
            row = PlaylistRow(snapshot=snapshot)
            session.add(row)
            session.flush()
            saved = {**snapshot, "id": row.id}
            row.snapshot = saved
            return saved

    def get(self, playlist_id: int) -> JsonObject | None:
        with self.database.sessions() as session:
            row = session.get(PlaylistRow, playlist_id)
            return row.snapshot if row else None

    def list(self) -> list[JsonObject]:
        with self.database.sessions() as session:
            rows = session.scalars(select(PlaylistRow).order_by(PlaylistRow.id.desc()).limit(100))
            return [{"id": r.id, "name": r.snapshot["name"], "preset": r.snapshot["preset"],
                     "created_at": r.snapshot["created_at"], "fit_score": r.snapshot["fit_score"]} for r in rows]


class LogRepository:
    """Persist user-visible tool traces independently of tool failures."""

    def __init__(self, database: Database) -> None:
        self.database = database

    def append(self, payload: JsonObject) -> JsonObject:
        with self.database.sessions.begin() as session:
            row = LogRow(payload=payload)
            session.add(row)
            session.flush()
            return {**payload, "id": row.id}

    def list(self, limit: int = 30) -> list[JsonObject]:
        with self.database.sessions() as session:
            return [{**row.payload, "id": row.id} for row in
                    session.scalars(select(LogRow).order_by(LogRow.id.desc()).limit(limit))]


class ConversationRepository:
    """Only chat context lives here; all song/playlist actions still use tools."""

    def __init__(self, database: Database) -> None:
        self.database = database

    def get(self, conversation_id: str) -> JsonObject | None:
        with self.database.sessions() as session:
            row = session.get(ConversationRow, conversation_id)
            return row.state if row else None

    def save(self, conversation_id: str, state: JsonObject) -> None:
        with self.database.sessions.begin() as session:
            session.merge(ConversationRow(id=conversation_id, state=state))
