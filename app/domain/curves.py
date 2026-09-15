"""Piecewise-linear mood targets on normalized positions 0..1."""

from dataclasses import dataclass
from math import isfinite
from collections.abc import Sequence

from app.domain.models import PRESETS, Song

PRESET_LABELS: dict[str, str] = {
    "gentle_rise": "완만한 상승", "mid_peak": "중반 절정형",
    "late_explosion": "후반 폭발형", "calm_afterglow": "잔잔한 여운", "auto": "자동 흐름",
}
ANCHORS: dict[str, tuple[tuple[float, float], ...]] = {
    "gentle_rise": ((0, 20), (0.5, 50), (1, 80)),
    "mid_peak": ((0, 25), (0.5, 95), (1, 30)),
    "late_explosion": ((0, 20), (0.5, 45), (0.75, 65), (1, 98)),
    "calm_afterglow": ((0, 35), (0.35, 80), (0.6, 55), (1, 15)),
}


@dataclass(frozen=True)
class MoodCurve:
    """A fixed curve, or a distribution-adapted rise-and-settle curve."""

    preset: str
    anchors: tuple[tuple[float, float], ...]

    @classmethod
    def create(cls, preset: str, songs: Sequence[Song]) -> "MoodCurve":
        """Adapt auto's targets to quantiles of the supplied energies."""
        if preset not in PRESETS:
            raise ValueError("지원하지 않는 분위기 Preset입니다.")
        if preset != "auto":
            return cls(preset, ANCHORS[preset])
        if not songs:
            raise ValueError("auto 곡선을 만들 곡이 없습니다.")
        energies = sorted(s.energy for s in songs)

        def quantile(q: float) -> float:
            index = q * (len(energies) - 1)
            low = int(index)
            high = min(low + 1, len(energies) - 1)
            return energies[low] + (energies[high] - energies[low]) * (index - low)

        return cls(preset, ((0, quantile(0.1)), (0.6, quantile(0.9)), (1, quantile(0.35))))

    def at(self, position: float) -> float:
        """Interpolate; reject positions outside the normalized interval."""
        if not isfinite(position) or not 0 <= position <= 1:
            raise ValueError("곡선 위치는 0.0~1.0이어야 합니다.")
        for (x0, y0), (x1, y1) in zip(self.anchors, self.anchors[1:]):
            if position <= x1:
                return y0 + (y1 - y0) * (position - x0) / (x1 - x0)
        return self.anchors[-1][1]

    def targets(self, count: int) -> list[float]:
        """Use the midpoint for a one-song playlist."""
        return [self.at(i / (count - 1) if count > 1 else 0.5) for i in range(count)]

