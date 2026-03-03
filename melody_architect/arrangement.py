from __future__ import annotations

import json
import sqlite3
from functools import lru_cache
from pathlib import Path

from .models import Chord


KNOWLEDGE_DB_PATH = Path(__file__).resolve().parents[1] / "knowledge" / "knowledge.db"

STYLE_LAYERS = {
    "pop": [
        {"role": "lead", "instrument": "vocal_or_lead_synth", "register": "C4-A5", "pattern": "phrase-driven"},
        {"role": "harmony", "instrument": "piano_or_guitar", "register": "C3-C5", "pattern": "arpeggio_or_block"},
        {"role": "bass", "instrument": "electric_bass", "register": "E1-C3", "pattern": "root_plus_connecting_tones"},
        {"role": "texture", "instrument": "pad_or_strings", "register": "G3-G5", "pattern": "long_sustain"},
        {"role": "rhythm", "instrument": "drum_kit", "register": "full", "pattern": "kick_snare_hat"},
    ],
    "rock": [
        {"role": "lead", "instrument": "electric_guitar_or_vocal", "register": "D4-A5", "pattern": "riff_driven"},
        {"role": "harmony", "instrument": "rhythm_guitar", "register": "A2-E4", "pattern": "power_chords_or_open"},
        {"role": "bass", "instrument": "electric_bass", "register": "E1-G3", "pattern": "eighth_note_root"},
        {"role": "texture", "instrument": "distorted_guitar_layer", "register": "E3-B4", "pattern": "sustained_power"},
        {"role": "rhythm", "instrument": "drum_kit", "register": "full", "pattern": "driving_rock_beat"},
    ],
    "rnb": [
        {"role": "lead", "instrument": "vocal_or_lead_synth", "register": "C4-B5", "pattern": "melisma_with_space"},
        {"role": "harmony", "instrument": "electric_piano", "register": "C3-F5", "pattern": "lush_seventh_voicings"},
        {"role": "bass", "instrument": "sub_bass", "register": "E1-C3", "pattern": "syncopated_glide"},
        {"role": "texture", "instrument": "ambient_pad_or_guitar", "register": "G3-G5", "pattern": "counterphrases"},
        {"role": "rhythm", "instrument": "drum_machine", "register": "full", "pattern": "laid_back_backbeat"},
    ],
    "edm": [
        {"role": "lead", "instrument": "lead_synth_or_vocal_chop", "register": "C4-C6", "pattern": "hook_loop"},
        {"role": "harmony", "instrument": "supersaw_or_pluck", "register": "C3-C5", "pattern": "sidechained_chords"},
        {"role": "bass", "instrument": "sub_or_reese_bass", "register": "E1-C3", "pattern": "quarter_note_pulse"},
        {"role": "texture", "instrument": "fx_and_risers", "register": "high", "pattern": "build_and_release"},
        {"role": "rhythm", "instrument": "electronic_drums", "register": "full", "pattern": "four_on_floor"},
    ],
    "classical": [
        {"role": "lead", "instrument": "strings_or_woodwinds", "register": "C4-A5", "pattern": "thematic_development"},
        {"role": "harmony", "instrument": "strings_and_horns", "register": "C3-G5", "pattern": "functional_voice_leading"},
        {"role": "bass", "instrument": "cello_and_double_bass", "register": "C2-E3", "pattern": "root_and_counterline"},
        {"role": "texture", "instrument": "harp_or_inner_strings", "register": "C3-C6", "pattern": "ornamental_motion"},
        {"role": "rhythm", "instrument": "timpani_or_orchestral_percussion", "register": "full", "pattern": "dynamic_accents"},
    ],
    "blues": [
        {"role": "lead", "instrument": "vocal_or_blues_guitar", "register": "C4-A5", "pattern": "call_and_response"},
        {"role": "harmony", "instrument": "piano_or_guitar", "register": "C3-E5", "pattern": "dominant_voicing_comping"},
        {"role": "bass", "instrument": "electric_or_upright_bass", "register": "E1-C3", "pattern": "shuffle_walk"},
        {"role": "texture", "instrument": "organ_or_harmonica", "register": "G3-G5", "pattern": "fill_phrases"},
        {"role": "rhythm", "instrument": "drum_kit", "register": "full", "pattern": "shuffle_backbeat"},
    ],
    "folk": [
        {"role": "lead", "instrument": "vocal", "register": "C4-A5", "pattern": "storytelling_phrase"},
        {"role": "harmony", "instrument": "acoustic_guitar", "register": "C3-E5", "pattern": "open_strum_or_fingerpick"},
        {"role": "bass", "instrument": "upright_bass", "register": "E1-C3", "pattern": "roots_with_walkups"},
        {"role": "texture", "instrument": "mandolin_or_fiddle", "register": "G3-B5", "pattern": "light_countermelody"},
        {"role": "rhythm", "instrument": "shaker_or_brush_percussion", "register": "full", "pattern": "gentle_pulse"},
    ],
    "latin": [
        {"role": "lead", "instrument": "vocal_or_flute", "register": "C4-B5", "pattern": "syncopated_hook"},
        {"role": "harmony", "instrument": "piano_or_nylon_guitar", "register": "C3-F5", "pattern": "montuno_or_syncopated_chords"},
        {"role": "bass", "instrument": "bass_guitar", "register": "E1-C3", "pattern": "tumbao"},
        {"role": "texture", "instrument": "horns_or_aux_percussion", "register": "G3-C6", "pattern": "stabs_and_responses"},
        {"role": "rhythm", "instrument": "latin_percussion_kit", "register": "full", "pattern": "clave_driven_groove"},
    ],
    "country": [
        {"role": "lead", "instrument": "vocal", "register": "C4-A5", "pattern": "lyric_forward_hook"},
        {"role": "harmony", "instrument": "acoustic_and_electric_guitar", "register": "C3-E5", "pattern": "open_chords_and_picking"},
        {"role": "bass", "instrument": "electric_bass", "register": "E1-C3", "pattern": "two_beat_root_fifth"},
        {"role": "texture", "instrument": "pedal_steel_or_fiddle", "register": "G3-B5", "pattern": "answer_lines"},
        {"role": "rhythm", "instrument": "drum_kit", "register": "full", "pattern": "train_beat_or_half_time"},
    ],
    "modal": [
        {"role": "lead", "instrument": "lead_vocal_or_guitar", "register": "C4-A5", "pattern": "motif-loop"},
        {"role": "harmony", "instrument": "rhodes_or_clav", "register": "C3-C5", "pattern": "syncopated_comping"},
        {"role": "bass", "instrument": "finger_bass", "register": "E1-B2", "pattern": "groove_locked_to_kick"},
        {"role": "rhythm", "instrument": "drum_kit", "register": "full", "pattern": "backbeat_with_ghost_notes"},
    ],
    "jazz": [
        {"role": "lead", "instrument": "lead_voice_or_horn", "register": "B3-G5", "pattern": "phrase-driven"},
        {"role": "harmony", "instrument": "piano_or_guitar", "register": "C3-F5", "pattern": "shell_voicing_comping"},
        {"role": "bass", "instrument": "upright_or_electric_bass", "register": "E1-C3", "pattern": "walking_or_half_note"},
        {"role": "rhythm", "instrument": "drums", "register": "full", "pattern": "ride_hat_interaction"},
    ],
}


