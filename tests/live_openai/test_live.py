"""Explicit opt-in: RUN_LIVE_OPENAI=1 python -m pytest -m live_openai."""

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.mark.live_openai
def test_real_responses_function_calling(tmp_path: Path) -> None:
    """Only list local test songs; never modify a production DB."""
    configured = Settings.from_env()
    if os.getenv("RUN_LIVE_OPENAI") != "1" or not configured.api_key or not configured.model:
        pytest.skip("Live test requires explicit opt-in, OPENAI_API_KEY, and OPENAI_MODEL.")
    settings = Settings(db_path=tmp_path / "live.db", api_key=configured.api_key, model=configured.model)
    with TestClient(create_app(settings)) as client:
        reply = client.post("/api/agent/chat", json={"message": "list_songs Tool을 사용해서 등록된 곡을 조회해줘."}).json()
        assert any(t["tool_name"] == "list_songs" and t["success"] for t in reply["tool_calls"])
