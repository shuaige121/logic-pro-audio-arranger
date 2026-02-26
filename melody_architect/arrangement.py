from __future__ import annotations

from .models import Chord


STYLE_LAYERS = {
    "pop": [
        {"role": "lead", "instrument": "vocal_or_lead_synth", "register": "C4-A5", "pattern": "phrase-driven"},
        {"role": "harmony", "instrument": "piano_or_guitar", "register": "C3-C5", "pattern": "arpeggio_or_block"},
        {"role": "bass", "instrument": "electric_bass", "register": "E1-C3", "pattern": "root_plus_connecting_tones"},
        {"role": "texture", "instrument": "pad_or_strings", "register": "G3-G5", "pattern": "long_sustain"},
        {"role": "rhythm", "instrument": "drum_kit", "register": "full", "pattern": "kick_snare_hat"},
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


def _build_sections(bar_count: int, style: str) -> list[dict[str, object]]:
    if bar_count <= 4:
        return [
            {"name": "A", "start_bar": 1, "end_bar": bar_count, "focus": "present_theme"},
        ]

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
        "mix_recommendations": _mix_recommendations(style, median_pitch),
    }
