"""Explicit runtime settings; reading configuration never requires an API key."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    """Injected into the app factory so tests use isolated databases."""

    db_path: Path = PROJECT_ROOT / "data" / "setflow.db"
    api_key: str = ""
    model: str = ""
    demo_mode: bool = False
    max_tool_rounds: int = 6
    api_timeout: float = 30.0
    auto_seed: bool = False
    public_demo: bool = False

    @classmethod
    def from_env(cls) -> "Settings":
        """Load .env from the project root; existing environment values win."""
        load_dotenv(PROJECT_ROOT / ".env")
        path = Path(os.getenv("SETFLOW_DB_PATH", "data/setflow.db"))
        return cls(path if path.is_absolute() else PROJECT_ROOT / path,
                   os.getenv("OPENAI_API_KEY", "").strip(), os.getenv("OPENAI_MODEL", "").strip(),
                   os.getenv("SETFLOW_DEMO_MODE", "false").lower() == "true",
                   max(1, min(12, int(os.getenv("SETFLOW_MAX_TOOL_ROUNDS", "6")))),
                   max(1, float(os.getenv("SETFLOW_API_TIMEOUT", "30"))),
                   os.getenv("SETFLOW_AUTO_SEED", "false").lower() == "true",
                   os.getenv("SETFLOW_PUBLIC_DEMO", "false").lower() == "true")

    @property
    def mode(self) -> str:
        """Demo is explicit or selected when credentials are absent."""
        return "demo" if self.public_demo or self.demo_mode or not self.api_key else "openai"
