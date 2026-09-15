"""Run from the project root: python -m scripts.seed."""

import json

from app.application.services import SongService
from app.config import PROJECT_ROOT, Settings
from app.infrastructure.database import Database
from app.infrastructure.repositories import SqlSongRepository


def main() -> None:
    """Add samples without replacing existing songs or clearing the database."""
    database = Database(Settings.from_env().db_path)
    try:
        database.initialize()
        result = SongService(SqlSongRepository(database)).seed(PROJECT_ROOT / "data" / "king_gnu_songs.json")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        database.close()


if __name__ == "__main__":
    main()
