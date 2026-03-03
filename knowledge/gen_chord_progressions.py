#!/usr/bin/env python3
"""Generate and seed chord progressions knowledge into SQLite."""

from __future__ import annotations

import re
import sqlite3
from collections import Counter
from pathlib import Path

try:
    from knowledge.brave_search import batch_search
    from knowledge.init_db import init_db
except ModuleNotFoundError:
    # Support direct execution: python3 knowledge/gen_chord_progressions.py
    from brave_search import batch_search  # type: ignore
    from init_db import init_db  # type: ignore

DB_PATH = Path(__file__).parent / "knowledge.db"
TARGET_TOTAL = 80
TARGET_SEARCH_RECORDS = 40

STYLES = (
    "pop",
    "rock",
    "jazz",
    "r&b",
    "edm",
    "classical",
    "folk",
    "latin",
    "blues",
    "country",
)

DEFAULT_ENERGY_BY_STYLE = {
    "pop": "medium",
    "rock": "high",
    "jazz": "medium",
    "r&b": "low",
    "edm": "high",
    "classical": "low",
    "folk": "medium",
    "latin": "high",
    "blues": "medium",
    "country": "medium",
}

HARD_CODED_PROGRESSIONS = [
    {
        "name": "Pop Axis Loop",
        "style": "pop",
        "roman_numerals": "I-V-vi-IV",
        "mode": "major",
        "bars": 4,
        "description": "Axis-style loop used heavily in modern pop choruses.",
        "example_songs": "Let It Be; With or Without You; No Woman No Cry",
        "energy_level": "medium",
        "source": "hardcoded:common_pop",
    },
    {
        "name": "Pop Sensitive Loop",
        "style": "pop",
        "roman_numerals": "vi-IV-I-V",
        "mode": "major",
        "bars": 4,
        "description": "Emotional pop progression common in verse-to-chorus writing.",
        "example_songs": "Someone Like You; Apologize",
        "energy_level": "medium",
        "source": "hardcoded:common_pop",
    },
    {
        "name": "Pop 50s Progression",
        "style": "pop",
        "roman_numerals": "I-vi-IV-V",
        "mode": "major",
        "bars": 4,
        "description": "Classic doo-wop inspired 50s progression.",
        "example_songs": "Stand by Me; Heart and Soul",
        "energy_level": "medium",
        "source": "hardcoded:common_pop",
    },
    {
        "name": "Pop Lift Loop",
        "style": "pop",
        "roman_numerals": "I-IV-vi-V",
        "mode": "major",
        "bars": 4,
        "description": "Stable major loop with a broad, uplifting contour.",
        "example_songs": "Every Breath You Take; Complicated",
        "energy_level": "high",
        "source": "hardcoded:common_pop",
    },
    {
        "name": "Rock Mixolydian Core",
        "style": "rock",
        "roman_numerals": "I-bVII-IV",
        "mode": "mixolydian",
        "bars": 4,
        "description": "Modal rock core progression with flat seventh color.",
        "example_songs": "Sweet Home Alabama; All Right Now",
        "energy_level": "high",
        "source": "hardcoded:common_rock",
    },
    {
        "name": "Rock Riff Driver",
        "style": "rock",
        "roman_numerals": "I-IV-V-IV",
        "mode": "major",
        "bars": 4,
        "description": "Riff-friendly loop for energetic rock choruses.",
        "example_songs": "Twist and Shout",
        "energy_level": "high",
        "source": "hardcoded:common_rock",
    },
    {
        "name": "Rock Anthem Loop",
        "style": "rock",
        "roman_numerals": "I-bIII-bVII-IV",
        "mode": "mixolydian",
        "bars": 4,
        "description": "Power-chord centric anthem progression.",
        "example_songs": "Smoke on the Water style",
        "energy_level": "high",
        "source": "hardcoded:common_rock",
    },
    {
        "name": "Rock Minor Descent",
        "style": "rock",
        "roman_numerals": "i-bVI-bIII-bVII",
        "mode": "minor",
        "bars": 4,
        "description": "Minor-mode descending rock progression.",
        "example_songs": "Numb; Boulevard of Broken Dreams",
        "energy_level": "high",
        "source": "hardcoded:common_rock",
    },
    {
        "name": "Jazz ii-V-I",
        "style": "jazz",
        "roman_numerals": "ii7-V7-Imaj7",
        "mode": "major",
        "bars": 4,
        "description": "Foundational jazz cadence in major keys.",
        "example_songs": "Autumn Leaves style",
        "energy_level": "medium",
        "source": "hardcoded:common_jazz",
    },
    {
        "name": "Jazz Rhythm Changes A",
        "style": "jazz",
        "roman_numerals": "Imaj7-vi7-ii7-V7",
        "mode": "major",
        "bars": 4,
        "description": "Core turnaround used in standards and bebop lines.",
        "example_songs": "I Got Rhythm changes",
        "energy_level": "medium",
        "source": "hardcoded:common_jazz",
    },
    {
        "name": "Jazz Circle Sequence",
        "style": "jazz",
        "roman_numerals": "iii7-vi7-ii7-V7",
        "mode": "major",
        "bars": 4,
        "description": "Circle-of-fifths sequence leading to tonic.",
        "example_songs": "All the Things You Are style",
        "energy_level": "medium",
        "source": "hardcoded:common_jazz",
    },
    {
        "name": "Jazz Blues Core",
        "style": "jazz",
        "roman_numerals": "I7-IV7-I7-V7",
        "mode": "blues",
        "bars": 4,
        "description": "Dominant-function jazz blues skeleton.",
        "example_songs": "C Jam Blues style",
        "energy_level": "medium",
        "source": "hardcoded:common_jazz",
    },
    {
        "name": "R&B Soul Lift",
        "style": "r&b",
        "roman_numerals": "I-IV-vi-V",
        "mode": "major",
        "bars": 4,
        "description": "Soul-pop hybrid loop with warm pre-dominant motion.",
        "example_songs": "Ain't No Mountain High Enough style",
        "energy_level": "medium",
        "source": "hardcoded:common_rnb",
    },
    {
        "name": "R&B Modern Loop",
        "style": "r&b",
        "roman_numerals": "vi-IV-I-V",
        "mode": "major",
        "bars": 4,
        "description": "Modern R&B chord cycle balancing tension and release.",
        "example_songs": "Halo; If I Ain't Got You",
        "energy_level": "low",
        "source": "hardcoded:common_rnb",
    },
    {
        "name": "R&B Tonic Return",
        "style": "r&b",
        "roman_numerals": "I-vi-IV-I",
        "mode": "major",
        "bars": 4,
        "description": "Tonic-return loop for intimate vocal lines.",
        "example_songs": "Use Me style",
        "energy_level": "low",
        "source": "hardcoded:common_rnb",
    },
    {
        "name": "R&B Jazz Touch",
        "style": "r&b",
        "roman_numerals": "ii7-V7-Imaj7-vi7",
        "mode": "major",
        "bars": 4,
        "description": "Jazz-inflected R&B cadence with smooth voice-leading.",
        "example_songs": "Neo-soul standard practice",
        "energy_level": "medium",
        "source": "hardcoded:common_rnb",
    },
    {
        "name": "EDM Mainstage Loop",
        "style": "edm",
        "roman_numerals": "vi-IV-I-V",
        "mode": "major",
        "bars": 4,
        "description": "Mainstage EDM loop used for build/drop sections.",
        "example_songs": "Wake Me Up style",
        "energy_level": "high",
        "source": "hardcoded:common_edm",
    },
    {
        "name": "EDM Minor Festival",
        "style": "edm",
        "roman_numerals": "i-bVI-bVII-i",
        "mode": "minor",
        "bars": 4,
        "description": "Minor EDM loop with strong cyclical return.",
        "example_songs": "Festival trap style",
        "energy_level": "high",
        "source": "hardcoded:common_edm",
    },
    {
        "name": "EDM Melodic Minor",
        "style": "edm",
        "roman_numerals": "i-bVI-bIII-bVII",
        "mode": "minor",
        "bars": 4,
        "description": "Melodic EDM loop common in progressive and trance.",
        "example_songs": "Progressive house style",
        "energy_level": "high",
        "source": "hardcoded:common_edm",
    },
    {
        "name": "EDM Epic Sequence",
        "style": "edm",
        "roman_numerals": "I-V-vi-iii-IV-I-IV-V",
        "mode": "major",
        "bars": 8,
        "description": "Longer pop-classical hybrid loop for breakdowns.",
        "example_songs": "Canon-inspired electronic arrangements",
        "energy_level": "high",
        "source": "hardcoded:common_edm",
    },
    {
        "name": "Classical Authentic Cadence",
        "style": "classical",
        "roman_numerals": "I-IV-V-I",
        "mode": "major",
        "bars": 4,
        "description": "Basic tonal motion used across common-practice harmony.",
        "example_songs": "Elementary classical harmony",
        "energy_level": "low",
        "source": "hardcoded:common_classical",
    },
    {
        "name": "Classical Songbook Loop",
        "style": "classical",
        "roman_numerals": "I-vi-IV-V",
        "mode": "major",
        "bars": 4,
        "description": "Simple tonal progression connecting tonic and dominant.",
        "example_songs": "Classical-derived songbook harmony",
        "energy_level": "low",
        "source": "hardcoded:common_classical",
    },
    {
        "name": "Classical Predominant",
        "style": "classical",
        "roman_numerals": "I-ii-V-I",
        "mode": "major",
        "bars": 4,
        "description": "Predominant-to-dominant cadence frame.",
        "example_songs": "Bach chorale style",
        "energy_level": "low",
        "source": "hardcoded:common_classical",
    },
    {
        "name": "Classical Leading Tone Loop",
        "style": "classical",
        "roman_numerals": "I-IV-viio-I",
        "mode": "major",
        "bars": 4,
        "description": "Uses leading-tone diminished chord for resolution pull.",
        "example_songs": "Common-practice voice-leading",
        "energy_level": "low",
        "source": "hardcoded:common_classical",
    },
    {
        "name": "Folk Campfire",
        "style": "folk",
        "roman_numerals": "I-IV-V-I",
        "mode": "major",
        "bars": 4,
        "description": "Core campfire folk progression.",
        "example_songs": "This Land Is Your Land style",
        "energy_level": "medium",
        "source": "hardcoded:common_folk",
    },
    {
        "name": "Folk Open Guitar",
        "style": "folk",
        "roman_numerals": "I-V-IV-I",
        "mode": "major",
        "bars": 4,
        "description": "Open-chord friendly loop for acoustic strumming.",
        "example_songs": "American folk standard practice",
        "energy_level": "medium",
        "source": "hardcoded:common_folk",
    },
    {
        "name": "Folk Drone Loop",
        "style": "folk",
        "roman_numerals": "I-IV-I-V",
        "mode": "major",
        "bars": 4,
        "description": "Drone-friendly loop with repeated tonic anchoring.",
        "example_songs": "Traditional ballad accompaniment",
        "energy_level": "medium",
        "source": "hardcoded:common_folk",
    },
    {
        "name": "Folk Pre-Cadential",
        "style": "folk",
        "roman_numerals": "ii-IV-V-I",
        "mode": "major",
        "bars": 4,
        "description": "Folk-pop variant adding predominant lift.",
        "example_songs": "Modern indie-folk writing",
        "energy_level": "medium",
        "source": "hardcoded:common_folk",
    },
    {
        "name": "Latin Tonic Cadence",
        "style": "latin",
        "roman_numerals": "I-IV-V-V",
        "mode": "major",
        "bars": 4,
        "description": "Straight-ahead major Latin cadence with repeated dominant.",
        "example_songs": "Traditional dance accompaniment",
        "energy_level": "high",
        "source": "hardcoded:common_latin",
    },
    {
        "name": "Latin Minor Cadence",
        "style": "latin",
        "roman_numerals": "i-iv-V-V",
        "mode": "minor",
        "bars": 4,
        "description": "Minor cadence heard in bolero and ballad settings.",
        "example_songs": "Latin romantic standard practice",
        "energy_level": "medium",
        "source": "hardcoded:common_latin",
    },
    {
        "name": "Latin Modal Bounce",
        "style": "latin",
        "roman_numerals": "I-IV-bVII-IV",
        "mode": "mixolydian",
        "bars": 4,
        "description": "Modal bounce progression used in latin-rock crossover.",
        "example_songs": "Oye Como Va style",
        "energy_level": "high",
        "source": "hardcoded:common_latin",
    },
    {
        "name": "Latin Andalusian Touch",
        "style": "latin",
        "roman_numerals": "i-bVII-bVI-V",
        "mode": "minor",
        "bars": 4,
        "description": "Andalusian-inspired descent often adapted in Latin genres.",
        "example_songs": "Flamenco-pop influence",
        "energy_level": "high",
        "source": "hardcoded:common_latin",
    },
    {
        "name": "Blues Quick Change",
        "style": "blues",
        "roman_numerals": "I7-IV7-I7-V7",
        "mode": "blues",
        "bars": 4,
        "description": "Compact dominant blues frame for riff-based writing.",
        "example_songs": "Rock and roll blues backing",
        "energy_level": "medium",
        "source": "hardcoded:common_blues",
    },
    {
        "name": "Blues 12 Bar Standard",
        "style": "blues",
        "roman_numerals": "I7-I7-I7-I7-IV7-IV7-I7-I7-V7-IV7-I7-V7",
        "mode": "blues",
        "bars": 12,
        "description": "Standard 12-bar blues in dominant chords.",
        "example_songs": "Hoochie Coochie Man style",
        "energy_level": "medium",
        "source": "hardcoded:common_blues",
    },
    {
        "name": "Blues Turnaround Variant",
        "style": "blues",
        "roman_numerals": "I7-I7-IV7-I7-V7-IV7-I7-V7",
        "mode": "blues",
        "bars": 8,
        "description": "Eight-bar blues variant with turnaround close.",
        "example_songs": "Key to the Highway style",
        "energy_level": "medium",
        "source": "hardcoded:common_blues",
    },
    {
        "name": "Blues Quick IV",
        "style": "blues",
        "roman_numerals": "I7-IV7-I7-I7",
        "mode": "blues",
        "bars": 4,
        "description": "Quick-IV opening phrase found in many blues heads.",
        "example_songs": "Sweet Home Chicago style",
        "energy_level": "medium",
        "source": "hardcoded:common_blues",
    },
    {
        "name": "Country Core",
        "style": "country",
        "roman_numerals": "I-IV-V-I",
        "mode": "major",
        "bars": 4,
        "description": "Traditional country three-chord cadence.",
        "example_songs": "Jambalaya style",
        "energy_level": "medium",
        "source": "hardcoded:common_country",
    },
    {
        "name": "Country Ballad",
        "style": "country",
        "roman_numerals": "I-vi-IV-V",
        "mode": "major",
        "bars": 4,
        "description": "Ballad-friendly country-pop progression.",
        "example_songs": "Take Me Home Country Roads style",
        "energy_level": "medium",
        "source": "hardcoded:common_country",
    },
    {
        "name": "Country Pop Crossover",
        "style": "country",
        "roman_numerals": "I-V-vi-IV",
        "mode": "major",
        "bars": 4,
        "description": "Modern country crossover progression.",
        "example_songs": "Cruise style",
        "energy_level": "high",
        "source": "hardcoded:common_country",
    },
    {
        "name": "Country Train Beat",
        "style": "country",
        "roman_numerals": "I-IV-I-V",
        "mode": "major",
        "bars": 4,
        "description": "Train-beat compatible progression with tonic pedal feel.",
        "example_songs": "Classic honky-tonk accompaniment",
        "energy_level": "medium",
        "source": "hardcoded:common_country",
    },
]

