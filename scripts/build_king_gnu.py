"""Rebuild sourced King Gnu seed values; no network, audio analysis or training."""

import json
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import TypedDict, cast


class Source(TypedDict):
    label: str
    url: str


class Section(TypedDict):
    name: str
    songs: list[str]


class Concert(TypedDict):
    id: str
    date: str
    name: str
    venue: str
    sources: list[Source]
    sections: list[Section]


class Corpus(TypedDict):
    artist: str
    accessed_on: str
    aliases: dict[str, str]
    excluded_titles: dict[str, str]
    concerts: list[Concert]


class ResearchSong(TypedDict):
    title: str
    genre_tags: list[str]
    genre_status: str
    instruments: list[str]
    instrument_scope: str
    evidence_note: str
    source_ids: list[str]
    base_ratings: dict[str, int]
    rating_status: str


class Research(TypedDict):
    sources: dict[str, Source]
    songs: list[ResearchSong]


class Occurrence(TypedDict):
    concert_id: str
    source_title: str
    source_position: int
    section: str
    position: int
    song_count: int
    normalized_position: float
    section_position: int
    section_song_count: int
    assumed_energy: float
    closure_evidence: int
    is_opener: bool
    is_main_closer: bool
    is_show_closer: bool


ROOT = Path(__file__).resolve().parents[1]
FIELDS = ("energy", "valence", "tension", "density", "closure")
MAIN_CURVE = ((0.0, 88), (0.18, 78), (0.45, 32), (0.62, 52), (0.85, 90), (1.0, 82))
ENCORE_CURVE = ((0.0, 60), (0.5, 88), (1.0, 55))
MUSIC_ENERGY_WEIGHT = 0.85
MUSIC_CLOSURE_WEIGHT = 0.55
PRIOR_OBSERVATIONS = 2
NOTICE = ("King Gnu 대표 공연 7개(2019~2025)와 곡·장르·악기 자료를 참고한 주관적 초깃값입니다. "
          "실측 음원 분석·공식 점수·역대 전수조사가 아닙니다. 공연 편곡은 원곡과 다를 수 있으며 직접 수정할 수 있습니다.")


def position_energy(position: float, section: str) -> float:
    """A declared editorial template, never a measurement of a concert's energy."""
    curve = MAIN_CURVE if section == "main" else ENCORE_CURVE
    for (start, low), (end, high) in zip(curve, curve[1:]):
        if start <= position <= end:
            return low + (high - low) * (position - start) / (end - start)
    raise ValueError("Position must be between zero and one.")


def collect_occurrences(raw: Corpus) -> dict[str, list[Occurrence]]:
    """Keep raw order, normalize eligible tracks, and separate main/encore endings."""
    result: dict[str, list[Occurrence]] = defaultdict(list)
    seen_concerts: set[str] = set()
    for show in raw["concerts"]:
        if show["id"] in seen_concerts:
            raise ValueError("Duplicate concert: " + show["id"])
        seen_concerts.add(show["id"])
        eligible: list[tuple[str, str, str, int]] = []
        source_position = 0
        for section in show["sections"]:
            for title in section["songs"]:
                source_position += 1
                canonical = raw["aliases"].get(title, title)
                if title not in raw["excluded_titles"] and canonical not in raw["excluded_titles"]:
                    eligible.append((canonical, title, section["name"], source_position))
        if len({entry[0] for entry in eligible}) != len(eligible):
            raise ValueError("Repeated song within a concert needs manual version handling: " + show["id"])
        main = [entry for entry in eligible if entry[2] == "main"]
        for index, (title, source_title, section, source_index) in enumerate(eligible):
            in_section = [entry for entry in eligible if entry[2] == section]
            section_index = next(i for i, entry in enumerate(in_section) if entry[0] == title)
            section_position = section_index / max(1, len(in_section) - 1)
            is_main_closer = bool(main) and title == main[-1][0]
            is_show_closer = index == len(eligible) - 1
            closing = 100 if is_show_closer else 80 if is_main_closer else 60 if section != "main" else 20
            result[title].append({"concert_id": show["id"], "source_title": source_title,
                "source_position": source_index, "section": section, "position": index + 1,
                "song_count": len(eligible), "normalized_position": round(index / max(1, len(eligible) - 1), 4),
                "section_position": section_index + 1, "section_song_count": len(in_section),
                "assumed_energy": round(position_energy(section_position, section), 4),
                "closure_evidence": closing, "is_opener": index == 0,
                "is_main_closer": is_main_closer, "is_show_closer": is_show_closer})
    return dict(result)


