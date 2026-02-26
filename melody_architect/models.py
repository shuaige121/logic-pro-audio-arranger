from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class NoteEvent:
    pitch: int
    start: float
    end: float
    velocity: int = 64
    track: str | None = None

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)


@dataclass
class MelodyData:
    notes: list[NoteEvent]
    tempo_bpm: float = 120.0
    beats_per_bar: int = 4
    beat_unit: int = 4
    source: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def sorted_notes(self) -> list[NoteEvent]:
        return sorted(self.notes, key=lambda n: (n.start, n.pitch, n.end))


@dataclass(frozen=True)
class KeyEstimate:
    tonic_pc: int
    tonic_name: str
    mode: str
    score: float
    margin: float


@dataclass(frozen=True)
class Chord:
    root_pc: int
    root_name: str
    quality: str
    symbol: str
    roman: str
    tones: tuple[int, ...]


@dataclass(frozen=True)
class HarmonyCandidate:
    name: str
    mode: str
    bars: tuple[Chord, ...]
    score: float
    chord_tone_coverage: float
    strong_beat_coverage: float
