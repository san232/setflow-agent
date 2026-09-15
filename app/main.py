"""Application factory and composition root. Run with python -m uvicorn app.main:app."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import OperationalError

from app.agent.executor import ToolExecutor
from app.agent.openai_agent import OpenAIAgent, ResponsesGateway, SDKGateway
from app.agent.service import AgentService
from app.api.dependencies import Services
from app.api.routes import router
from app.application.errors import AppError
from app.application.services import PlaylistService, SongService
from app.config import PROJECT_ROOT, Settings
from app.exporters.service import ExportService
from app.infrastructure.database import Database
from app.infrastructure.repositories import ConversationRepository, LogRepository, SqlPlaylistRepository, SqlSongRepository
from app.tools.handlers import ToolContext
from app.tools.registry import ToolRegistry


def create_app(settings: Settings | None = None, gateway: ResponsesGateway | None = None) -> FastAPI:
    """Inject settings and a gateway to run the entire default suite without a key."""
    config = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        database = Database(config.db_path)
        database.initialize()
        songs = SongService(SqlSongRepository(database))
        if config.auto_seed:
            songs.seed(PROJECT_ROOT / "data" / "king_gnu_songs.json")
        playlists = PlaylistService(songs, SqlPlaylistRepository(database))
        registry = ToolRegistry()
        logs = LogRepository(database)
        executor = ToolExecutor(registry, ToolContext(songs, playlists), logs)
        sdk = gateway or SDKGateway(config)
        agent = AgentService(config, executor, ConversationRepository(database), OpenAIAgent(config, registry, sdk))
        application.state.services = Services(songs, playlists, agent, logs, registry, ExportService(), database)
        try:
            yield
        finally:
            if isinstance(sdk, SDKGateway):
                sdk.close()
            database.close()

    application = FastAPI(title="SetFlow Agent", version="0.1.0", lifespan=lifespan,
        description="수동 분위기 수치 기반 Playlist Prototype. Demo Mode와 Responses API Tool Calling을 지원합니다.")
    application.include_router(router)
    static_path = PROJECT_ROOT / "app" / "static"
    application.mount("/static", StaticFiles(directory=static_path, check_dir=False), name="static")

    @application.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(static_path / "index.html")

    @application.exception_handler(AppError)
    async def application_error(request: Request, error: AppError) -> JSONResponse:
        return JSONResponse(status_code=error.status_code, content={"detail": error.message})

    @application.exception_handler(RequestValidationError)
    async def validation_error(request: Request, error: RequestValidationError) -> JSONResponse:
        errors = [{"field": ".".join(str(p) for p in e["loc"]), "message": e["msg"]} for e in error.errors()]
        return JSONResponse(status_code=422, content={"detail": "입력값을 확인하세요. 분위기 수치는 0~100 정수입니다.", "errors": errors})

    @application.exception_handler(OperationalError)
    async def database_error(request: Request, error: OperationalError) -> JSONResponse:
        return JSONResponse(status_code=503, content={"detail": "DB 작업에 실패했습니다. 파일 쓰기 권한, 동기화 상태와 다른 서버 프로세스를 확인하세요."})

    return application


app = create_app()
