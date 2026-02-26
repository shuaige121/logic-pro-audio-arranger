from __future__ import annotations

import math
from statistics import median

from .models import KeyEstimate, MelodyData, NoteEvent
from .theory import MAJOR_PROFILE, MINOR_PROFILE, cosine_similarity, pc_to_name, rotate


def pitch_class_histogram(notes: list[NoteEvent]) -> list[float]:
    histogram = [0.0] * 12
    for note in notes:
        weight = max(0.05, note.duration)
        histogram[note.pitch % 12] += weight
    return histogram


def estimate_key(notes: list[NoteEvent]) -> KeyEstimate:
    histogram = pitch_class_histogram(notes)
    candidates: list[tuple[float, int, str]] = []

    for tonic in range(12):
        major_score = cosine_similarity(histogram, rotate(MAJOR_PROFILE, tonic))
        minor_score = cosine_similarity(histogram, rotate(MINOR_PROFILE, tonic))
        candidates.append((major_score, tonic, "major"))
        candidates.append((minor_score, tonic, "minor"))

    candidates.sort(key=lambda item: item[0], reverse=True)
    best_score, tonic_pc, mode = candidates[0]
    second_score = candidates[1][0] if len(candidates) > 1 else 0.0
    margin = best_score - second_score
    return KeyEstimate(
        tonic_pc=tonic_pc,
        tonic_name=pc_to_name(tonic_pc),
        mode=mode,
        score=best_score,
        margin=margin,
    )


def infer_bar_count(data: MelodyData) -> int:
    if not data.notes:
        return 1
    beat_seconds = 60.0 / max(1e-6, data.tempo_bpm)
    bar_seconds = beat_seconds * data.beats_per_bar
    max_end = max(note.end for note in data.notes)
    return max(1, int(math.ceil(max_end / bar_seconds)))


def detect_phrases(notes: list[NoteEvent], beat_seconds: float) -> list[dict[str, float | int]]:
    if not notes:
        return []

    ordered = sorted(notes, key=lambda note: note.start)
    split_threshold = 1.5 * beat_seconds

    phrases: list[dict[str, float | int]] = []
    phrase_start = ordered[0].start
    phrase_end = ordered[0].end
    phrase_count = 1

    for idx in range(1, len(ordered)):
        gap = ordered[idx].start - ordered[idx - 1].end
        if gap >= split_threshold:
            phrases.append(
                {
                    "start_sec": round(phrase_start, 4),
                    "end_sec": round(phrase_end, 4),
                    "note_count": phrase_count,
                }
            )
            phrase_start = ordered[idx].start
            phrase_end = ordered[idx].end
            phrase_count = 1
        else:
            phrase_end = max(phrase_end, ordered[idx].end)
            phrase_count += 1

    phrases.append(
        {
            "start_sec": round(phrase_start, 4),
            "end_sec": round(phrase_end, 4),
            "note_count": phrase_count,
        }
    )
    return phrases


def melody_summary(data: MelodyData) -> dict[str, float | int | list[dict[str, float | int]]]:
    notes = data.sorted_notes()
    if not notes:
        return {
            "note_count": 0,
            "range_min": 0,
            "range_max": 0,
            "range_span": 0,
            "median_pitch": 0,
            "avg_duration_sec": 0.0,
            "phrases": [],
        }

    beat_seconds = 60.0 / max(1e-6, data.tempo_bpm)
    total_duration = sum(note.duration for note in notes)
    return {
        "note_count": len(notes),
        "range_min": min(note.pitch for note in notes),
        "range_max": max(note.pitch for note in notes),
        "range_span": max(note.pitch for note in notes) - min(note.pitch for note in notes),
        "median_pitch": int(median(note.pitch for note in notes)),
        "avg_duration_sec": round(total_duration / len(notes), 4),
        "phrases": detect_phrases(notes, beat_seconds),
    }
