"""Choose an implemented exporter from an explicit allowlist."""

from app.application.errors import AppError
from app.application.ports import JsonObject
from app.exporters.base import ExportedFile, PlaylistExporter
from app.exporters.formats import JsonExporter, M3UExporter


class ExportService:
    """Register an additional real adapter here when adding a future format."""

    def __init__(self) -> None:
        self.exporters: dict[str, PlaylistExporter] = {"json": JsonExporter(), "m3u": M3UExporter()}

    def render(self, playlist: JsonObject, format: str) -> ExportedFile:
        exporter = self.exporters.get(format)
        if exporter is None:
            raise AppError("지원하는 Export 형식은 json, m3u입니다.", 422)
        return exporter.export(playlist)

