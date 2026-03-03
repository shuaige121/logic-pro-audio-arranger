from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
import re
import sqlite3

from .models import Chord, HarmonyCandidate, NoteEvent
from .theory import resolve_roman_to_chord


@dataclass(frozen=True)
class ProgressionTemplate:
    name: str
    tokens: tuple[str, ...]
    mode: str
    energy_level: str = "medium"
    mood: str = "neutral"


BASE_STYLE_TEMPLATES: dict[str, list[ProgressionTemplate]] = {
    "pop": [
        ProgressionTemplate("pop_primary", ("I", "V", "vi", "IV"), "major", "medium", "happy"),
        ProgressionTemplate("pop_alt", ("I", "vi", "IV", "V"), "major", "medium", "happy"),
        ProgressionTemplate("pop_desc", ("vi", "IV", "I", "V"), "major", "medium", "sad"),
        ProgressionTemplate("pop_minor", ("i", "bVII", "bVI", "bVII"), "minor", "medium", "sad"),
        ProgressionTemplate("pop_lift", ("I", "IV", "vi", "V"), "major", "high", "happy"),
        ProgressionTemplate("pop_drive", ("I", "V", "IV"), "major", "high", "happy"),
        ProgressionTemplate("pop_classic_cadence", ("IV", "V", "I"), "major", "medium", "happy"),
        ProgressionTemplate("pop_tonic_dominant", ("I", "IV", "V"), "major", "medium", "happy"),
        ProgressionTemplate("pop_jazz_touch", ("I", "vi", "ii", "V"), "major", "medium", "warm"),
    ],
    "rock": [
        ProgressionTemplate("rock_mixolydian_core", ("I", "bVII", "IV"), "mixolydian", "high", "energetic"),
        ProgressionTemplate("rock_riff_driver", ("I", "IV", "V", "IV"), "major", "high", "energetic"),
        ProgressionTemplate("rock_anthem_loop", ("I", "bIII", "bVII", "IV"), "mixolydian", "high", "energetic"),
        ProgressionTemplate("rock_minor_descent", ("i", "bVI", "bIII", "bVII"), "minor", "high", "tense"),
        ProgressionTemplate("rock_power_hook", ("I", "V", "bVII", "IV"), "mixolydian", "high", "energetic"),
    ],
    "modal": [
        ProgressionTemplate("modal_dorian", ("i7", "IV7"), "dorian", "medium", "cool"),
        ProgressionTemplate("modal_mixolydian", ("I7", "bVII7"), "mixolydian", "medium", "cool"),
        ProgressionTemplate("modal_aeolian_cycle", ("i", "bVII", "bVI", "bVII"), "minor", "low", "dark"),
        ProgressionTemplate("modal_dorian_turn", ("i7", "IV7", "i7", "v7"), "dorian", "medium", "cool"),
        ProgressionTemplate("modal_mixolydian_cadence", ("I", "bVII", "IV", "I"), "mixolydian", "medium", "earthy"),
    ],
    "jazz": [
        ProgressionTemplate("jazz_ii_v_i", ("ii7", "V7", "Imaj7"), "major", "medium", "smooth"),
        ProgressionTemplate("jazz_cycle", ("ii7", "V7", "Imaj7", "VI7"), "major", "medium", "smooth"),
        ProgressionTemplate("jazz_circle", ("iii7", "vi7", "ii7", "V7"), "major", "medium", "sophisticated"),
        ProgressionTemplate("jazz_rhythm_changes", ("Imaj7", "vi7", "ii7", "V7"), "major", "medium", "sophisticated"),
        ProgressionTemplate("jazz_blues_core", ("I7", "IV7", "I7", "V7"), "blues", "medium", "tense"),
    ],
    "rnb": [
        ProgressionTemplate("rnb_soul_lift", ("I", "IV", "vi", "V"), "major", "medium", "warm"),
        ProgressionTemplate("rnb_modern_loop", ("vi", "IV", "I", "V"), "major", "low", "sad"),
        ProgressionTemplate("rnb_jazz_touch", ("ii7", "V7", "Imaj7", "vi7"), "major", "medium", "smooth"),
        ProgressionTemplate("rnb_tonic_return", ("I", "vi", "IV", "I"), "major", "low", "intimate"),
        ProgressionTemplate("rnb_lush_turnaround", ("Imaj7", "VI7", "ii7", "V7"), "major", "low", "smooth"),
    ],
    "edm": [
        ProgressionTemplate("edm_mainstage_loop", ("vi", "IV", "I", "V"), "major", "high", "euphoric"),
        ProgressionTemplate("edm_minor_festival", ("i", "bVI", "bVII", "i"), "minor", "high", "tense"),
        ProgressionTemplate("edm_melodic_minor", ("i", "bVI", "bIII", "bVII"), "minor", "high", "dark"),
        ProgressionTemplate("edm_dark_drive", ("i", "bVII", "bVI", "V"), "minor", "high", "tense"),
        ProgressionTemplate("edm_pop_crossover", ("I", "V", "vi", "IV"), "major", "high", "happy"),
    ],
    "classical": [
        ProgressionTemplate("classical_authentic_cadence", ("I", "IV", "V", "I"), "major", "low", "resolved"),
        ProgressionTemplate("classical_songbook_loop", ("I", "vi", "IV", "V"), "major", "low", "warm"),
        ProgressionTemplate("classical_predominant", ("I", "ii", "V", "I"), "major", "low", "resolved"),
        ProgressionTemplate("classical_leading_tone", ("I", "IV", "viio", "I"), "major", "low", "tense"),
        ProgressionTemplate("classical_cadential_chain", ("I", "vi", "ii", "V"), "major", "low", "resolved"),
    ],
    "blues": [
        ProgressionTemplate("blues_quick_change", ("I7", "IV7", "I7", "V7"), "blues", "medium", "soulful"),
        ProgressionTemplate(
            "blues_12_bar",
            ("I7", "I7", "I7", "I7", "IV7", "IV7", "I7", "I7", "V7", "IV7", "I7", "V7"),
            "blues",
            "medium",
            "soulful",
        ),
        ProgressionTemplate("blues_turnaround_variant", ("I7", "I7", "IV7", "I7", "V7", "IV7", "I7", "V7"), "blues", "medium", "soulful"),
        ProgressionTemplate("blues_minor", ("i7", "iv7", "i7", "V7"), "minor", "medium", "sad"),
        ProgressionTemplate("blues_jazz", ("I7", "VI7", "ii7", "V7"), "blues", "medium", "tense"),
    ],
    "folk": [
        ProgressionTemplate("folk_campfire", ("I", "IV", "V", "I"), "major", "medium", "earthy"),
        ProgressionTemplate("folk_open_guitar", ("I", "V", "IV", "I"), "major", "medium", "earthy"),
        ProgressionTemplate("folk_drone_loop", ("I", "IV", "I", "V"), "major", "medium", "earthy"),
        ProgressionTemplate("folk_precadential", ("ii", "IV", "V", "I"), "major", "medium", "hopeful"),
        ProgressionTemplate("folk_axis_variant", ("vi", "IV", "I", "V"), "minor", "medium", "reflective"),
    ],
    "latin": [
        ProgressionTemplate("latin_tonic_cadence", ("I", "IV", "V", "V"), "major", "high", "dance"),
        ProgressionTemplate("latin_minor_cadence", ("i", "iv", "V", "V"), "minor", "medium", "passionate"),
        ProgressionTemplate("latin_modal_bounce", ("I", "IV", "bVII", "IV"), "mixolydian", "high", "dance"),
        ProgressionTemplate("latin_andalusian_touch", ("i", "bVII", "bVI", "V"), "minor", "high", "tense"),
        ProgressionTemplate("latin_turnaround", ("ii", "V", "I", "IV"), "major", "high", "bright"),
    ],
    "country": [
        ProgressionTemplate("country_core", ("I", "IV", "V", "I"), "major", "medium", "bright"),
        ProgressionTemplate("country_ballad", ("I", "vi", "IV", "V"), "major", "medium", "warm"),
        ProgressionTemplate("country_pop_crossover", ("I", "V", "vi", "IV"), "major", "high", "happy"),
        ProgressionTemplate("country_train_beat", ("I", "IV", "I", "V"), "major", "medium", "bright"),
        ProgressionTemplate("country_walkup", ("I", "ii", "IV", "V"), "major", "medium", "hopeful"),
    ],
}


