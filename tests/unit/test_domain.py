from dataclasses import replace

import pytest

from app.domain.models import Song
from app.domain.curves import MoodCurve
from app.domain.optimizer import optimize
from app.domain.scoring import evaluate


def song(song_id: int, energy: int = 50, closure: int = 50) -> Song:
    return Song(song_id, f"곡 {song_id}", "샘플", energy, 50, 50, 50, closure)


@pytest.mark.parametrize("field", ["energy", "valence", "tension", "density", "closure"])
@pytest.mark.parametrize("value", [-1, 101, True, 12.5])
def test_mood_must_be_integer_in_range(field: str, value: object) -> None:
    with pytest.raises(ValueError):
        replace(song(1), **{field: value})


def test_mid_peak_target() -> None:
    curve = MoodCurve.create("mid_peak", [song(1)])
    assert curve.at(0.5) > curve.at(0)
    assert curve.at(0.5) > curve.at(1)


def test_afterglow_target_falls() -> None:
    curve = MoodCurve.create("calm_afterglow", [song(1)])
    assert curve.at(0.5) > curve.at(0.75) > curve.at(1)


@pytest.mark.parametrize("preset", ["gentle_rise", "mid_peak", "late_explosion", "calm_afterglow", "auto"])
def test_deterministic_permutation(preset: str) -> None:
    songs = [song(i, e) for i, e in enumerate([15, 80, 45, 95, 25, 65, 50, 35], 1)]
    first = optimize(songs, preset)
    assert first == optimize(songs, preset)
    assert first == optimize(list(reversed(songs)), preset)
    ids = [item.song.id for item in first.items]
    assert sorted(ids) == list(range(1, 9))
    assert len(ids) == len(set(ids))


def test_closure_is_better_at_end() -> None:
    low, high = song(1, closure=5), song(2, closure=95)
    curve = MoodCurve.create("gentle_rise", [low, high])
    assert evaluate([low, high], curve).cost < evaluate([high, low], curve).cost
    assert optimize([high, low], "gentle_rise").items[-1].song.id == high.id


def test_large_jump_penalty() -> None:
    songs = [song(1, 5), song(2, 95)]
    result = evaluate(songs, MoodCurve.create("gentle_rise", songs))
    assert result.penalties[1]["large_jump"] > 0


def test_empty_and_duplicate_input_rejected() -> None:
    with pytest.raises(ValueError):
        optimize([], "auto")
    with pytest.raises(ValueError):
        optimize([song(1), song(1)], "auto")


def test_single_song_and_cost_consistency() -> None:
    result = optimize([song(1)], "mid_peak")
    assert result.items[0].position == 1
    assert 0 <= result.fit_score <= 100
    assert result.cost == pytest.approx(sum(sum(i.penalties.values()) for i in result.items), abs=0.02)

