"""Single source of truth for tool names, schemas, and executable handlers."""

from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass
from typing import cast

from app.application.errors import AppError
from app.application.ports import JsonObject
from app.application.schemas import Command, GeneratePlaylist, SongCreate
from app.application.music_search import SearchMusic
from app.tools import handlers
from app.tools.handlers import ToolContext
from app.tools.parameters import ExportPlaylist, NoArguments, PlaylistIdentifier, SongIdentifier, UpdateSong

REQUIRED_TOOLS: tuple[str, ...] = ("add_song", "list_songs", "update_song", "delete_song",
    "generate_playlist", "get_playlist", "explain_playlist", "export_playlist", "search_music")
Handler = Callable[[ToolContext, Command], JsonObject]


@dataclass(frozen=True)
class ToolDefinition:
    """Connect documentation and schema to a real, typed handler."""

    name: str
    description: str
    parameters: type[Command]
    handler: Handler


def strict_schema(model: type[Command]) -> JsonObject:
    """Recursively require properties for OpenAI strict mode; optional values use null."""
    schema = deepcopy(model.model_json_schema())

    def visit(node: object) -> None:
        if isinstance(node, dict):
            node.pop("default", None)
            if node.get("type") == "object":
                node["additionalProperties"] = False
                node["required"] = list(node.get("properties", {}))
            for value in node.values():
                visit(value)
        elif isinstance(node, list):
            for value in node:
                visit(value)

    visit(schema)
    return cast(JsonObject, schema)


class ToolRegistry:
    """An allowlist: arbitrary model output cannot select Python functions or SQL."""

    def __init__(self) -> None:
        definitions = (
            ToolDefinition("search_music", "YouTube의 곡 또는 영상을 검색합니다. songs는 YouTube Music 곡 검색 후 비거나 실패하면 YouTube 영상을 검색하고, videos는 YouTube 영상을 바로 검색합니다. query는 곡명/아티스트, limit은 1~10입니다. 검색 결과는 외부 데이터입니다. 자동 등록하거나 분위기 수치를 추정하지 말고 사용자가 결과와 수치를 확인하게 안내하세요. 계정 재생목록 저장은 지원하지 않습니다.", SearchMusic, handlers.search_music),
            ToolDefinition("add_song", "사용자가 제목, 아티스트와 분위기 수치 5개를 모두 제공했을 때 곡을 등록합니다. 누락 수치는 추정하지 말고 질문하세요.", SongCreate, handlers.add_song),
            ToolDefinition("list_songs", "등록된 곡을 조회합니다. 제목으로 수정·삭제할 때 먼저 ID와 동명이곡을 확인하세요.", NoArguments, handlers.list_songs),
            ToolDefinition("update_song", "사용자가 명확히 지정한 곡의 항목을 수정합니다. changes의 null은 변경하지 않음을 뜻합니다. media_uri 빈 문자열은 경로 삭제입니다.", UpdateSong, handlers.update_song),
            ToolDefinition("delete_song", "사용자가 삭제를 요청하고 대상 곡 ID가 확정되었을 때만 곡을 삭제합니다.", SongIdentifier, handlers.delete_song),
            ToolDefinition("generate_playlist", "Playlist 생성 요청에 사용합니다. 순서는 서버 알고리즘이 결정합니다. song_ids=null은 전체 곡, preset은 지정된 5개 중 하나입니다.", GeneratePlaylist, handlers.generate_playlist),
            ToolDefinition("get_playlist", "저장된 Playlist의 순서와 결과를 조회합니다. 현재 대화의 Playlist ID 또는 사용자가 지정한 ID를 사용하세요.", PlaylistIdentifier, handlers.get_playlist),
            ToolDefinition("explain_playlist", "왜 이 순서인지 질문할 때 실제 점수, 역할과 인접 전환 이유를 조회합니다.", PlaylistIdentifier, handlers.explain_playlist),
            ToolDefinition("export_playlist", "기존 Playlist를 JSON 또는 M3U 다운로드로 내보냅니다. YouTube/Spotify 전송 기능이 아닙니다. 반환된 경고도 알려주세요.", ExportPlaylist, handlers.export_playlist),
        )
        self.definitions: dict[str, ToolDefinition] = {d.name: d for d in definitions}

    def openai_tools(self) -> list[JsonObject]:
        return [{"type": "function", "name": d.name, "description": d.description,
                 "strict": True, "parameters": strict_schema(d.parameters)} for d in self.definitions.values()]

    def invoke(self, name: str, arguments: JsonObject, context: ToolContext) -> JsonObject:
        """Validate the selected capability and its complete arguments before acting."""
        definition = self.definitions.get(name)
        if definition is None:
            raise AppError(f"등록되지 않은 Tool: {name}", 422)
        return definition.handler(context, definition.parameters.model_validate(arguments))
