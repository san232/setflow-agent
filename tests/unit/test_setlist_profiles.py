import json
from pathlib import Path

from app.application.schemas import SongCreate
from scripts.build_king_gnu import build_profiles, collect_occurrences, position_energy

ROOT = Path(__file__).resolve().parents[2]


def concert(name: str, main: list[str], encore: list[str] | None = None) -> dict:
    return {"id": name, "date": "2020-01-01", "name": name, "venue": "Test",
            "sources": [{"url": "https://example.com/source", "label": "fixture"}],
            "sections": [{"name": "main", "songs": main},
                         {"name": "encore", "songs": encore or []}]}


def corpus(concerts: list[dict]) -> dict:
    return {"artist": "King Gnu", "accessed_on": "2026-09-15", "aliases": {},
            "excluded_titles": {}, "concerts": concerts}


def research(raw: dict) -> dict:
    return {"sources": {"test": {"label": "fixture", "url": "https://example.com"}},
            "songs": [{"title": title, "source_ids": ["test"],
                       "base_ratings": dict(energy=50, valence=50, tension=50, density=50, closure=50)}
                      for title in collect_occurrences(raw)]}


def test_closure_uses_finale_evidence_not_low_energy() -> None:
    raw = corpus([concert(str(i), ["Opener", "Middle", "Main finale"], ["Encore", "Finale"])
                  for i in range(4)])
    profiles = {p["title"]: p for p in build_profiles(raw, research(raw))["profiles"]}
    assert profiles["Finale"]["ratings"]["closure"] > profiles["Main finale"]["ratings"]["closure"]
    assert profiles["Main finale"]["ratings"]["closure"] > profiles["Middle"]["ratings"]["closure"]
    assert profiles["Opener"]["stats"]["opening_count"] == 4
    assert profiles["Finale"]["stats"]["show_closing_count"] == 4


def test_se_guest_aliases_and_short_sections_do_not_corrupt_positions() -> None:
    raw = corpus([concert("a", ["SE", "CHAMELEON", "Guest"], ["Last"]),
                  concert("b", ["カメレオン", "Last"])])
    raw["aliases"] = {"CHAMELEON": "カメレオン"}
    raw["excluded_titles"] = {"SE": "stage cue", "Guest": "other artist"}
    profiles = {p["title"]: p for p in build_profiles(raw, research(raw))["profiles"]}
    assert set(profiles) == {"カメレオン", "Last"}
    assert profiles["カメレオン"]["stats"]["concert_count"] == 2
    occurrence = profiles["カメレオン"]["occurrences"][0]
    assert occurrence["source_title"] == "CHAMELEON"
    assert occurrence["source_position"] == 2
    assert occurrence["position"] == 1
    assert position_energy(0, "main") > position_energy(0.45, "main")
    assert profiles["Last"]["ratings"]["valence"] == 50


def test_published_dataset_is_reproducible_and_king_gnu_only() -> None:
    raw = json.loads((ROOT / "data/king_gnu_setlists.json").read_text(encoding="utf-8"))
    notes = json.loads((ROOT / "data/king_gnu_research.json").read_text(encoding="utf-8"))
    built = build_profiles(raw, notes)
    saved = json.loads((ROOT / "data/king_gnu_profiles.json").read_text(encoding="utf-8"))
    assert built == saved
    assert len(raw["concerts"]) == 7
    assert len({c["id"] for c in raw["concerts"]}) == 7
    seeds = json.loads((ROOT / "data/king_gnu_songs.json").read_text(encoding="utf-8"))["songs"]
    assert 30 <= len(seeds) <= 50
    assert len({s["title"] for s in seeds}) == len(seeds)
    assert {s["artist"] for s in seeds} == {"King Gnu"}
    for seed, profile in zip(seeds, built["profiles"], strict=True):
        SongCreate.model_validate(seed)
        assert seed["title"] == profile["title"]
        assert all(seed[k] == v for k, v in profile["ratings"].items())
        assert profile["source_ids"] and profile["evidence_note"]
        assert profile["occurrences"]
    assert not {s["title"] for s in seeds} & set(raw["excluded_titles"])


def test_musical_research_prevents_false_position_only_mood() -> None:
    profiles = json.loads((ROOT / "data/king_gnu_profiles.json").read_text(encoding="utf-8"))["profiles"]
    by_title = {p["title"]: p for p in profiles}
    assert by_title["一途"]["ratings"]["energy"] > by_title["逆夢"]["ratings"]["energy"]
    assert by_title["The hole"]["ratings"]["tension"] > by_title["BOY"]["ratings"]["tension"]
    assert by_title["BOY"]["ratings"]["valence"] > by_title["SPECIALZ"]["ratings"]["valence"]
    assert by_title["NIGHT POOL"]["ratings"]["density"] > by_title["Don't Stop the Clocks"]["ratings"]["density"]
    for profile in profiles:
        assert abs(profile["ratings"]["energy"] - profile["base_ratings"]["energy"]) <= 15