def build_profiles(raw: Corpus, research: Research) -> dict[str, object]:
    """Combine explicit musical judgments with bounded setlist position evidence."""
    occurrences = collect_occurrences(raw)
    notes = {s["title"]: s for s in research["songs"]}
    if len(notes) != len(research["songs"]) or set(notes) != set(occurrences):
        raise ValueError("Every eligible song must have exactly one research record.")
    if raw["artist"] != "King Gnu":
        raise ValueError("This catalogue is limited to King Gnu.")
    profiles: list[dict[str, object]] = []
    for title, visits in occurrences.items():
        note = notes[title]
        base = note["base_ratings"]
        if set(base) != set(FIELDS) or any(type(v) is not int or not 0 <= v <= 100 for v in base.values()):
            raise ValueError("All five base ratings must be integers from 0 to 100.")
        if not note["source_ids"] or any(s not in research["sources"] for s in note["source_ids"]):
            raise ValueError("Missing music source for " + title)
        count = len(visits)
        # Two neutral pseudo-observations temper one-off finale/song placement evidence.
        position_score = (50 * PRIOR_OBSERVATIONS + sum(v["assumed_energy"] for v in visits)) / (count + PRIOR_OBSERVATIONS)
        closing_score = (50 * PRIOR_OBSERVATIONS + sum(v["closure_evidence"] for v in visits)) / (count + PRIOR_OBSERVATIONS)
        ratings = dict(base)
        ratings["energy"] = round(MUSIC_ENERGY_WEIGHT * base["energy"] + (1 - MUSIC_ENERGY_WEIGHT) * position_score)
        ratings["closure"] = round(MUSIC_CLOSURE_WEIGHT * base["closure"] + (1 - MUSIC_CLOSURE_WEIGHT) * closing_score)
        profiles.append({**note, "artist": "King Gnu", "ratings": ratings,
            "stats": {"concert_count": count,
                "mean_position": round(mean(v["normalized_position"] for v in visits), 4),
                "opening_count": sum(v["is_opener"] for v in visits),
                "main_closing_count": sum(v["is_main_closer"] for v in visits),
                "show_closing_count": sum(v["is_show_closer"] for v in visits),
                "encore_count": sum(v["section"] != "main" for v in visits),
                "position_energy": round(position_score, 4), "closing_evidence": round(closing_score, 4)},
            "occurrences": visits})
    return {"version": "king-gnu-research-v1", "notice": NOTICE, "accessed_on": raw["accessed_on"],
        "method": {"music_energy_weight": MUSIC_ENERGY_WEIGHT, "music_closure_weight": MUSIC_CLOSURE_WEIGHT,
            "neutral_prior_observations": PRIOR_OBSERVATIONS, "main_curve": [list(p) for p in MAIN_CURVE],
            "encore_curve": [list(p) for p in ENCORE_CURVE], "rounding": "Python round (ties to even)"},
        "excluded_titles": raw["excluded_titles"], "sources": research["sources"],
        "concerts": raw["concerts"], "profiles": profiles}