_STYLE_ALIASES = {
    "r&b": "rnb",
}

_KNOWLEDGE_DB_PATH = Path(__file__).resolve().parent.parent / "knowledge" / "knowledge.db"


def _normalize_style(style: str) -> str:
    normalized = style.strip().lower()
    return _STYLE_ALIASES.get(normalized, normalized)


def _normalize_name(style: str, name: str, index: int) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    if not slug:
        slug = f"{style}_progression_{index}"
    if not slug.startswith(f"{style}_"):
        slug = f"{style}_{slug}"
    return slug


def _parse_roman_tokens(roman_numerals: str) -> tuple[str, ...]:
    return tuple(token.strip() for token in roman_numerals.split("-") if token.strip())


def _infer_mood(style: str, mode: str, energy_level: str, tokens: tuple[str, ...], description: str) -> str:
    text = description.lower()
    mode_key = mode.lower()

    if style == "blues":
        return "soulful"
    if any(word in text for word in ("intimate", "emotional", "ballad", "descent", "minor")):
        return "sad"
    if any(word in text for word in ("uplift", "anthem", "mainstage", "festival", "build", "drop")):
        return "happy" if mode_key in {"major", "mixolydian"} else "tense"
    if energy_level == "high" and any(token.startswith("V7") or token.startswith("bII") for token in tokens):
        return "tense"
    if mode_key in {"minor", "aeolian", "dorian", "phrygian"}:
        return "sad"
    if energy_level == "high":
        return "happy"
    if energy_level == "low":
        return "calm"
    if style in {"jazz", "rnb"}:
        return "smooth"
    return "neutral"


