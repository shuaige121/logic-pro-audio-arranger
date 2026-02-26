from __future__ import annotations

from .models import Chord, NoteEvent


def _root_line_leaps(chords: tuple[Chord, ...], base_octave: int = 2) -> list[int]:
    if len(chords) < 2:
        return []
    values = [base_octave * 12 + chord.root_pc for chord in chords]
    leaps: list[int] = []
    for idx in range(1, len(values)):
        raw = abs(values[idx] - values[idx - 1]) % 12
        leaps.append(min(raw, 12 - raw))
    return leaps


def _melody_range(notes: list[NoteEvent]) -> int:
    if not notes:
        return 0
    return max(note.pitch for note in notes) - min(note.pitch for note in notes)


def validate_arrangement(
    notes: list[NoteEvent],
    chords: tuple[Chord, ...],
    chord_tone_coverage: float,
    strong_beat_coverage: float,
) -> dict[str, object]:
    leaps = _root_line_leaps(chords)
    max_leap = max(leaps) if leaps else 0
    note_range = _melody_range(notes)

    warnings: list[str] = []
    if chord_tone_coverage < 0.7:
        warnings.append("Overall chord-tone coverage is below 0.70; consider slower harmonic rhythm.")
    if strong_beat_coverage < 0.55:
        warnings.append("Strong-beat coverage is below 0.55; adjust bar-level chord choices.")
    if max_leap > 7:
        warnings.append("Bass root motion has large leaps (> perfect fifth); smooth with inversions or passing bass notes.")
    if note_range > 24:
        warnings.append("Melody range exceeds two octaves; verify accompaniment register to avoid masking.")

    passed = len(warnings) == 0
    return {
        "passed": passed,
        "metrics": {
            "chord_tone_coverage": round(chord_tone_coverage, 4),
            "strong_beat_coverage": round(strong_beat_coverage, 4),
            "max_bass_root_leap_semitones": max_leap,
            "melody_range_semitones": note_range,
        },
        "warnings": warnings,
    }