STYLE_QUERIES = {
    "pop": [
        "common chord progressions pop songs examples",
        "popular pop chord changes roman numerals",
        "pop harmony progression analysis",
        "chord progression database pop",
    ],
    "rock": [
        "common chord progressions rock songs examples",
        "popular rock chord changes roman numerals",
        "rock harmony progression analysis",
        "chord progression database rock",
    ],
    "jazz": [
        "common chord progressions jazz songs examples",
        "popular jazz chord changes roman numerals",
        "jazz harmony progression analysis",
        "chord progression database jazz",
    ],
    "r&b": [
        "common chord progressions r&b songs examples",
        "popular neo soul r&b chord changes roman numerals",
        "r&b harmony progression analysis",
        "chord progression database r&b",
    ],
    "edm": [
        "common chord progressions edm songs examples",
        "popular edm chord changes roman numerals",
        "edm harmony progression analysis",
        "chord progression database edm",
    ],
    "classical": [
        "common chord progressions classical harmony examples",
        "popular classical chord changes roman numerals",
        "classical harmony progression analysis",
        "chord progression database classical",
    ],
    "folk": [
        "common chord progressions folk songs examples",
        "popular folk chord changes roman numerals",
        "folk harmony progression analysis",
        "chord progression database folk",
    ],
    "latin": [
        "common chord progressions latin songs examples",
        "popular latin chord changes roman numerals",
        "latin harmony progression analysis",
        "chord progression database latin",
    ],
    "blues": [
        "common chord progressions blues songs examples",
        "popular blues chord changes roman numerals",
        "blues harmony progression analysis",
        "chord progression database blues",
    ],
    "country": [
        "common chord progressions country songs examples",
        "popular country chord changes roman numerals",
        "country harmony progression analysis",
        "chord progression database country",
    ],
}

