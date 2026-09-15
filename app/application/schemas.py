"""Validated commands shared by the API and tool registry."""

from typing import Annotated, Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator, model_validator

from app.domain.weights import DEFAULT_CONFIG

Mood = Annotated[StrictInt, Field(ge=0, le=100)]
Identifier = Annotated[StrictInt, Field(gt=0)]
Preset = Literal["gentle_rise", "mid_peak", "late_explosion", "calm_afterglow", "auto"]
ExportFormat = Literal["json", "m3u"]


def validate_media(value: str | None) -> str | None:
    """Keep one-line user media references; the server never fetches them."""
    if value is None or value == "":
        return value
    if any(ord(c) < 32 for c in value) or value.startswith("#"):
        raise ValueError("재생 위치에는 제어 문자나 #로 시작하는 값을 사용할 수 없습니다.")
    scheme = urlsplit(value).scheme.lower()
    if scheme and scheme not in ("https", "http", "file") and not (len(scheme) == 1 and value[1:3] in (":\\", ":/")):
        raise ValueError("재생 위치는 파일 경로 또는 http/https/file URI여야 합니다.")
    return value


class Command(BaseModel):
    """Unknown properties are rejected at every command boundary."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class SongCreate(Command):
    """All five subjective ratings must be provided by the user."""

    title: str = Field(min_length=1, max_length=200)
    artist: str = Field(min_length=1, max_length=200)
    energy: Mood
    valence: Mood
    tension: Mood
    density: Mood
    closure: Mood
    media_uri: str | None = Field(default=None, max_length=2000)
    _media = field_validator("media_uri")(validate_media)


class SongPatch(Command):
    """Null means unchanged; empty media_uri removes the playback reference."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    artist: str | None = Field(default=None, min_length=1, max_length=200)
    energy: Mood | None = None
    valence: Mood | None = None
    tension: Mood | None = None
    density: Mood | None = None
    closure: Mood | None = None
    media_uri: str | None = Field(default=None, max_length=2000)
    _media = field_validator("media_uri")(validate_media)

    @model_validator(mode="after")
    def require_change(self) -> "SongPatch":
        """Reject a patch without an explicit effective change."""
        if all(value is None for value in self.model_dump().values()):
            raise ValueError("수정할 항목을 하나 이상 입력하세요.")
        return self


class GeneratePlaylist(Command):
    """None selects all registered songs; an empty list is an error."""

    song_ids: list[Identifier] | None = Field(default=None, max_length=DEFAULT_CONFIG.max_playlist_songs)
    preset: Preset = "auto"
    name: str = Field(default="SetFlow Playlist", min_length=1, max_length=200)


class ExportRequest(Command):
    """Supported local export formats."""

    format: ExportFormat


class ChatRequest(Command):
    """Continue a server-side conversation by its opaque ID."""

    message: str = Field(min_length=1, max_length=4000)
    conversation_id: str | None = Field(default=None, pattern=r"^[0-9a-f]{32}$")
    playlist_id: Identifier | None = None
    song_id: Identifier | None = None
