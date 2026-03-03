from __future__ import annotations

import math
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from .models import Chord

PC_NAMES_SHARP = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
PC_NAMES_FLAT = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]

MAJOR_PROFILE = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
MINOR_PROFILE = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]

MODE_INTERVALS = {
    "major": [0, 2, 4, 5, 7, 9, 11],
    "minor": [0, 2, 3, 5, 7, 8, 10],
    "dorian": [0, 2, 3, 5, 7, 9, 10],
    "mixolydian": [0, 2, 4, 5, 7, 9, 10],
    "phrygian": [0, 1, 3, 5, 7, 8, 10],
    "lydian": [0, 2, 4, 6, 7, 9, 11],
    "aeolian": [0, 2, 3, 5, 7, 8, 10],
    "locrian": [0, 1, 3, 5, 6, 8, 10],
    "harmonic_minor": [0, 2, 3, 5, 7, 8, 11],
    "melodic_minor": [0, 2, 3, 5, 7, 9, 11],
    "pentatonic_major": [0, 2, 4, 7, 9],
    "pentatonic_minor": [0, 3, 5, 7, 10],
    "blues": [0, 3, 5, 6, 7, 10],
    "whole_tone": [0, 2, 4, 6, 8, 10],
    "diminished_hw": [0, 1, 3, 4, 6, 7, 9, 10],
    "diminished_wh": [0, 2, 3, 5, 6, 8, 9, 11],
    "bebop_dominant": [0, 2, 4, 5, 7, 9, 10, 11],
    "phrygian_dominant": [0, 1, 4, 5, 7, 8, 10],
    "hungarian_minor": [0, 2, 3, 6, 7, 8, 11],
    "double_harmonic": [0, 1, 4, 5, 7, 8, 11],
}

ROMAN_TO_DEGREE = {
    "I": 1,
    "II": 2,
    "III": 3,
    "IV": 4,
    "V": 5,
    "VI": 6,
    "VII": 7,
}

CHORD_TONE_INTERVALS = {
    "major": [0, 4, 7],
    "minor": [0, 3, 7],
    "dim": [0, 3, 6],
    "dominant7": [0, 4, 7, 10],
    "maj7": [0, 4, 7, 11],
    "min7": [0, 3, 7, 10],
    "aug": [0, 4, 8],
    "sus2": [0, 2, 7],
    "sus4": [0, 5, 7],
    "dom7": [0, 4, 7, 10],
    "min_maj7": [0, 3, 7, 11],
    "dim7": [0, 3, 6, 9],
    "half_dim7": [0, 3, 6, 10],
    "aug7": [0, 4, 8, 10],
    "aug_maj7": [0, 4, 8, 11],
    "6": [0, 4, 7, 9],
    "min6": [0, 3, 7, 9],
    "9": [0, 4, 7, 10, 14],
    "maj9": [0, 4, 7, 11, 14],
    "min9": [0, 3, 7, 10, 14],
    "add9": [0, 4, 7, 14],
    "11": [0, 4, 7, 10, 14, 17],
    "min11": [0, 3, 7, 10, 14, 17],
    "13": [0, 4, 7, 10, 14, 17, 21],
    "power5": [0, 7],
    "7sharp5": [0, 4, 8, 10],
    "7flat5": [0, 4, 6, 10],
    "7sharp9": [0, 4, 7, 10, 15],
    "7flat9": [0, 4, 7, 10, 13],
    "7sharp11": [0, 4, 7, 10, 18],
}

ROMAN_PATTERN = re.compile(r"^(?P<accidental>[b#]?)(?P<roman>[ivIV]+)(?P<suffix>.*)$")


def _normalize_lookup_key(name: str) -> str:
    token = name.strip().lower().replace("♭", "b").replace("♯", "#")
    token = re.sub(r"[^a-z0-9#]+", "_", token)
    return token.strip("_")


def _parse_intervals(interval_text: str) -> list[int]:
    return [int(part.strip()) for part in interval_text.split(",") if part.strip()]


def _knowledge_db_path() -> Path:
    return Path(__file__).resolve().parent.parent / "knowledge" / "knowledge.db"


def load_scales_from_db() -> dict[str, list[int]]:
    db_path = _knowledge_db_path()
    if not db_path.exists():
        return {}
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT name, intervals FROM scales_modes ORDER BY id"
        ).fetchall()
    return {_normalize_lookup_key(name): _parse_intervals(intervals) for name, intervals in rows}