OFFLINE_SEARCH_FALLBACK = {
    "pop": [
        "I-IV-V-vi",
        "I-iii-IV-V",
        "IV-I-V-vi",
        "vi-V-IV-V",
        "I-V-vi-iii-IV-I-IV-V",
    ],
    "rock": [
        "I-V-bVII-IV",
        "i-VI-III-VII",
        "I-bVII-I-bVII",
        "i-bVII-bVI-V",
        "I-V-IV-I",
    ],
    "jazz": [
        "ii7-V7-I6",
        "vi7-ii7-V7-Imaj7",
        "iio7-V7-im7",
        "Imaj7-IV7-iii7-vi7",
        "ii7b5-V7b9-im7",
    ],
    "r&b": [
        "Imaj7-ii7-iii7-ii7",
        "vi7-ii7-V7-Imaj7",
        "Imaj7-VI7-ii7-V7",
        "IVmaj7-iii7-ii7-V7",
        "i7-iv7-v7-iv7",
    ],
    "edm": [
        "I-V-vi-IV",
        "i-VI-III-VII",
        "i-VII-VI-VII",
        "vi-I-V-IV",
        "IV-I-V-vi",
    ],
    "classical": [
        "I-vi-ii-V",
        "I-VI-ii-V",
        "i-iv-V-i",
        "I-viio-I6-IV",
        "I-V6-vi-iii-IV-I-IV-V",
    ],
    "folk": [
        "I-V-vi-IV",
        "I-bVII-IV-I",
        "I-IV-I-IV",
        "vi-IV-I-V",
        "I-ii-IV-V",
    ],
    "latin": [
        "i-bVII-bVI-bVII",
        "I-V-vi-IV",
        "I-bVII-IV-I",
        "ii-V-I-IV",
        "i-iv-bVII-III",
    ],
    "blues": [
        "I7-IV7-I7-I7",
        "IV7-IV7-I7-I7",
        "V7-IV7-I7-V7",
        "I7-VI7-ii7-V7",
        "I7-IV7-I7-VI7-II7-V7-I7-V7",
    ],
    "country": [
        "I-V-IV-V",
        "I-IV-I-IV",
        "I-ii-IV-V",
        "I-V-I-IV",
        "vi-IV-I-V",
    ],
}