def _load_templates_from_db(db_path: Path) -> dict[str, list[ProgressionTemplate]]:
    if not db_path.exists():
        return {}

    query = """
    SELECT name, style, roman_numerals, mode, energy_level, description
    FROM chord_progressions
    ORDER BY style, id
    """
    loaded: dict[str, list[ProgressionTemplate]] = defaultdict(list)

    try:
        with sqlite3.connect(db_path) as conn:
            rows = conn.execute(query).fetchall()
    except sqlite3.Error:
        return {}

    for index, (name, raw_style, roman_numerals, mode, energy_level, description) in enumerate(rows, start=1):
        style = _normalize_style(raw_style or "")
        tokens = _parse_roman_tokens(roman_numerals or "")
        if not style or not tokens:
            continue

        mode_value = (mode or "major").strip().lower() or "major"
        energy_value = (energy_level or "medium").strip().lower() or "medium"
        mood = _infer_mood(style, mode_value, energy_value, tokens, description or "")
        template_name = _normalize_name(style, name or "", index)
        loaded[style].append(
            ProgressionTemplate(
                name=template_name,
                tokens=tokens,
                mode=mode_value,
                energy_level=energy_value,
                mood=mood,
            )
        )
    return dict(loaded)


def _merge_templates(
    base_templates: dict[str, list[ProgressionTemplate]],
    db_templates: dict[str, list[ProgressionTemplate]],
) -> dict[str, list[ProgressionTemplate]]:
    merged = {style: list(templates) for style, templates in base_templates.items()}
    for style, templates in db_templates.items():
        target = merged.setdefault(style, [])
        seen_signatures = {(item.tokens, item.mode.lower()) for item in target}
        for template in templates:
            signature = (template.tokens, template.mode.lower())
            if signature in seen_signatures:
                continue
            target.append(template)
            seen_signatures.add(signature)
    return merged


STYLE_TEMPLATES: dict[str, list[ProgressionTemplate]] = _merge_templates(
    BASE_STYLE_TEMPLATES,
    _load_templates_from_db(_KNOWLEDGE_DB_PATH),
)


def get_progressions_by_style(style: str) -> list[ProgressionTemplate]:
    style_key = _normalize_style(style)
    return list(STYLE_TEMPLATES.get(style_key, ()))


def get_progressions_by_mood(mood: str) -> list[ProgressionTemplate]:
    mood_key = mood.strip().lower()
    if not mood_key:
        return []

    matches: list[ProgressionTemplate] = []
    for templates in STYLE_TEMPLATES.values():
        matches.extend(template for template in templates if template.mood.lower() == mood_key)
    return matches


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
    style_key = _normalize_style(style)
    if style_key not in STYLE_TEMPLATES:
        raise ValueError(f"Unsupported style: {style}")

    templates = list(STYLE_TEMPLATES[style_key])
    if style_key == "pop" and include_borrowed_iv:
        templates.append(ProgressionTemplate("pop_borrowed_iv", ("I", "V", "vi", "iv"), "major", "medium", "tense"))
    if style_key == "jazz" and include_tritone_sub:
        templates.append(ProgressionTemplate("jazz_tritone", ("ii7", "bII7", "Imaj7"), "major", "high", "tense"))

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
