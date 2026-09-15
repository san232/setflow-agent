"""Immutable domain values; no web, ORM, or SDK dependencies."""

from dataclasses import dataclass

MOOD_FIELDS: tuple[str, ...] = ("energy", "valence", "tension", "density", "closure")
PRESETS: tuple[str, ...] = ("gentle_rise", "mid_peak", "late_explosion", "calm_afterglow", "auto")


@dataclass(frozen=True)
class Song:
    """A user's subjective mood ratings, not audio-analysis measurements."""

    id: int
    title: str
    artist: str
    energy: int
    valence: int
    tension: int
    density: int
    closure: int
    media_uri: str | None = None

    def __post_init__(self) -> None:
        for field in MOOD_FIELDS:
            value = getattr(self, field)
            if type(value) is not int or not 0 <= value <= 100:
                raise ValueError(f"{field}는 0~100 사이 정수여야 합니다.")
        if not self.title.strip() or not self.artist.strip():
            raise ValueError("제목과 아티스트는 비워 둘 수 없습니다.")


@dataclass(frozen=True)
class PlaylistItem:
    """A placement and its evidence, calculated from the final order."""

    position: int
    song: Song
    target_energy: float
    actual_energy: int
    role: str
    transition_reason: str
    penalties: dict[str, float]


@dataclass(frozen=True)
class PlaylistResult:
    """Deterministic result saved as an immutable generation snapshot."""

    preset: str
    cost: float
    fit_score: float
    items: tuple[PlaylistItem, ...]
    summary: str

