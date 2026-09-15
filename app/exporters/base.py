"""Exporter contract used by both implemented formats."""

from dataclasses import dataclass
from typing import Protocol

from app.application.ports import JsonObject


@dataclass(frozen=True)
class ExportedFile:
    """Bytes to download, with honest warnings about missing playback locations."""

    content: bytes
    media_type: str
    filename: str
    warnings: tuple[str, ...] = ()


class PlaylistExporter(Protocol):
    """A future adapter must actually implement export before being registered."""

    def export(self, playlist: JsonObject) -> ExportedFile: ...

