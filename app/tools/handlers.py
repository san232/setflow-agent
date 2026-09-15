"""Small explicit adapters from validated tool commands to application use cases."""

from dataclasses import asdict, dataclass
from typing import cast

from app.application.ports import JsonObject
from app.application.schemas import Command, GeneratePlaylist, SongCreate
from app.application.services import PlaylistService, SongService
from app.tools.parameters import ExportPlaylist, PlaylistIdentifier, SongIdentifier, UpdateSong


@dataclass(frozen=True)
class ToolContext:
    """Only the use cases needed by the registered handlers."""

    songs: SongService
    playlists: PlaylistService


def add_song(context: ToolContext, command: Command) -> JsonObject:
    return asdict(context.songs.add(cast(SongCreate, command)))


def list_songs(context: ToolContext, command: Command) -> JsonObject:
    return {"songs": [asdict(s) for s in context.songs.list()]}


def update_song(context: ToolContext, command: Command) -> JsonObject:
    update = cast(UpdateSong, command)
    return asdict(context.songs.update(update.song_id, update.changes))


def delete_song(context: ToolContext, command: Command) -> JsonObject:
    song_id = cast(SongIdentifier, command).song_id
    context.songs.delete(song_id)
    return {"deleted_song_id": song_id}


def generate_playlist(context: ToolContext, command: Command) -> JsonObject:
    return context.playlists.generate(cast(GeneratePlaylist, command))


def get_playlist(context: ToolContext, command: Command) -> JsonObject:
    return context.playlists.get(cast(PlaylistIdentifier, command).playlist_id)


def explain_playlist(context: ToolContext, command: Command) -> JsonObject:
    return context.playlists.explain(cast(PlaylistIdentifier, command).playlist_id)


def export_playlist(context: ToolContext, command: Command) -> JsonObject:
    # Import at this boundary keeps the domain independent of serialization formats.
    from app.exporters.service import ExportService

    export = cast(ExportPlaylist, command)
    snapshot = context.playlists.get(export.playlist_id)
    rendered = ExportService().render(snapshot, export.format)
    return {"playlist_id": export.playlist_id, "format": export.format,
            "download_url": f"/api/playlists/{export.playlist_id}/download?format={export.format}",
            "warnings": list(rendered.warnings), "filename": rendered.filename}

