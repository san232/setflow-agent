"""Chat orchestration, explicit context, and user-visible tool evidence."""

from threading import Lock
from uuid import uuid4

from app.agent.demo import DemoRouter
from app.agent.executor import ToolExecutor
from app.agent.openai_agent import OpenAIAgent
from app.application.errors import AppError
from app.application.ports import JsonObject
from app.application.schemas import ChatRequest
from app.config import Settings
from app.infrastructure.repositories import ConversationRepository


class AgentService:
    """Serialize chats in this single-process MVP to prevent context races."""

    def __init__(self, settings: Settings, executor: ToolExecutor, conversations: ConversationRepository,
                 openai_agent: OpenAIAgent) -> None:
        self.settings = settings
        self.executor = executor
        self.conversations = conversations
        self.openai_agent = openai_agent
        self.demo = DemoRouter()
        self.lock = Lock()

    def chat(self, command: ChatRequest) -> JsonObject:
        if not self.lock.acquire(blocking=False):
            raise AppError("다른 Agent 요청을 처리 중입니다. 잠시 후 다시 시도하세요.", 409)
        try:
            return self._chat(command)
        finally:
            self.lock.release()

    def _chat(self, command: ChatRequest) -> JsonObject:
        conversation_id = command.conversation_id or uuid4().hex
        state = self.conversations.get(conversation_id)
        if command.conversation_id and state is None:
            raise AppError("대화를 찾을 수 없습니다. 새 대화를 시작하세요.", 404)
        state = state or {}
        if command.playlist_id is not None:
            state["last_playlist_id"] = command.playlist_id
        if command.song_id is not None:
            state["last_song_id"] = command.song_id
        traces: list[JsonObject] = []

        def execute(name: str, arguments: JsonObject) -> JsonObject:
            raw: str | JsonObject = arguments
            call_id = uuid4().hex
            if "__raw_arguments__" in arguments:
                raw = str(arguments["__raw_arguments__"])
                call_id = str(arguments["__call_id__"])
            trace = self.executor.execute(name, raw, user_request=command.message,
                conversation_id=conversation_id, call_id=call_id, mode=self.settings.mode)
            traces.append(trace)
            result = trace["result"]
            if trace["success"] and isinstance(result, dict):
                if name in ("add_song", "update_song"):
                    state["last_song_id"] = result["id"]
                elif name == "delete_song" and state.get("last_song_id") == result.get("deleted_song_id"):
                    state.pop("last_song_id", None)
                elif name in ("generate_playlist", "get_playlist", "explain_playlist"):
                    state["last_playlist_id"] = result["id"]
            return trace

        router = self.demo if self.settings.mode == "demo" else self.openai_agent
        answer = router.run(command.message, state, execute)
        history = state.get("history", [])
        if not isinstance(history, list):
            history = []
        state["history"] = (history + [{"role": "user", "content": command.message},
                            {"role": "assistant", "content": answer.message}])[-12:]
        self.conversations.save(conversation_id, state)
        download_url = next((trace["result"].get("download_url") for trace in reversed(traces)
            if trace["success"] and isinstance(trace["result"], dict) and "download_url" in trace["result"]), None)
        return {"conversation_id": conversation_id, "mode": self.settings.mode, "message": answer.message,
            "needs_input": answer.needs_input, "tool_calls": traces,
            "playlist_id": state.get("last_playlist_id"), "song_id": state.get("last_song_id"),
            "download_url": download_url}
