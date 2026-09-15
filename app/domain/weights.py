"""Central tuning point for scoring, roles, and bounded local search."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ScoringConfig:
    """Heuristic parameters; these have not been learned from listening data."""

    target: float = 0.9
    energy_step: float = 0.10
    direction: float = 0.25
    valence: float = 0.10
    tension: float = 0.08
    density: float = 0.09
    closure: float = 0.24
    repetition: float = 6.0
    jump: float = 0.65
    jump_threshold: int = 30
    similarity_threshold: int = 8
    role_step: int = 8
    peak_tolerance: int = 8
    max_swap_passes: int = 6
    max_playlist_songs: int = 50
    precision: int = 4
    improvement_epsilon: float = 1e-8


DEFAULT_CONFIG = ScoringConfig()

