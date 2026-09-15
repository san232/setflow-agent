"""Fact-based Korean explanations of the computed placement."""

from collections.abc import Sequence

from app.domain.models import Song
from app.domain.scoring import PENALTY_LABELS
from app.domain.weights import DEFAULT_CONFIG, ScoringConfig


def classify_role(energy: int, previous_energy: int | None, *, is_last: bool = False,
                  is_peak: bool = False, config: ScoringConfig = DEFAULT_CONFIG) -> str:
    """A role belongs to a placement, never permanently to a Song."""
    if is_last:
        return "마무리"
    if is_peak:
        return "절정"
    if previous_energy is None:
        return "유지"
    delta = energy - previous_energy
    return "상승" if delta > config.role_step else "완화" if delta < -config.role_step else "유지"


def explain_position(index: int, songs: Sequence[Song], targets: Sequence[float],
                     penalties: dict[str, float], config: ScoringConfig = DEFAULT_CONFIG) -> tuple[str, str]:
    """Explain measured transitions and the largest cost contributors."""
    current = songs[index]
    previous = songs[index - 1] if index else None
    peak = (len(songs) > 2 and targets[index] == max(targets) and
            current.energy >= max(s.energy for s in songs) - config.peak_tolerance)
    role = classify_role(current.energy, previous.energy if previous else None,
                         is_last=index == len(songs) - 1, is_peak=peak, config=config)
    text = f"목표 에너지 {targets[index]:.1f}, 실제 {current.energy}. "
    if previous:
        text += (f"앞 곡 ‘{previous.title}’에서 에너지 {current.energy - previous.energy:+d}, "
                 f"밝기 {current.valence - previous.valence:+d}, 긴장도 {current.tension - previous.tension:+d}, "
                 f"밀도 {current.density - previous.density:+d} 변화하여 {role} 역할입니다. ")
    else:
        text += "첫 곡으로 흐름의 기준을 만듭니다. "
    if index == len(songs) - 1:
        text += f"마지막 위치에서 closure {current.closure}을 반영했습니다. "
    major = sorted(((k, v) for k, v in penalties.items() if v > 0), key=lambda pair: (-pair[1], pair[0]))[:2]
    if major:
        text += "주요 비용: " + ", ".join(f"{PENALTY_LABELS[k]} {v:.1f}" for k, v in major) + "."
    return role, text

