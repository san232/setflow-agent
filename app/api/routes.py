"""REST endpoints delegate to application use cases."""

from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, Query, Response
from fastapi.responses import FileResponse
from sqlalchemy import text

from app.api.dependencies import ServiceDependency
from app.api.dto import ChatView, MusicSearchQuery, PlaylistView, SongView, ToolLogView
from app.application.ports import JsonObject
from app.application.schemas import ChatRequest, ExportFormat, ExportRequest, GeneratePlaylist, SongCreate, SongPatch
from app.config import PROJECT_ROOT
from app.domain.curves import MoodCurve, PRESET_LABELS
from app.domain.models import PRESETS

router = APIRouter()


@router.get("/api/music/search", tags=["music"])
def search_music(command: Annotated[MusicSearchQuery, Query()], services: ServiceDependency) -> JsonObject:
    """Search public YouTube Music metadata without changing the library."""
    return services.music_search.search(command)


@router.get("/health", tags=["status"])
def health(services: ServiceDependency) -> JsonObject:
    """Confirm database connectivity and report the actual agent mode."""
    with services.database.engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    settings = services.agent.settings
    return {"status": "ok", "mode": settings.mode, "model": settings.model if settings.mode == "openai" else None,
            "public_demo": settings.public_demo,
            "agent_ready": settings.mode == "demo" or bool(settings.model),
            "notice": "Demo Mode · 제한된 규칙 Router" if settings.mode == "demo" else "OpenAI Mode · Responses API",
            "prototype_notice": "사용자 입력 분위기 수치에 기반한 Prototype"}


@router.post("/api/songs", status_code=201, response_model=SongView, tags=["songs"])
def add_song(command: SongCreate, services: ServiceDependency) -> JsonObject:
    return asdict(services.songs.add(command))


@router.get("/api/songs", response_model=list[SongView], tags=["songs"])
def list_songs(services: ServiceDependency) -> list[JsonObject]:
    return [asdict(s) for s in services.songs.list()]


@router.patch("/api/songs/{song_id}", response_model=SongView, tags=["songs"])
def update_song(song_id: int, command: SongPatch, services: ServiceDependency) -> JsonObject:
    return asdict(services.songs.update(song_id, command))


@router.delete("/api/songs/{song_id}", status_code=204, tags=["songs"])
def delete_song(song_id: int, services: ServiceDependency) -> Response:
    services.songs.delete(song_id)
    return Response(status_code=204)


@router.post("/api/playlists/generate", response_model=PlaylistView, status_code=201, tags=["playlists"])
def generate_playlist(command: GeneratePlaylist, services: ServiceDependency) -> JsonObject:
    return services.playlists.generate(command)


@router.get("/api/playlists", tags=["playlists"])
def list_playlists(services: ServiceDependency) -> list[JsonObject]:
    return services.playlists.list()


@router.get("/api/playlists/{playlist_id}", response_model=PlaylistView, tags=["playlists"])
def get_playlist(playlist_id: int, services: ServiceDependency) -> JsonObject:
    return services.playlists.get(playlist_id)


@router.get("/api/playlists/{playlist_id}/explanation", tags=["playlists"])
def explain_playlist(playlist_id: int, services: ServiceDependency) -> JsonObject:
    return services.playlists.explain(playlist_id)


def export_response(playlist_id: int, format: str, services: ServiceDependency) -> Response:
    result = services.exporters.render(services.playlists.get(playlist_id), format)
    return Response(result.content, media_type=result.media_type,
        headers={"Content-Disposition": f'attachment; filename="{result.filename}"',
                 "X-SetFlow-Missing-Media": "true" if any("재생 위치가 없어" in w for w in result.warnings) else "false",
                 "X-SetFlow-Webpage-Links": "true" if any("웹페이지 링크" in w for w in result.warnings) else "false"})


@router.post("/api/playlists/{playlist_id}/export", tags=["exports"], response_class=Response,
             responses={200: {"content": {"application/json": {}, "audio/x-mpegurl": {}}}})
def export_playlist(playlist_id: int, command: ExportRequest, services: ServiceDependency) -> Response:
    return export_response(playlist_id, command.format, services)


@router.get("/api/playlists/{playlist_id}/download", tags=["exports"], response_class=Response)
def download_playlist(playlist_id: int, format: ExportFormat, services: ServiceDependency) -> Response:
    return export_response(playlist_id, format, services)


@router.post("/api/agent/chat", response_model=ChatView, tags=["agent"])
def chat(command: ChatRequest, services: ServiceDependency) -> JsonObject:
    return services.agent.chat(command)


@router.get("/api/tool-logs", response_model=list[ToolLogView], tags=["agent"])
def tool_logs(services: ServiceDependency, limit: Annotated[int, Query(ge=1, le=100)] = 30) -> list[JsonObject]:
    return services.logs.list(limit)


@router.get("/api/tools", tags=["agent"])
def tools(services: ServiceDependency) -> list[JsonObject]:
    return services.registry.openai_tools()


@router.get("/api/presets", tags=["playlists"])
def presets(services: ServiceDependency) -> list[JsonObject]:
    songs = services.songs.list()
    return [{"id": p, "label": PRESET_LABELS[p],
             "targets": MoodCurve.create(p, songs).targets(21) if p != "auto" or songs else []} for p in PRESETS]


@router.post("/api/sample-data", tags=["songs"])
def sample_data(services: ServiceDependency) -> JsonObject:
    return services.songs.seed(PROJECT_ROOT / "data" / "king_gnu_songs.json")


@router.get("/api/catalog/king-gnu", tags=["songs"], response_class=FileResponse)
def king_gnu_catalog() -> FileResponse:
    """Read-only research provenance, independent of the user's editable ratings."""
    return FileResponse(PROJECT_ROOT / "data" / "king_gnu_profiles.json", media_type="application/json")
