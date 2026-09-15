"""A deliberately limited Korean/English rule router, openly labeled Demo Mode."""

import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import cast

from app.application.ports import JsonObject
from app.domain.models import MOOD_FIELDS

Execute = Callable[[str, JsonObject], JsonObject]
ALIASES: dict[str, str] = {
    "energy": r"energy|에너지", "valence": r"valence|밝기|긍정도",
    "tension": r"tension|긴장도|긴장감", "density": r"density|밀도",
    "closure": r"closure|마무리\s*적합도|마무리도|마무리",
}


@dataclass(frozen=True)
class AgentAnswer:
    """Whether another user message is required to safely choose arguments."""

    message: str
    needs_input: bool = False


def mood_values(message: str) -> JsonObject:
    """Extract only explicit numeric ratings; no subjective values are inferred."""
    values: JsonObject = {}
    for field, aliases in ALIASES.items():
        match = re.search(rf"(?:{aliases})(?:를|을|는|은)?\s*[:=]?\s*(-?\d+(?:\.\d+)?)", message, re.I)
        if match:
            number = match.group(1)
            values[field] = float(number) if "." in number else int(number)
    return values


def explicit_id(message: str, playlist: bool = False) -> int | None:
    prefix = r"(?:플레이리스트|playlist|플리)\s*(?:id\s*)?[#:]?\s*(\d+)" if playlist else r"(?:곡\s*(?:id)?\s*[#:]?\s*(\d+)|(\d+)\s*번\s*곡|#(\d+))"
    match = re.search(prefix, message, re.I)
    return int(next(g for g in match.groups() if g is not None)) if match else None


def song_metadata(message: str) -> JsonObject:
    """Read supported title/artist patterns and explicit mood values."""
    values = mood_values(message)
    match = re.search(r"^\s*(.+?)의\s+(.+?)(?:을|를)\s+", message)
    if match:
        values.update(artist=match.group(1).strip(" '\"“”"), title=match.group(2).strip(" '\"“”"))
    else:
        for field, alias in (("title", "제목"), ("artist", "아티스트|가수")):
            match = re.search(rf"(?:{alias})\s*[:=]\s*([^,]+)", message)
            if match:
                values[field] = match.group(1).strip()
    return values


