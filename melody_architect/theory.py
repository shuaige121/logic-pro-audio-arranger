from __future__ import annotations

import math
import re
from dataclasses import dataclass

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
}

ROMAN_PATTERN = re.compile(r"^(?P<accidental>[b#]?)(?P<roman>[ivIV]+)(?P<suffix>.*)$")


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
    if mode not in MODE_INTERVALS:
        raise ValueError(f"Unsupported mode: {mode}")
    return MODE_INTERVALS[mode]


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
