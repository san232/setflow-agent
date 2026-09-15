from app.agent.demo import DemoRouter
from app.application.ports import JsonObject


def test_negated_delete_does_not_execute() -> None:
    def forbidden(name: str, arguments: JsonObject) -> JsonObject:
        raise AssertionError("Negated requests must not call a tool.")

    answer = DemoRouter().run("곡 ID 1을 삭제하지 마", {}, forbidden)
    assert answer.needs_input


def test_pending_add_can_fill_title_and_artist() -> None:
    state: JsonObject = {}
    calls: list[JsonObject] = []

    def record(name: str, arguments: JsonObject) -> JsonObject:
        calls.append(arguments)
        return {"success": True, "tool_name": name, "result_summary": "등록 완료", "result": {"id": 1}}

    router = DemoRouter()
    assert router.run("에너지 50, 밝기 50, 긴장도 30, 밀도 40, 마무리 60으로 등록", state, record).needs_input
    assert not router.run("제목: 시험 곡, 아티스트: 시험 가수", state, record).needs_input
    assert calls[0]["title"] == "시험 곡"
