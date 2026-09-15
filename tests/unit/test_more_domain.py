from dataclasses import replace

import pytest

from app.domain.curves import MoodCurve
from app.domain.explanations import classify_role
from app.domain.models import Song
from app.domain.optimizer import optimize
from app.domain.scoring import evaluate


def test_same_song_gets_contextual_roles() -> None:
    assert classify_role(80, 50) == "상승"
    assert classify_role(80, 82) == "유지"
    assert classify_role(80, 95) == "완화"


def test_repetition_penalty_requires_three_similar_songs() -> None:
    songs = [Song(i, str(i), "sample", 50, 50, 50, 50, 50) for i in range(1, 4)]
    score = evaluate(songs, MoodCurve.create("auto", songs))
    assert score.penalties[0]["repetition"] == 0
    assert score.penalties[1]["repetition"] == 0
    assert score.penalties[2]["repetition"] > 0


@pytest.mark.parametrize("field", ["valence", "tension", "density"])
def test_non_energy_transition_cost(field: str) -> None:
    first = Song(1, "a", "a", 50, 50, 50, 50, 50)
    second = replace(first, id=2, **{field: 100})
    assert evaluate([first, second], MoodCurve.create("auto", [first, second])).penalties[1][field] > 0


def test_auto_adapts_to_distribution() -> None:
    low = [Song(i, str(i), "s", e, 50, 50, 50, 50) for i, e in enumerate([10, 20, 30], 1)]
    high = [replace(s, energy=s.energy + 60) for s in low]
    for a, b in zip(MoodCurve.create("auto", low).targets(5), MoodCurve.create("auto", high).targets(5)):
        assert b - a == pytest.approx(60)


def test_all_equal_stays_deterministic_and_finite() -> None:
    songs = [Song(i, str(i), "s", 50, 50, 50, 50, 50) for i in range(1, 9)]
    assert optimize(songs, "auto") == optimize(songs[::-1], "auto")
    assert 0 <= optimize(songs, "auto").fit_score <= 100

