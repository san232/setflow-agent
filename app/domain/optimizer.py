"""Deterministic greedy ordering followed by bounded best-improvement swaps."""

from collections.abc import Sequence

from app.domain.curves import MoodCurve, PRESET_LABELS
from app.domain.explanations import explain_position
from app.domain.models import PlaylistItem, PlaylistResult, Song
from app.domain.scoring import evaluate, placement_penalties
from app.domain.weights import DEFAULT_CONFIG, ScoringConfig


def optimize(songs: Sequence[Song], preset: str,
             config: ScoringConfig = DEFAULT_CONFIG) -> PlaylistResult:
    """Preserve every unique input song; lower cost is better, not a global optimum."""
    if not songs:
        raise ValueError("Playlist를 만들 곡을 하나 이상 선택하세요.")
    if len(songs) > config.max_playlist_songs:
        raise ValueError(f"이번 MVP는 한 Playlist에 최대 {config.max_playlist_songs}곡을 지원합니다.")
    if len({s.id for s in songs}) != len(songs):
        raise ValueError("같은 곡 ID를 중복 선택할 수 없습니다.")
    curve = MoodCurve.create(preset, songs)
    targets = curve.targets(len(songs))
    remaining = sorted(songs, key=lambda s: s.id)
    order: list[Song] = []
    for index, target in enumerate(targets):
        def candidate_key(candidate: Song) -> tuple[float, int]:
            penalties = placement_penalties(candidate, order[-1] if order else None,
                order[-2] if len(order) > 1 else None, target, targets[index - 1] if index else None,
                index == len(songs) - 1, config)
            return sum(penalties.values()), candidate.id

        chosen = min(remaining, key=candidate_key)
        order.append(chosen)
        remaining.remove(chosen)
    cost = evaluate(order, curve, config).cost
    for _ in range(config.max_swap_passes):
        best_cost, best_pair = cost, None
        for left in range(len(order) - 1):
            for right in range(left + 1, len(order)):
                candidate = order.copy()
                candidate[left], candidate[right] = candidate[right], candidate[left]
                new_cost = evaluate(candidate, curve, config).cost
                if new_cost < best_cost - config.improvement_epsilon:
                    best_cost, best_pair = new_cost, (left, right)
        if best_pair is None:
            break
        left, right = best_pair
        order[left], order[right] = order[right], order[left]
        cost = best_cost
    evaluation = evaluate(order, curve, config)
    items: list[PlaylistItem] = []
    for index, song in enumerate(order):
        penalties = {k: round(v, config.precision) for k, v in evaluation.penalties[index].items()}
        role, reason = explain_position(index, order, targets, penalties, config)
        items.append(PlaylistItem(index + 1, song, round(targets[index], config.precision),
                                  song.energy, role, reason, penalties))
    final_cost = round(sum(sum(i.penalties.values()) for i in items), config.precision)
    fit = round(max(0, 100 - final_cost / len(order)), 2)
    return PlaylistResult(preset, final_cost, fit, tuple(items),
        f"{PRESET_LABELS[preset]} · {len(items)}곡 · 적합도 {fit}/100. "
        "입력한 주관적 수치와 휴리스틱 비용에 따른 Prototype이며 음악적 품질의 객관적 평가는 아닙니다.")
