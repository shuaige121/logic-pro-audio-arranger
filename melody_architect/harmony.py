from __future__ import annotations

from dataclasses import dataclass

from .models import Chord, HarmonyCandidate, NoteEvent
from .theory import resolve_roman_to_chord


@dataclass(frozen=True)
class ProgressionTemplate:
    name: str
    tokens: tuple[str, ...]
    mode: str


STYLE_TEMPLATES: dict[str, list[ProgressionTemplate]] = {
    "pop": [
        ProgressionTemplate("pop_primary", ("I", "V", "vi", "IV"), "major"),
        ProgressionTemplate("pop_alt", ("I", "vi", "IV", "V"), "major"),
        ProgressionTemplate("pop_desc", ("vi", "IV", "I", "V"), "major"),
        ProgressionTemplate("pop_minor", ("i", "bVII", "bVI", "bVII"), "minor"),
    ],
    "modal": [
        ProgressionTemplate("modal_dorian", ("i7", "IV7"), "dorian"),
        ProgressionTemplate("modal_mixolydian", ("I7", "bVII7"), "mixolydian"),
    ],
    "jazz": [
        ProgressionTemplate("jazz_ii_v_i", ("ii7", "V7", "Imaj7"), "major"),
        ProgressionTemplate("jazz_cycle", ("ii7", "V7", "Imaj7", "VI7"), "major"),
    ],
}


def _cycle_tokens(tokens: tuple[str, ...], bars: int) -> tuple[str, ...]:
    if bars <= 0:
        return tuple()
    return tuple(tokens[idx % len(tokens)] for idx in range(bars))


def _notes_by_bar(notes: list[NoteEvent], bar_seconds: float, bar_count: int) -> list[list[NoteEvent]]:
    grouped: list[list[NoteEvent]] = [[] for _ in range(max(1, bar_count))]
    for note in notes:
        idx = int(note.start / bar_seconds)
        if idx < 0:
            idx = 0
        if idx >= len(grouped):
            idx = len(grouped) - 1
        grouped[idx].append(note)
    return grouped


def _is_strong_beat(note: NoteEvent, bar_idx: int, bar_seconds: float, beat_seconds: float, beats_per_bar: int) -> bool:
    bar_start = bar_idx * bar_seconds
    beat_position = (note.start - bar_start) / beat_seconds
    nearest = round(beat_position)
    on_grid = abs(beat_position - nearest) <= 0.2
    strong_beats = {0}
    if beats_per_bar >= 4:
        strong_beats.add(beats_per_bar // 2)
    return on_grid and (nearest % beats_per_bar) in strong_beats


def _score_progression(
    chords: tuple[Chord, ...],
    notes_grouped: list[list[NoteEvent]],
    beats_per_bar: int,
    tempo_bpm: float,
) -> tuple[float, float, float]:
    beat_seconds = 60.0 / max(1e-6, tempo_bpm)
    bar_seconds = beat_seconds * beats_per_bar

    total_notes = 0
    chord_tone_hits = 0
    strong_total = 0
    strong_hits = 0
    score = 0.0

    for bar_idx, bar_notes in enumerate(notes_grouped):
        chord = chords[min(bar_idx, len(chords) - 1)]
        tones = set(chord.tones)

        for note in bar_notes:
            total_notes += 1
            strong = _is_strong_beat(note, bar_idx, bar_seconds, beat_seconds, beats_per_bar)
            in_chord = (note.pitch % 12) in tones

            if strong:
                strong_total += 1
            if in_chord:
                chord_tone_hits += 1
                if strong:
                    strong_hits += 1
                    score += 2.0
                else:
                    score += 1.0
            else:
                if strong:
                    score -= 2.0
                else:
                    score -= 0.75

    coverage = (chord_tone_hits / total_notes) if total_notes else 0.0
    strong_coverage = (strong_hits / strong_total) if strong_total else 0.0
    score += coverage * 8.0 + strong_coverage * 6.0
    return score, coverage, strong_coverage


def generate_harmony_candidates(
    notes: list[NoteEvent],
    tonic_pc: int,
    detected_mode: str,
    style: str,
    bar_count: int,
    beats_per_bar: int,
    tempo_bpm: float,
    mode_override: str | None = None,
    include_borrowed_iv: bool = True,
    include_tritone_sub: bool = True,
) -> list[HarmonyCandidate]:
    if style not in STYLE_TEMPLATES:
        raise ValueError(f"Unsupported style: {style}")

    templates = list(STYLE_TEMPLATES[style])
    if style == "pop" and include_borrowed_iv:
        templates.append(ProgressionTemplate("pop_borrowed_iv", ("I", "V", "vi", "iv"), "major"))
    if style == "jazz" and include_tritone_sub:
        templates.append(ProgressionTemplate("jazz_tritone", ("ii7", "bII7", "Imaj7"), "major"))

    beat_seconds = 60.0 / max(1e-6, tempo_bpm)
    bar_seconds = beat_seconds * beats_per_bar
    grouped = _notes_by_bar(notes, bar_seconds, bar_count)

    candidates: list[HarmonyCandidate] = []
    for template in templates:
        mode = mode_override or template.mode or detected_mode
        romans = _cycle_tokens(template.tokens, bar_count)
        bars = tuple(resolve_roman_to_chord(token, tonic_pc, mode) for token in romans)
        score, coverage, strong_coverage = _score_progression(bars, grouped, beats_per_bar, tempo_bpm)
        candidates.append(
            HarmonyCandidate(
                name=template.name,
                mode=mode,
                bars=bars,
                score=round(score, 4),
                chord_tone_coverage=round(coverage, 4),
                strong_beat_coverage=round(strong_coverage, 4),
            )
        )

    return sorted(candidates, key=lambda item: item.score, reverse=True)
