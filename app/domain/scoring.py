"""One cost function shared by optimization and user-visible explanations."""

from collections.abc import Sequence
from dataclasses import dataclass

from app.domain.curves import MoodCurve
from app.domain.models import Song
from app.domain.weights import DEFAULT_CONFIG, ScoringConfig

PENALTY_LABELS: dict[str, str] = {
    "target": "목표 에너지 차이", "energy_step": "에너지 변화",
    "direction": "목표 흐름과 변화 방향 차이", "valence": "밝기 변화",
    "tension": "긴장도 변화", "density": "밀도 변화",
    "closure": "마무리 적합도 부족", "repetition": "유사 분위기 3곡 연속",
    "large_jump": "큰 에너지 도약",
}


def placement_penalties(song: Song, previous: Song | None, before_previous: Song | None,
                        target: float, previous_target: float | None, last: bool,
                        config: ScoringConfig = DEFAULT_CONFIG) -> dict[str, float]:
    """Return nonnegative contributions; closure applies at the last position only."""
    costs = {key: 0.0 for key in PENALTY_LABELS}
    costs["target"] = abs(song.energy - target) * config.target
    if last:
        costs["closure"] = (100 - song.closure) * config.closure
    if previous is not None:
        delta = song.energy - previous.energy
        costs["energy_step"] = abs(delta) * config.energy_step
        expected_delta = target - previous_target if previous_target is not None else 0
        costs["direction"] = abs(delta - expected_delta) * config.direction
        for field in ("valence", "tension", "density"):
            costs[field] = abs(getattr(song, field) - getattr(previous, field)) * getattr(config, field)
        costs["large_jump"] = max(0, abs(delta) - config.jump_threshold) * config.jump
        if before_previous is not None:
            same = all(max(getattr(s, f) for s in (before_previous, previous, song)) -
                       min(getattr(s, f) for s in (before_previous, previous, song)) <= config.similarity_threshold
                       for f in ("energy", "valence", "tension", "density"))
            if same:
                costs["repetition"] = config.repetition
    return costs


@dataclass(frozen=True)
class Evaluation:
    """Total optimization cost and each position's contributions."""

    cost: float
    penalties: tuple[dict[str, float], ...]


def evaluate(songs: Sequence[Song], curve: MoodCurve,
             config: ScoringConfig = DEFAULT_CONFIG) -> Evaluation:
    """Evaluate the complete order without hidden state or random choices."""
    targets = curve.targets(len(songs))
    penalties = tuple(placement_penalties(s, songs[i - 1] if i else None,
                     songs[i - 2] if i > 1 else None, targets[i], targets[i - 1] if i else None,
                     i == len(songs) - 1, config) for i, s in enumerate(songs))
    return Evaluation(sum(sum(p.values()) for p in penalties), penalties)

