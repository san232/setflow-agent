"""Public response models displayed in the OpenAPI documentation."""

from pydantic import BaseModel

from app.application.ports import JsonObject
from app.application.schemas import SongCreate


class SongView(SongCreate):
    """A registered song and its stable ID."""

    id: int


class PlaylistItemView(BaseModel):
    """Placement details from a saved snapshot."""

    position: int
    song: SongView
    target_energy: float
    actual_energy: int
    role: str
    transition_reason: str
    penalties: dict[str, float]


class PlaylistView(BaseModel):
    """Full generated playlist."""

    id: int
    name: str
    preset: str
    cost: float
    fit_score: float
    items: list[PlaylistItemView]
    summary: str
    created_at: str
    algorithm_version: str


class ToolLogView(BaseModel):
    """Selection and execution evidence persisted in SQLite."""

    id: int
    user_request: str
    tool_name: str
    arguments: JsonObject
    success: bool
    result_summary: str
    created_at: str
    conversation_id: str
    call_id: str
    mode: str


class ToolCallView(ToolLogView):
    """A tool trace with its current request's full result."""

    result: JsonObject


class ChatView(BaseModel):
    """Agent text and observable tool decisions."""

    conversation_id: str
    mode: str
    message: str
    needs_input: bool
    tool_calls: list[ToolCallView]
    playlist_id: int | None
    song_id: int | None
    download_url: str | None

