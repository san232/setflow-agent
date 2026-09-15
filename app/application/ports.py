"""Small persistence contracts consumed by use cases."""

from typing import Protocol

from pydantic import JsonValue

from app.domain.models import Song

JsonObject = dict[str, JsonValue]


class SongRepository(Protocol):
    """Storage operations required by song management."""

    def list(self) -> list[Song]: ...
    def get(self, song_id: int) -> Song | None: ...
    def add(self, values: JsonObject) -> Song: ...
    def update(self, song: Song) -> Song: ...
    def delete(self, song_id: int) -> None: ...


class PlaylistRepository(Protocol):
    """Snapshot persistence so later song edits cannot alter past explanations."""

    def save(self, snapshot: JsonObject) -> JsonObject: ...
    def get(self, playlist_id: int) -> JsonObject | None: ...
    def list(self) -> list[JsonObject]: ...

