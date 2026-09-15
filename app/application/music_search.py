"""Read-only music discovery shared by REST and agent tools."""

from typing import Literal, Protocol
from urllib.parse import quote

from pydantic import Field, StrictInt

from app.application.ports import JsonObject
from app.application.schemas import Command


class SearchMusic(Command):
    """Search metadata only; selecting a result never registers a song."""

    query: str = Field(min_length=1, max_length=200)
    kind: Literal["songs", "videos"] = "songs"
    limit: StrictInt = Field(default=8, ge=1, le=10)


class MusicSearchProvider(Protocol):
    def search(self, query: str, kind: str, limit: int) -> list[JsonObject]: ...


class MusicSearchService:
    def __init__(self, provider: MusicSearchProvider) -> None:
        self.provider = provider

    def search(self, command: SearchMusic) -> JsonObject:
        results = self.provider.search(command.query, command.kind, command.limit)
        return {"query": command.query, "source": results[0].get("source", "YouTube") if results else "YouTube",
                "results": results,
                "search_url": "https://music.youtube.com/search?q=" + quote(command.query, safe=""),
                "notice": "검색 결과를 선택해 등록 폼에서 확인하세요. 검색은 보관함이나 계정 재생목록을 변경하지 않습니다."}
