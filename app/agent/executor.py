"""Validate, execute and audit every selected tool, including failed attempts."""

import json
from datetime import datetime, timezone

from pydantic import ValidationError

from app.application.errors import AppError
from app.application.ports import JsonObject
from app.infrastructure.repositories import LogRepository
from app.tools.handlers import ToolContext
from app.tools.registry import ToolRegistry


class ToolExecutor:
    """An execution boundary shared by Demo and OpenAI modes."""

    def __init__(self, registry: ToolRegistry, context: ToolContext, logs: LogRepository) -> None:
        self.registry = registry
        self.context = context
        self.logs = logs

    def execute(self, name: str, raw_arguments: str | JsonObject, *, user_request: str,
                conversation_id: str, call_id: str, mode: str) -> JsonObject:
        """Return structured evidence; errors do not masquerade as successful writes."""
        arguments: JsonObject = {}
        success = False
        try:
            if isinstance(raw_arguments, str):
                decoded = json.loads(raw_arguments)
                if not isinstance(decoded, dict):
                    raise AppError("Tool arguments는 JSON 객체여야 합니다.", 422)
                arguments = decoded
            else:
                arguments = raw_arguments
            result = self.registry.invoke(name, arguments, self.context)
            success = True
            summary = summarize(name, result)
        except json.JSONDecodeError:
            arguments = {"invalid_json": str(raw_arguments)[:2000]}
            result = {"error": "Tool arguments JSON을 해석할 수 없습니다.", "status_code": 422}
            summary = str(result["error"])
        except ValidationError as error:
            message = "; ".join(f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in error.errors(include_input=False))
            result = {"error": message, "status_code": 422}
            summary = message
        except AppError as error:
            result = {"error": error.message, "status_code": error.status_code}
            summary = error.message
        trace: JsonObject = {"user_request": user_request, "tool_name": name, "arguments": arguments,
            "success": success, "result_summary": summary, "created_at": datetime.now(timezone.utc).isoformat(),
            "conversation_id": conversation_id, "call_id": call_id, "mode": mode}
        return {**self.logs.append(trace), "result": result}


def summarize(name: str, result: JsonObject) -> str:
    """Short factual text rather than fabricated model explanations."""
    if name == "list_songs":
        songs = result.get("songs", [])
        return f"등록된 곡 {len(songs) if isinstance(songs, list) else 0}개 조회"
    if name in ("add_song", "update_song"):
        return f"곡 #{result['id']} · {result['artist']} — {result['title']} " + ("등록" if name == "add_song" else "수정")
    if name == "delete_song":
        return f"곡 #{result['deleted_song_id']} 삭제"
    if name == "export_playlist":
        return f"{str(result['format']).upper()} 파일 준비. " + " ".join(str(w) for w in result.get("warnings", []) or [])
    return str(result.get("summary", "Playlist 조회 완료"))
