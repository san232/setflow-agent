"""SQLAlchemy 2 engine and tables for a local single-server MVP."""

from pathlib import Path

from sqlalchemy import JSON, String, Text, create_engine
from sqlalchemy.engine import Engine, URL
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, Session

from app.application.ports import JsonObject


class Base(DeclarativeBase):
    """Shared metadata for infrastructure tables only."""


class SongRow(Base):
    """Editable source song metadata."""

    __tablename__ = "songs"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    artist: Mapped[str] = mapped_column(String(200))
    energy: Mapped[int]
    valence: Mapped[int]
    tension: Mapped[int]
    density: Mapped[int]
    closure: Mapped[int]
    media_uri: Mapped[str | None] = mapped_column(Text, nullable=True)


class PlaylistRow(Base):
    """Self-contained snapshot, intentionally independent of source song deletion."""

    __tablename__ = "playlists"
    id: Mapped[int] = mapped_column(primary_key=True)
    snapshot: Mapped[JsonObject] = mapped_column(JSON)


class LogRow(Base):
    """One auditable tool attempt, including argument validation failures."""

    __tablename__ = "tool_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    payload: Mapped[JsonObject] = mapped_column(JSON)


class ConversationRow(Base):
    """Bounded local history and explicit last selected IDs."""

    __tablename__ = "conversations"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    state: Mapped[JsonObject] = mapped_column(JSON)


class Database:
    """Own the engine lifecycle; sessions are short-lived per operation."""

    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.engine: Engine = create_engine(URL.create("sqlite", database=str(path)),
            connect_args={"check_same_thread": False, "timeout": 15})
        self.sessions: sessionmaker[Session] = sessionmaker(self.engine, expire_on_commit=False)

    def initialize(self) -> None:
        Base.metadata.create_all(self.engine)

    def close(self) -> None:
        self.engine.dispose()