def render_document(output: dict[str, object]) -> str:
    """Keep the human-readable submission reference in sync with the seed."""
    profiles = cast(list[dict[str, object]], output["profiles"])
    concerts = cast(list[Concert], output["concerts"])
    sources = cast(dict[str, Source], output["sources"])
    lines = ["# King Gnu 초깃값과 조사 근거", "", str(output["notice"]), "",
        "자료 확인일: " + str(output["accessed_on"]) + ". 이 문서는 `python -m scripts.build_king_gnu`로 재생성합니다.", "",
        "## 수집 범위", "",
        "연도와 투어가 다른 대표 공연 7개를 수작업으로 대조했습니다. 역대 모든 공연, 전곡 목록, 2026년 최신 투어를 포괄하지 않습니다. 같은 투어의 여러 날짜를 많이 넣어 특정 편곡이 과대표집되는 것을 피했습니다. 이 표본은 임의로 고른 것으로 통계적 대표성을 보장하지 않습니다.", "",
        "| 날짜 | 공연 | 장소 | 세트리스트 출처 |", "|---|---|---|---|"]
    for show in concerts:
        links = " · ".join(f'[{s["label"]}]({s["url"]})' for s in show["sources"])
        lines.append(f'| {show["date"]} | {show["name"]} | {show["venue"]} | {links} |')
    lines += ["", "원자료에는 연결 트랙과 게스트 곡도 원래 순서로 남겼습니다. 아래 항목을 정렬 대상과 통계에서 제외한 뒤 43곡을 선정했습니다. `NIGHT POOL`은 공연의 확장 편곡을 다룬 악기 자료가 있어 포함했고, `MASCARA`는 Sony가 발매를 확인한 King Gnu 셀프 커버 버전으로 포함했습니다.", ""]
    for title, reason in cast(dict[str, str], output["excluded_titles"]).items():
        lines.append(f"- {title}: {reason}")
    lines += ["", "`ロウラブ → ロウラヴ`, `Stardom → STARDOM`, `CHAMELEON → カメレオン`으로 묶었습니다. 원문 제목은 각 출현 기록의 `source_title`에 보존합니다. 카멜레온의 버전별 편곡 차이는 이 초기 모델에서 별도 곡으로 나누지 않습니다.", "",
        "## 사실과 주관적 수치의 구분", "",
        "공연 날짜·순서와 출처가 서술한 악기·음색은 자료에 근거합니다. 장르 태그는 리뷰의 설명을 정리한 편집 태그이며 공식 장르 분류가 아닙니다. `instruments`는 언급된 일부 악기·보컬·처리 음색만 기록합니다. 현악 음색이나 목금 음색의 언급을 실제 연주자의 악기 크레딧으로 바꾸지 않았습니다. 공연용 어쿠스틱 편곡은 해당 공연의 특징입니다.", "",
        "다섯 기본값은 조사 내용을 읽고 수작업으로 정한 가설입니다. 악기가 몇 개라는 이유만으로 밀도를 계산하지 않으며, 음원 분석·BPM 측정·감정 인식 모델·공식 수치·객관적 정답은 사용하지 않았습니다. 직접 들어본 본인의 판단으로 수정하는 용도입니다.", "",
        "| 필드 | 낮은 값 → 높은 값 |", "|---|---|",
        "| energy | 억제된 추진력 → 강한 추진력·공격성 |",
        "| valence | 어둡거나 우울한 인상 → 밝거나 낙관적인 인상 |",
        "| tension | 안정·완화 → 불안·긴장·급격한 전개 |",
        "| density | 여백이 많은 편성 → 겹치는 음색·리듬이 많은 편성 |",
        "| closure | 연결 구간에 어울림 → 종결·합창·여운에 어울림 |", "",
        "## 공연 배치 반영식", "",
        "본편과 앙코르를 각각 분리하고, 선정 곡의 구간 내 순서를 0~1로 정규화합니다. 시작부터 끝까지 에너지가 단조 증가한다고 가정하지 않습니다. 아래 곡선은 실제 콘서트의 측정치가 아니라 이 프로젝트가 정한 임의의 보조 템플릿입니다.", "",
        "- 본편: `(0,88), (0.18,78), (0.45,32), (0.62,52), (0.85,90), (1,82)` 사이를 선형 보간.",
        "- 앙코르·더블 앙코르 각각: `(0,60), (0.5,88), (1,55)` 사이를 선형 보간. 1곡 구간은 위치 0으로 취급.",
        "- 종료 근거 점수: 공연 전체 마지막 100, 그 외 본편 마지막 80, 그 외 앙코르 60, 나머지 본편 20. 제외 트랙을 제거한 뒤 판단.",
        "- 해당 곡 출현 횟수가 n일 때, 배치 점수 = `(50×2 + 각 출현의 템플릿 에너지 합) / (n+2)`.",
        "- 종료 점수 = `(50×2 + 각 출현의 종료 근거 점수 합) / (n+2)`.",
        "- 최종 energy = `round(0.85×음악 기본값 + 0.15×배치 점수)`.",
        "- 최종 closure = `round(0.55×음악 기본값 + 0.45×종료 점수)`.",
        "- valence / tension / density는 음악 자료에 따른 기본값 그대로 사용.", "",
        "두 번의 중립 관측(50)을 추가해 한 공연의 배치만으로 값을 과도하게 바꾸지 않게 했습니다. 가중치와 곡선은 학습한 결과가 아닌 편집 규칙이며 모든 곡에 동일하게 적용합니다. 반올림은 Python round의 ties-to-even입니다. 음악 기본값과 최종값은 0~100 정수입니다.", "",
        "`source_position`은 저장한 원자료에서 연결 트랙을 포함한 연속 순번입니다. 기사에 인쇄된 곡 번호와 다를 수 있습니다. `position`, `section_position`은 제외 트랙을 제거한 전체·구간 내 순번입니다. `mean_position`은 선정 곡 기준 전체 상대 위치의 평균(0~1)입니다. 공연 출현 횟수는 이 표본 7개 안에서의 횟수이며 역대 연주 횟수가 아닙니다.", "",
        "## 43곡 최종 초깃값", "",
        "장르·악기를 참고한 음악 기본값에 위 배치 보정을 반영한 값입니다. 이 값이 보관함에 들어갑니다.", "",
        "| 곡 | 에너지 | 밝기 | 긴장 | 밀도 | 마무리 | 표본 출현 |", "|---|---:|---:|---:|---:|---:|---:|"]
    for p in profiles:
        ratings = cast(dict[str, int], p["ratings"])
        stats = cast(dict[str, object], p["stats"])
        values = " | ".join(str(ratings[f]) for f in FIELDS)
        lines.append(f'| {p["title"]} | {values} | {stats["concert_count"]} |')
    lines += ["", "## 곡별 음악 자료와 기본값", "",
        "아래 다섯 숫자는 배치 보정 전의 음악 기본값이며 순서는 에너지 / 밝기 / 긴장 / 밀도 / 마무리입니다. 출처의 숫자를 옮긴 것이 아닙니다.", ""]
    for p in profiles:
        base = cast(dict[str, int], p["base_ratings"])
        instruments = cast(list[str], p["instruments"])
        genre = " · ".join(cast(list[str], p["genre_tags"]))
        links = " · ".join(f'[{sources[s]["label"]}]({sources[s]["url"]})' for s in cast(list[str], p["source_ids"]))
        lines += [f'### {p["title"]}', "", f'장르·스타일: {genre}. 확인된 악기·음색: {" · ".join(instruments) or "곡 단위 확인 자료 없음"}.', "",
            str(p["evidence_note"]), "", "주관적 음악 기본값: **" + " / ".join(str(base[f]) for f in FIELDS) + "**. " + links, ""]
    lines += ["## 파일과 갱신", "",
        "- `data/king_gnu_setlists.json`: 공연 7개의 순서, 원문 표기와 제외 규칙.",
        "- `data/king_gnu_research.json`: 곡별 음악 설명, 출처, 수작업 기본값. 수정은 이 원자료에서 시작.",
        "- `data/king_gnu_profiles.json`: 최종값, 기본값, 출현별 위치, 공연 통계와 출처를 보존한 생성물.",
        "- `data/king_gnu_songs.json`: 기존 SongCreate 형식의 43곡 Seed.",
        "- `python -m scripts.build_king_gnu`: 인터넷 없이 JSON 두 개와 이 문서를 재생성. 실행 DB를 바꾸지 않음.",
        "- `python -m scripts.seed`: 없는 제목·아티스트 조합만 추가. 기존 사용자 편집을 덮어쓰지 않음.", "",
        "UI에서 바꾼 값은 SQLite에만 저장되며 이 조사 자료를 바꾸지 않습니다. 이미 만든 Playlist도 생성 당시의 값을 유지합니다. 근거 자료는 별도 읽기 전용 `/api/catalog/king-gnu`에서 확인합니다. 가사·음원·이미지와 YouTube 재생 ID는 포함하지 않습니다.", ""]
    return "\n".join(lines)


def main() -> None:
    """Write source-controlled seed values and reproducible, inspectable provenance."""
    raw = cast(Corpus, json.loads((ROOT / "data/king_gnu_setlists.json").read_text(encoding="utf-8")))
    research = cast(Research, json.loads((ROOT / "data/king_gnu_research.json").read_text(encoding="utf-8")))
    output = build_profiles(raw, research)
    profiles = cast(list[dict[str, object]], output["profiles"])
    songs = [{"title": p["title"], "artist": p["artist"], **cast(dict[str, int], p["ratings"])} for p in profiles]
    for name, content in (("king_gnu_profiles.json", output), ("king_gnu_songs.json", {"notice": NOTICE, "songs": songs})):
        (ROOT / "data" / name).write_text(json.dumps(content, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "docs/KING_GNU_DATA.md").write_text(render_document(output), encoding="utf-8")
    print(f"Built {len(songs)} King Gnu songs from {len(raw['concerts'])} representative concerts.")


if __name__ == "__main__":
    main()
