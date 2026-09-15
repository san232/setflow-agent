"""Tool-specific argument models. Strict JSON schemas derive from these."""

from app.application.schemas import Command, ExportFormat, Identifier, SongPatch


class NoArguments(Command):
    """A tool without parameters."""


class SongIdentifier(Command):
    """An unambiguous existing song ID."""

    song_id: Identifier


class UpdateSong(Command):
    """Explicit target and editable fields."""

    song_id: Identifier
    changes: SongPatch


class PlaylistIdentifier(Command):
    """An existing generated playlist."""

    playlist_id: Identifier


class ExportPlaylist(PlaylistIdentifier):
    """A local download, never an external-service playlist creation."""

    format: ExportFormat