def load_chords_from_db() -> dict[str, list[int]]:
    db_path = _knowledge_db_path()
    if not db_path.exists():
        return {}
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT name, intervals FROM chord_types ORDER BY id"
        ).fetchall()
    return {_normalize_lookup_key(name): _parse_intervals(intervals) for name, intervals in rows}


def get_scale(name: str) -> list[int]:
    key = _normalize_lookup_key(name)
    if key in MODE_INTERVALS:
        return MODE_INTERVALS[key]
    scales_from_db = load_scales_from_db()
    if key in scales_from_db:
        return scales_from_db[key]
    raise ValueError(f"Unsupported scale: {name}")


def get_chord_type(name: str) -> list[int]:
    key = _normalize_lookup_key(name)
    if key in CHORD_TONE_INTERVALS:
        return CHORD_TONE_INTERVALS[key]
    chords_from_db = load_chords_from_db()
    if key in chords_from_db:
        return chords_from_db[key]
    raise ValueError(f"Unsupported chord type: {name}")


def pc_to_name(pc: int, prefer_flats: bool = False) -> str:
    names = PC_NAMES_FLAT if prefer_flats else PC_NAMES_SHARP
    return names[pc % 12]


def note_name_to_pc(name: str) -> int:
    token = name.strip().replace("♭", "b").replace("♯", "#")
    if token in PC_NAMES_SHARP:
        return PC_NAMES_SHARP.index(token)
    if token in PC_NAMES_FLAT:
        return PC_NAMES_FLAT.index(token)
    raise ValueError(f"Unsupported note name: {name}")


def rotate(values: list[float], shift: int) -> list[float]:
    size = len(values)
    return [values[(idx - shift) % size] for idx in range(size)]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


@dataclass(frozen=True)
class RomanToken:
    accidental: int
    degree: int
    roman: str
    suffix: str
    lowered_case: bool


def parse_roman(token: str) -> RomanToken:
    text = token.strip()
    match = ROMAN_PATTERN.match(text)
    if not match:
        raise ValueError(f"Invalid roman numeral token: {token}")

    accidental_prefix = match.group("accidental")
    accidental = -1 if accidental_prefix == "b" else (1 if accidental_prefix == "#" else 0)
    roman = match.group("roman")
    suffix = match.group("suffix") or ""

    upper_roman = roman.upper()
    if upper_roman not in ROMAN_TO_DEGREE:
        raise ValueError(f"Unsupported roman numeral: {token}")

    return RomanToken(
        accidental=accidental,
        degree=ROMAN_TO_DEGREE[upper_roman],
        roman=roman,
        suffix=suffix,
        lowered_case=roman.islower(),
    )


def infer_chord_quality(token: RomanToken) -> str:
    suffix = token.suffix.lower()
    if "dim" in suffix or "°" in suffix:
        return "dim"
    if "maj7" in suffix:
        return "maj7"
    if suffix.startswith("m7"):
        return "min7"
    if suffix == "7":
        return "min7" if token.lowered_case else "dominant7"
    if token.lowered_case:
        return "minor"
    return "major"


def scale_intervals(mode: str) -> list[int]:
    try:
        return get_scale(mode)
    except ValueError as exc:
        raise ValueError(f"Unsupported mode: {mode}") from exc


def chord_symbol(root_name: str, quality: str) -> str:
    if quality == "major":
        return root_name
    if quality == "minor":
        return f"{root_name}m"
    if quality == "dim":
        return f"{root_name}dim"
    if quality == "dominant7":
        return f"{root_name}7"
    if quality == "maj7":
        return f"{root_name}maj7"
    if quality == "min7":
        return f"{root_name}m7"
    raise ValueError(f"Unsupported chord quality: {quality}")


def resolve_roman_to_chord(token: str, tonic_pc: int, mode: str) -> Chord:
    parsed = parse_roman(token)
    intervals = scale_intervals(mode)
    root_pc = (tonic_pc + intervals[parsed.degree - 1] + parsed.accidental) % 12
    quality = infer_chord_quality(parsed)
    tones = tuple((root_pc + interval) % 12 for interval in CHORD_TONE_INTERVALS[quality])
    prefer_flats = "b" in token
    root_name = pc_to_name(root_pc, prefer_flats=prefer_flats)
    return Chord(
        root_pc=root_pc,
        root_name=root_name,
        quality=quality,
        symbol=chord_symbol(root_name, quality),
        roman=token,
        tones=tones,
    )