ROMAN_TOKEN_PATTERN = (
    r"(?:b|#)?(?:VII|VI|IV|V|III|II|I|vii|vi|iv|v|iii|ii|i)"
    r"(?:maj13|maj11|maj9|maj7|maj6|mMaj7|m7b5|m13|m11|m9|m7|m6|m|7|9|11|13|"
    r"sus2|sus4|sus|add9|6|64|65|43|42|o|dim|aug|b9|#9|b5|#5)?"
)
TOKEN_RE = re.compile(rf"^{ROMAN_TOKEN_PATTERN}$")
DASHED_PROGRESS_RE = re.compile(
    rf"({ROMAN_TOKEN_PATTERN}(?:\s*[-\u2013\u2014>/|:]\s*{ROMAN_TOKEN_PATTERN}){{2,11}})"
)
SPACED_PROGRESS_RE = re.compile(rf"({ROMAN_TOKEN_PATTERN}(?:\s+{ROMAN_TOKEN_PATTERN}){{2,11}})")
SEPARATOR_RE = re.compile(r"[\s,;\.\-\u2013\u2014>/|:]+")


def clean_text(value: str, limit: int = 220) -> str:
    text = " ".join((value or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def canonicalize_token(token: str) -> str:
    tok = token.strip().replace("°", "o")
    tok = tok.replace("Vii", "vii")
    match = re.match(r"^(b|#)?(VII|VI|IV|V|III|II|I|vii|vi|iv|v|iii|ii|i)(.*)$", tok)
    if not match:
        return tok
    accidental, roman, suffix = match.groups()
    accidental = accidental or ""
    # Keep case from source roman; just normalize a few suffix variants.
    suffix = suffix.replace("Maj", "maj").replace("MIN", "m")
    return f"{accidental}{roman}{suffix}"


def normalize_progression(raw: str) -> str | None:
    parts = [p for p in SEPARATOR_RE.split(raw.replace("\u2014", "-").replace("\u2013", "-")) if p]
    tokens: list[str] = []
    for part in parts:
        token = canonicalize_token(part)
        if TOKEN_RE.match(token):
            tokens.append(token)
    if not (3 <= len(tokens) <= 12):
        return None
    return "-".join(tokens)


def extract_progressions(text: str) -> list[str]:
    if not text:
        return []

    candidates: list[str] = []
    work = text.replace("\n", " ")

    for regex in (DASHED_PROGRESS_RE, SPACED_PROGRESS_RE):
        for match in regex.finditer(work):
            normalized = normalize_progression(match.group(1))
            if normalized:
                candidates.append(normalized)

    # Deduplicate while preserving order.
    seen: set[str] = set()
    ordered: list[str] = []
    for progression in candidates:
        if progression not in seen:
            seen.add(progression)
            ordered.append(progression)
    return ordered


def infer_mode(style: str, roman: str) -> str:
    tokens = roman.split("-")
    first = tokens[0].lstrip("b#")
    if first and first[0].islower():
        return "minor"
    if style == "blues":
        return "blues"
    if any(t.startswith("bVII") for t in tokens):
        return "mixolydian"
    return "major"


def infer_bars(style: str, roman: str) -> int:
    token_count = len(roman.split("-"))
    if style == "blues" and token_count >= 10:
        return 12
    if 3 <= token_count <= 8:
        return token_count
    return max(4, min(16, token_count))


def infer_energy(style: str, text_blob: str) -> str:
    lowered = text_blob.lower()
    if any(word in lowered for word in ("drop", "dance", "anthem", "festival", "driving", "aggressive", "upbeat")):
        return "high"
    if any(word in lowered for word in ("ballad", "soft", "gentle", "slow", "sad", "chill", "ambient")):
        return "low"
    return DEFAULT_ENERGY_BY_STYLE.get(style, "medium")


def guess_examples(title: str, description: str) -> str:
    blob = f"{title} {description}"
    quoted = re.findall(r'["\u201c\u201d\']([^"\u201c\u201d\']{2,60})["\u201c\u201d\']', blob)
    if quoted:
        picked = []
        for item in quoted:
            cleaned = clean_text(item, limit=60)
            if cleaned and cleaned not in picked:
                picked.append(cleaned)
            if len(picked) == 3:
                break
        return "; ".join(picked)

    if "song" in blob.lower() or "songs" in blob.lower():
        return clean_text(title, limit=100)
    return ""


def make_record(
    *,
    style: str,
    roman_numerals: str,
    description: str,
    example_songs: str,
    source: str,
    name: str = "",
    mode: str | None = None,
    bars: int | None = None,
    energy_level: str | None = None,
) -> dict:
    normalized = normalize_progression(roman_numerals)
    if not normalized:
        raise ValueError(f"Invalid progression: {roman_numerals}")

    computed_mode = mode or infer_mode(style, normalized)
    computed_bars = bars or infer_bars(style, normalized)
    computed_energy = energy_level or infer_energy(style, f"{description} {name} {normalized}")

    if computed_energy not in {"low", "medium", "high"}:
        computed_energy = "medium"

    return {
        "name": name or f"{style.title()} progression {normalized}",
        "style": style,
        "roman_numerals": normalized,
        "mode": computed_mode,
        "bars": int(computed_bars),
        "description": clean_text(description, limit=260),
        "example_songs": clean_text(example_songs, limit=180),
        "energy_level": computed_energy,
        "source": source,
    }


def dedupe_records(records: list[dict]) -> list[dict]:
    kept: dict[tuple[str, str, str], dict] = {}
    for record in records:
        key = (
            record["style"].strip().lower(),
            record["roman_numerals"].strip(),
            record["mode"].strip().lower(),
        )
        if key not in kept:
            kept[key] = record
            continue

        existing = kept[key]
        # Prefer hardcoded rows and keep richer descriptions.
        if existing["source"].startswith("hardcoded"):
            continue
        if record["source"].startswith("hardcoded"):
            kept[key] = record
            continue
        if len(record["description"]) > len(existing["description"]):
            kept[key] = record
    return list(kept.values())


def gather_search_records() -> list[dict]:
    query_to_style: dict[str, str] = {}
    queries: list[str] = []
    for style, style_queries in STYLE_QUERIES.items():
        for query in style_queries:
            query_to_style[query] = style
            queries.append(query)

    results = batch_search(queries, count=12, delay=0.07)

    extracted: list[dict] = []
    for row in results:
        query = row.get("query", "")
        style = query_to_style.get(query)
        if style not in STYLES:
            continue

        title = row.get("title", "")
        description = row.get("description", "")
        source = row.get("url", "") or "brave:unknown"
        blob = f"{title}. {description}"
        progressions = extract_progressions(blob)
        if not progressions:
            continue

        for progression in progressions:
            try:
                extracted.append(
                    make_record(
                        style=style,
                        roman_numerals=progression,
                        description=f"Parsed from Brave snippet: {clean_text(description, limit=190)}",
                        example_songs=guess_examples(title, description),
                        source=source,
                        name=f"{style.title()} search progression {progression}",
                    )
                )
            except ValueError:
                continue

    return dedupe_records(extracted)


def build_offline_supplement(limit: int, existing_records: list[dict]) -> list[dict]:
    existing_keys = {
        (r["style"], r["roman_numerals"], r["mode"])
        for r in existing_records
    }

    supplement: list[dict] = []
    style_cycle = list(STYLES)
    idx = 0

    while len(supplement) < limit and idx < 1000:
        style = style_cycle[idx % len(style_cycle)]
        choices = OFFLINE_SEARCH_FALLBACK.get(style, [])
        pick = choices[(idx // len(style_cycle)) % len(choices)] if choices else ""
        idx += 1
        if not pick:
            continue

        try:
            record = make_record(
                style=style,
                roman_numerals=pick,
                description="Offline fallback progression used when Brave snippets are unavailable in this runtime.",
                example_songs="",
                source="fallback:offline_search_unavailable",
                name=f"{style.title()} fallback progression {pick}",
            )
        except ValueError:
            continue

        key = (record["style"], record["roman_numerals"], record["mode"])
        if key in existing_keys:
            continue
        existing_keys.add(key)
        supplement.append(record)

    return supplement


def insert_records(records: list[dict]) -> tuple[int, list[tuple[str, int]]]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM chord_progressions")

    cur.executemany(
        """
        INSERT INTO chord_progressions
        (name, style, roman_numerals, mode, bars, description, example_songs, energy_level, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                r["name"],
                r["style"],
                r["roman_numerals"],
                r["mode"],
                r["bars"],
                r["description"],
                r["example_songs"],
                r["energy_level"],
                r["source"],
            )
            for r in records
        ],
    )

    conn.commit()

    total = cur.execute("SELECT COUNT(*) FROM chord_progressions").fetchone()[0]
    style_counts = cur.execute(
        "SELECT style, COUNT(*) FROM chord_progressions GROUP BY style ORDER BY style"
    ).fetchall()

    conn.close()
    return total, style_counts


def main() -> int:
    init_db(DB_PATH)

    hardcoded = dedupe_records(HARD_CODED_PROGRESSIONS)

    search_records = gather_search_records()

    combined = dedupe_records(hardcoded + search_records)

    search_gap = max(0, TARGET_SEARCH_RECORDS - len(search_records))
    supplement: list[dict] = []
    if search_gap > 0:
        supplement = build_offline_supplement(search_gap, combined)

    all_records = dedupe_records(combined + supplement)

    if len(all_records) < TARGET_TOTAL:
        extra_needed = TARGET_TOTAL - len(all_records)
        all_records = dedupe_records(all_records + build_offline_supplement(extra_needed, all_records))

    total, style_counts = insert_records(all_records)

    by_source = Counter(
        "hardcoded" if r["source"].startswith("hardcoded")
        else "brave" if r["source"].startswith("http")
        else "fallback"
        for r in all_records
    )

    print(
        "Loaded chord progressions: "
        f"total={total}, hardcoded={by_source['hardcoded']}, "
        f"brave={by_source['brave']}, fallback={by_source['fallback']}"
    )
    for style, count in style_counts:
        print(f"{style}: {count}")

    if total < TARGET_TOTAL:
        print(f"ERROR: total records {total} < target {TARGET_TOTAL}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
