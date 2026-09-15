from copy import deepcopy
from pathlib import Path

from fastapi.testclient import TestClient
from openai.types.responses import (Response, ResponseFunctionToolCall, ResponseInputItemParam,
    ResponseOutputMessage, ResponseOutputText, ResponseReasoningItem)

from app.application.ports import JsonObject
from app.config import Settings
from app.main import create_app


def call(call_id: str, name: str, arguments: str) -> ResponseFunctionToolCall:
    return ResponseFunctionToolCall(type="function_call", call_id=call_id, name=name, arguments=arguments)


def response(*outputs: object) -> Response:
    return Response.model_construct(status="completed", output=list(outputs))


def final_response() -> Response:
    message = ResponseOutputMessage(id="message_fixture", type="message", role="assistant", status="completed",
        content=[ResponseOutputText(type="output_text", text="조회 결과입니다.", annotations=[])])
    return response(message)


class ScriptedGateway:
    """Fake only the external API boundary, leaving real tools and SQLite active."""

    def __init__(self, responses: list[Response]) -> None:
        self.responses = responses
        self.inputs: list[list[ResponseInputItemParam]] = []

    def respond(self, inputs: list[ResponseInputItemParam], tools: list[JsonObject], instructions: str) -> Response:
        self.inputs.append(deepcopy(inputs))
        return self.responses.pop(0)


def settings(tmp_path: Path) -> Settings:
    # A conspicuously fake fixture label, never resembling an actual API secret.
    return Settings(db_path=tmp_path / "openai-mock.db", api_key="offline-test-placeholder", model="fixture-model")


def test_tool_results_and_reasoning_are_returned(tmp_path: Path) -> None:
    reasoning = ResponseReasoningItem(id="reason_fixture", type="reasoning", summary=[], encrypted_content="fixture-context")
    gateway = ScriptedGateway([response(reasoning, call("call_one", "list_songs", "{}")), final_response()])
    with TestClient(create_app(settings(tmp_path), gateway)) as client:
        reply = client.post("/api/agent/chat", json={"message": "곡 목록"}).json()
        assert reply["mode"] == "openai"
        assert reply["tool_calls"][0]["success"]
        second = gateway.inputs[1]
        assert any(getattr(item, "type", None) == "reasoning" for item in second)
        assert any(isinstance(item, dict) and item.get("call_id") == "call_one" and item.get("type") == "function_call_output" for item in second)


def test_duplicate_call_id_does_not_repeat_write(tmp_path: Path) -> None:
    args = '{"title":"한 곡","artist":"테스트","energy":50,"valence":50,"tension":50,"density":50,"closure":50}'
    gateway = ScriptedGateway([response(call("same_call", "add_song", args)), response(call("same_call", "add_song", args)), final_response()])
    with TestClient(create_app(settings(tmp_path), gateway)) as client:
        reply = client.post("/api/agent/chat", json={"message": "한 곡 등록"}).json()
        assert len(reply["tool_calls"]) == 1
        assert len(client.get("/api/songs").json()) == 1


def test_invalid_arguments_and_unknown_tool_are_logged(tmp_path: Path) -> None:
    gateway = ScriptedGateway([response(call("bad_json", "add_song", "{"), call("unknown", "execute_sql", "{}"),
        call("invalid", "delete_song", '{"song_id":1,"extra":true}')), final_response()])
    with TestClient(create_app(settings(tmp_path), gateway)) as client:
        reply = client.post("/api/agent/chat", json={"message": "테스트"}).json()
        assert len(reply["tool_calls"]) == 3
        assert all(not t["success"] for t in reply["tool_calls"])
        assert len(client.get("/api/tool-logs").json()) == 3


def test_loop_limit_is_reported(tmp_path: Path) -> None:
    configured = Settings(db_path=tmp_path / "limit.db", api_key="offline-test-placeholder", model="fixture-model", max_tool_rounds=1)
    gateway = ScriptedGateway([response(call("one", "list_songs", "{}"))])
    with TestClient(create_app(configured, gateway)) as client:
        reply = client.post("/api/agent/chat", json={"message": "목록"}).json()
        assert reply["needs_input"]
        assert "상한" in reply["message"]


def test_missing_model_does_not_crash_server(tmp_path: Path) -> None:
    with TestClient(create_app(Settings(db_path=tmp_path / "model.db", api_key="offline-test-placeholder"))) as client:
        assert client.get("/health").status_code == 200
        reply = client.post("/api/agent/chat", json={"message": "목록"}).json()
        assert reply["needs_input"] and "OPENAI_MODEL" in reply["message"]