_FALLBACK_DRUM_PATTERNS: dict[str, dict[str, object]] = {
    "pop_basic": {
        "steps": 16,
        "kick": [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
        "snare": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
        "hihat": [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
    },
    "rock_basic": {
        "steps": 16,
        "kick": [1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0],
        "snare": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
        "hihat": [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
    },
    "rnb_basic": {
        "steps": 16,
        "kick": [1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0],
        "snare": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
        "hihat": [1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 0, 1, 1, 1, 0],
    },
    "edm_four_on_floor": {
        "steps": 16,
        "kick": [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
        "snare": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
        "hihat": [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0],
    },
    "classical_timpani_pulse": {
        "steps": 16,
        "kick": [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
        "snare": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "hihat": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    },
    "blues_shuffle": {
        "steps": 16,
        "kick": [1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0],
        "snare": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
        "hihat": [1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1],
    },
    "folk_brush": {
        "steps": 16,
        "kick": [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
        "snare": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
        "hihat": [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
    },
    "latin_clave": {
        "steps": 16,
        "kick": [1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0],
        "snare": [0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1],
        "hihat": [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
    },
    "country_train_beat": {
        "steps": 16,
        "kick": [1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0],
        "snare": [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0],
        "hihat": [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
    },
    "modal_backbeat": {
        "steps": 16,
        "kick": [1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0],
        "snare": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
        "hihat": [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
    },
    "jazz_swing": {
        "steps": 16,
        "kick": [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0],
        "snare": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0],
        "hihat": [1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1],
    },
}

_FALLBACK_BASS_PATTERNS: dict[str, dict[str, object]] = {
    "pop_root_fifth": {
        "steps": 16,
        "intervals": [0, -1, 7, -1, 0, -1, 7, -1, 0, -1, 7, -1, 0, -1, 7, -1],
    },
    "rock_eighth_note": {
        "steps": 16,
        "intervals": [0, 0, -1, 0, 0, -1, 0, 0, 7, 7, -1, 7, 0, 0, -1, 0],
    },
    "rnb_smooth": {
        "steps": 16,
        "intervals": [0, -1, -1, 7, -1, 5, -1, -1, 0, -1, -1, 4, -1, 5, -1, -1],
    },
    "edm_sidechain": {
        "steps": 16,
        "intervals": [0, -1, -1, -1, 0, -1, -1, -1, 0, -1, -1, -1, 0, -1, -1, -1],
    },
    "classical_pedal_tonic": {
        "steps": 16,
        "intervals": [0, -1, -1, -1, 0, -1, -1, -1, 0, -1, -1, -1, 7, -1, -1, -1],
    },
    "blues_shuffle_bass": {
        "steps": 16,
        "intervals": [0, -1, 0, -1, 3, -1, 3, -1, 5, -1, 5, -1, 6, -1, 6, -1],
    },
    "folk_simple": {
        "steps": 16,
        "intervals": [0, -1, -1, -1, 5, -1, -1, -1, 7, -1, -1, -1, 5, -1, -1, -1],
    },
    "latin_tumbao": {
        "steps": 16,
        "intervals": [0, -1, 5, -1, -1, 7, -1, 5, 0, -1, 5, -1, -1, 7, -1, 5],
    },
    "country_root_five": {
        "steps": 16,
        "intervals": [0, -1, 7, -1, 0, -1, 7, -1, 5, -1, 7, -1, 0, -1, 7, -1],
    },
    "modal_pedal": {
        "steps": 16,
        "intervals": [0, -1, -1, -1, 0, -1, 7, -1, 0, -1, -1, -1, 0, -1, 5, -1],
    },
    "jazz_walking": {
        "steps": 16,
        "intervals": [0, 2, 4, 5, 7, 6, 5, 4, 3, 2, 1, 0, -1, -1, -1, -1],
    },
}

_SECTION_PATTERN_COLUMNS = (
    "section_type",
    "style",
    "active_instruments",
    "texture_density",
    "energy_level",
    "melody_treatment",
    "harmony_treatment",
    "rhythm_treatment",
    "bass_treatment",
    "transition_in",
    "transition_out",
    "mood_function",
    "description",
    "source",
)


def _parse_pattern_data(raw_payload: str) -> dict[str, object] | None:
    try:
        parsed = json.loads(raw_payload)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict):
        return None
    return parsed


def _load_drum_patterns_from_db() -> dict[str, dict[str, object]]:
    if not KNOWLEDGE_DB_PATH.exists():
        return {}

    query = """
        SELECT name, style, pattern_data
        FROM rhythm_patterns
        WHERE instrument = 'drums' AND TRIM(name) <> ''
        ORDER BY id ASC
    """
    patterns: dict[str, dict[str, object]] = {}
    try:
        with sqlite3.connect(str(KNOWLEDGE_DB_PATH)) as conn:
            for name, style, payload in conn.execute(query):
                parsed = _parse_pattern_data(payload)
                if parsed is None:
                    continue
                key = str(name).strip()
                if not key:
                    continue
                patterns[key] = parsed
                basic_alias = f"{str(style).strip()}_basic"
                patterns.setdefault(basic_alias, parsed)
    except sqlite3.Error:
        return {}
    return patterns


def _load_bass_patterns_from_db() -> dict[str, dict[str, object]]:
    if not KNOWLEDGE_DB_PATH.exists():
        return {}

    query = """
        SELECT name, style, pattern_data
        FROM bass_patterns
        WHERE TRIM(name) <> ''
        ORDER BY id ASC
    """
    patterns: dict[str, dict[str, object]] = {}
    try:
        with sqlite3.connect(str(KNOWLEDGE_DB_PATH)) as conn:
            for name, style, payload in conn.execute(query):
                parsed = _parse_pattern_data(payload)
                if parsed is None:
                    continue
                key = str(name).strip()
                if not key:
                    continue
                patterns[key] = parsed
                basic_alias = f"{str(style).strip()}_basic"
                patterns.setdefault(basic_alias, parsed)
    except sqlite3.Error:
        return {}
    return patterns


DRUM_PATTERNS = {**_FALLBACK_DRUM_PATTERNS, **_load_drum_patterns_from_db()}
BASS_PATTERNS = {**_FALLBACK_BASS_PATTERNS, **_load_bass_patterns_from_db()}


def _decode_list(raw_value: str) -> list[str]:
    stripped = raw_value.strip()
    if not stripped:
        return []
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, list):
        return [str(item) for item in parsed]
    if "," in stripped:
        return [part.strip() for part in stripped.split(",") if part.strip()]
    return [stripped]


@lru_cache(maxsize=128)
def get_section_pattern(section_type: str, style: str) -> dict[str, object]:
    normalized_section = section_type.strip().lower()
    normalized_style = style.strip().lower()
    if not normalized_section or not KNOWLEDGE_DB_PATH.exists():
        return {}

    query = f"""
        SELECT {", ".join(_SECTION_PATTERN_COLUMNS)}
        FROM section_patterns
        WHERE lower(section_type) = ?
          AND (lower(style) = ? OR lower(style) = 'general' OR style = '')
        ORDER BY
            CASE
                WHEN lower(style) = ? THEN 0
                WHEN lower(style) = 'general' THEN 1
                ELSE 2
            END,
            id ASC
        LIMIT 1
    """

    try:
        with sqlite3.connect(str(KNOWLEDGE_DB_PATH)) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(query, (normalized_section, normalized_style, normalized_style)).fetchone()
    except sqlite3.Error:
        return {}

    if row is None:
        return {}

    pattern = {column: row[column] for column in _SECTION_PATTERN_COLUMNS}
    active_instruments = pattern.get("active_instruments")
    if isinstance(active_instruments, str):
        pattern["active_instruments"] = _decode_list(active_instruments)

    energy_level = pattern.get("energy_level")
    if isinstance(energy_level, str) and energy_level.isdigit():
        pattern["energy_level"] = int(energy_level)
    return pattern


def _expand_layout_lengths(layout: list[dict[str, object]], extra_bars: int, growth_order: tuple[int, ...]) -> None:
    cursor = 0
    while extra_bars > 0:
        idx = growth_order[cursor % len(growth_order)]
        layout[idx]["length"] = int(layout[idx]["length"]) + 1
        extra_bars -= 1
        cursor += 1


def _layout_to_sections(layout: list[dict[str, object]], style: str) -> list[dict[str, object]]:
    sections: list[dict[str, object]] = []
    start_bar = 1
    for item in layout:
        length = int(item["length"])
        end_bar = start_bar + length - 1
        section_name = str(item["name"])
        section = {
            "name": section_name,
            "start_bar": start_bar,
            "end_bar": end_bar,
            "focus": str(item["focus"]),
        }
        pattern = get_section_pattern(section_name, style)
        if pattern:
            section["pattern"] = pattern
        sections.append(section)
        start_bar = end_bar + 1
    return sections


def _patterns_for_style(patterns: dict[str, dict[str, object]], style: str) -> dict[str, dict[str, object]]:
    style_prefix = f"{style}_"
    return {name: payload for name, payload in patterns.items() if name.startswith(style_prefix)}


def _build_sections(bar_count: int, style: str) -> list[dict[str, object]]:
    if bar_count <= 4:
        return [
            {"name": "A", "start_bar": 1, "end_bar": bar_count, "focus": "present_theme"},
        ]

    if bar_count >= 32:
        layout = [
            {"name": "intro", "length": 2, "focus": "set_palette"},
            {"name": "verse", "length": 8, "focus": "introduce_main_motif"},
            {"name": "pre_chorus", "length": 4, "focus": "increase_tension"},
            {"name": "chorus", "length": 8, "focus": "deliver_primary_hook"},
            {"name": "bridge", "length": 4, "focus": "create_contrast"},
            {"name": "chorus", "length": 4, "focus": "return_to_hook"},
            {"name": "outro", "length": 2, "focus": "resolve_energy"},
        ]
        _expand_layout_lengths(layout, bar_count - 32, growth_order=(1, 3, 5, 4))
        return _layout_to_sections(layout, style)

    if bar_count >= 16:
        layout = [
            {"name": "intro", "length": 2, "focus": "set_palette"},
            {"name": "verse", "length": 8, "focus": "introduce_main_motif"},
            {"name": "chorus", "length": 6, "focus": "increase_density"},
        ]
        _expand_layout_lengths(layout, bar_count - 16, growth_order=(1, 2))
        return _layout_to_sections(layout, style)

    split = max(2, bar_count // 2)
    sections = [
        {"name": "Verse_or_A", "start_bar": 1, "end_bar": split, "focus": "introduce_main_motif"},
        {"name": "Chorus_or_B", "start_bar": split + 1, "end_bar": bar_count, "focus": "increase_density"},
    ]
    if style == "jazz" and bar_count >= 8:
        sections.append(
            {"name": "Turnaround", "start_bar": max(1, bar_count - 1), "end_bar": bar_count, "focus": "set_next_cycle"}
        )
    return sections


def _mix_recommendations(style: str, melody_median_pitch: int) -> list[str]:
    recommendations = [
        "Keep lead and bass as center anchors; spread harmony layers left/right for clarity.",
        "Automate section energy through instrumentation changes before heavy compression.",
    ]
    if melody_median_pitch <= 60:
        recommendations.append("Melody sits low; high-pass harmony layers and avoid dense low-mid pads.")
    else:
        recommendations.append("Melody sits mid/high; carve 2-4kHz space in accompaniment.")
    if style == "modal":
        recommendations.append("Prioritize groove consistency; avoid over-harmonizing each beat.")
    if style == "jazz":
        recommendations.append("Guide tones (3rd/7th) should stay clear in comping voicings.")
    if style == "edm":
        recommendations.append("Reserve sub-bass headroom; sidechain non-drum low content to the kick.")
    if style == "rock":
        recommendations.append("Balance guitars by role; avoid stacking identical distortion in the same register.")
    if style == "classical":
        recommendations.append("Keep orchestral doubling intentional; avoid masking melody in the midrange.")
    return recommendations


def suggest_arrangement(
    style: str,
    bar_count: int,
    median_pitch: int,
    chord_bars: tuple[Chord, ...],
) -> dict[str, object]:
    if style not in STYLE_LAYERS:
        raise ValueError(f"Unsupported style: {style}")

    chord_symbols = [chord.symbol for chord in chord_bars]
    return {
        "style": style,
        "layers": STYLE_LAYERS[style],
        "sections": _build_sections(bar_count, style),
        "chord_overview": chord_symbols,
        "drum_patterns": _patterns_for_style(DRUM_PATTERNS, style),
        "bass_patterns": _patterns_for_style(BASS_PATTERNS, style),
        "mix_recommendations": _mix_recommendations(style, median_pitch),
    }