class DemoRouter:
    """Recognize documented patterns; ambiguous requests never silently mutate songs."""

    def run(self, message: str, state: JsonObject, execute: Execute) -> AgentAnswer:
        text = message.lower()
        if re.search(r"하지\s*마|하지\s*말|말고|않[아는]|안\s*(?:지워|삭제|등록|수정)|don't|do not", text):
            return AgentAnswer("부정 또는 복합 지시가 포함되어 실행하지 않았습니다. 원하는 작업 한 가지를 명확히 입력하세요.", True)
        if any(word in text for word in ("취소", "cancel")):
            state.pop("pending", None)
            return AgentAnswer("입력 대기를 취소했습니다.")
        if any(word in text for word in ("검색", "찾아", "search")):
            if any(word in text for word in ("보관함", "등록된", "내 곡")):
                return self._result(execute("list_songs", {}))
            query = re.sub(r"(?:유튜브\s*뮤직|유튜브|youtube\s*music|youtube)(?:에서|로)?", "", message, flags=re.I)
            query = re.sub(r"(?:검색|찾아)(?:해\s*줘|해\s*주세요|\s*줘|\s*주세요)?[.!?]*\s*$", "", query).strip()
            query = re.sub(r"^(?:검색|search)\s*[:：]?\s*", "", query, flags=re.I).strip(" \"'“”.!?")
            query = re.sub(r"(?:을|를)$", "", query).strip()
            if not query:
                return AgentAnswer("검색할 곡명이나 아티스트를 입력하세요. 예: ‘유튜브에서 King Gnu 白日 검색해줘’.", True)
            return self._result(execute("search_music", {"query": query, "kind": "songs", "limit": 8}))
        if any(word in text for word in ("유튜브", "youtube", "spotify", "스포티파이")):
            return AgentAnswer("YouTube Music 곡 검색은 가능합니다. ‘유튜브에서 King Gnu 白日 검색해줘’처럼 요청하세요. 계정 재생목록에 직접 저장하는 기능은 아직 없으며, JSON/M3U로 내보낼 수 있습니다.")
        pending = state.get("pending")
        if isinstance(pending, dict) and (song_metadata(message) or "등록" in text):
            values = cast(JsonObject, pending.get("values", {})) | song_metadata(message)
            return self._add(values, state, execute)
        if "등록" in text and not any(word in text for word in ("보여", "목록", "조회")):
            return self._add(song_metadata(message), state, execute)
        if any(word in text for word in ("수정", "바꿔", "변경", "삭제", "지워")):
            return self._mutate(message, state, execute)
        if any(word in text for word in ("내보", "export", "다운로드")):
            playlist_id = explicit_id(message, True) or state.get("last_playlist_id")
            if not playlist_id:
                return AgentAnswer("내보낼 Playlist ID를 지정하거나 먼저 Playlist를 생성하세요.", True)
            if "m3u" not in text and "json" not in text:
                return AgentAnswer("JSON 또는 M3U 중 내보낼 형식을 입력하세요.", True)
            return self._result(execute("export_playlist", {"playlist_id": playlist_id,
                "format": "m3u" if "m3u" in text else "json"}))
        if any(word in text for word in ("설명", "왜", "이유")):
            playlist_id = explicit_id(message, True) or state.get("last_playlist_id")
            if not playlist_id:
                return AgentAnswer("설명할 Playlist ID를 지정하거나 먼저 Playlist를 생성하세요.", True)
            return self._result(execute("explain_playlist", {"playlist_id": playlist_id}))
        if any(word in text for word in ("만들", "생성", "정렬")):
            preset = "auto"
            for code, words in (("gentle_rise", ("완만", "gentle_rise")), ("mid_peak", ("중반", "mid_peak")),
                ("late_explosion", ("후반 폭발", "후반에", "late_explosion")),
                ("calm_afterglow", ("여운", "잔잔", "calm_afterglow"))):
                if any(word in text for word in words):
                    preset = code
            selection = re.search(r"(?:곡\s*(?:id|번호)|song_ids)\s*[:=]\s*([\d,\s]+)", text)
            ids = [int(n) for n in re.findall(r"\d+", selection.group(1))] if selection else None
            return self._result(execute("generate_playlist", {"preset": preset, "song_ids": ids, "name": "Demo Playlist"}))
        if any(word in text for word in ("플레이리스트", "playlist", "플리")):
            playlist_id = explicit_id(message, True) or state.get("last_playlist_id")
            if playlist_id:
                return self._result(execute("get_playlist", {"playlist_id": playlist_id}))
        if any(word in text for word in ("목록", "보여", "조회", "list")):
            return self._result(execute("list_songs", {}))
        return AgentAnswer("Demo Mode는 정해진 표현만 지원합니다. 예: ‘현재 등록된 곡을 보여줘’, "
            "‘중반 절정형으로 플레이리스트를 만들어줘’, ‘곡 ID 1의 긴장도를 60으로 수정해줘’.", True)

    def _add(self, values: JsonObject, state: JsonObject, execute: Execute) -> AgentAnswer:
        missing = [f for f in ("title", "artist", *MOOD_FIELDS) if f not in values]
        if missing:
            state["pending"] = {"values": values}
            return AgentAnswer("등록하려면 다음 정보를 더 입력하세요: " + ", ".join(missing) +
                ". 예: ‘긴장도 30, 밀도 70, 마무리 적합도 60’. 취소하려면 ‘취소’라고 입력하세요.", True)
        trace = execute("add_song", values)
        if trace["success"]:
            state.pop("pending", None)
        else:
            state["pending"] = {"values": values}
        return self._result(trace)

    def _mutate(self, message: str, state: JsonObject, execute: Execute) -> AgentAnswer:
        deleting = any(word in message for word in ("삭제", "지워"))
        song_id = explicit_id(message)
        if song_id is None and any(word in message for word in ("이 곡", "방금 등록", "방금 수정")):
            song_id = cast(int | None, state.get("last_song_id"))
        if song_id is None:
            # Looking up a title is itself an auditable tool invocation.
            trace = execute("list_songs", {})
            result = trace.get("result", {})
            songs = result.get("songs", []) if isinstance(result, dict) else []
            matches = [s for s in songs if isinstance(s, dict) and str(s["title"]) in message] if isinstance(songs, list) else []
            if len(matches) > 1:
                exact = [s for s in matches if str(s["artist"]) in message]
                matches = exact or matches
            if len(matches) == 1:
                song_id = cast(int, matches[0]["id"])
        if song_id is None:
            return AgentAnswer("대상 곡이 명확하지 않습니다. ‘곡 ID 1의 긴장도를 60으로 수정해줘’처럼 ID와 요청을 함께 입력하세요.", True)
        if deleting:
            return self._result(execute("delete_song", {"song_id": song_id}))
        changes = mood_values(message)
        if not changes:
            return AgentAnswer("Demo Mode의 자연어 수정은 분위기 수치를 지원합니다. 제목·아티스트·재생 위치는 곡 편집 Form을 사용하세요.", True)
        return self._result(execute("update_song", {"song_id": song_id, "changes": changes}))

    @staticmethod
    def _result(trace: JsonObject) -> AgentAnswer:
        result = trace.get("result", {})
        message = str(trace["result_summary"])
        if trace["tool_name"] == "list_songs" and isinstance(result, dict):
            songs = result.get("songs", [])
            if isinstance(songs, list):
                message += "\n" + "\n".join(f"#{s['id']} {s['artist']} — {s['title']}" for s in songs if isinstance(s, dict))
        if trace["tool_name"] == "explain_playlist" and isinstance(result, dict):
            items = result.get("items", [])
            if isinstance(items, list):
                message += "\n" + "\n".join(f"{i['position']}. {i['role']}: {i['transition_reason']}" for i in items if isinstance(i, dict))
        return AgentAnswer(message, not bool(trace["success"]))
