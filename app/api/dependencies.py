"""Typed access to the services assembled at application startup."""

from dataclasses import dataclass
from typing import Annotated, cast

from fastapi import Depends, Request

from app.agent.service import AgentService
from app.application.services import PlaylistService, SongService
from app.exporters.service import ExportService
from app.infrastructure.database import Database
from app.infrastructure.repositories import LogRepository
from app.tools.registry import ToolRegistry


@dataclass(frozen=True)
class Services:
    """One explicit composition container; domain models never read app state."""

    songs: SongService
    playlists: PlaylistService
    agent: AgentService
    logs: LogRepository
    registry: ToolRegistry
    exporters: ExportService
    database: Database


def get_services(request: Request) -> Services:
    return cast(Services, request.app.state.services)


ServiceDependency = Annotated[Services, Depends(get_services)]

