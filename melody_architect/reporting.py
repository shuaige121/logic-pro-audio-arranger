from __future__ import annotations

from typing import Any


def to_markdown(report: dict[str, Any]) -> str:
    input_info = report["input"]
    key = report["key_estimate"]
    summary = report["melody_summary"]
    harmony = report["harmony"]["selected_candidate"]
    arrangement = report["arrangement"]
    validation = report["validation"]

    lines: list[str] = []
    lines.append("# Melody Architecture Report")
    lines.append("")
    lines.append("## Input")
    lines.append(f"- Source: `{input_info['source']}`")
    lines.append(f"- Tempo: {input_info['tempo_bpm']} BPM")
    lines.append(f"- Meter: {input_info['beats_per_bar']}/{input_info['beat_unit']}")
    lines.append(f"- Bars: {input_info['bar_count']}")
    lines.append(f"- Notes: {input_info['note_count']}")
    lines.append("")
    lines.append("## Tonality")
    lines.append(f"- Estimated key: **{key['tonic']} {key['mode']}**")
    lines.append(f"- Confidence score: {key['score']}")
    lines.append(f"- Margin to next candidate: {key['margin']}")
    lines.append("")
    lines.append("## Melody Summary")
    lines.append(f"- Pitch range: {summary['range_min']}–{summary['range_max']} (span {summary['range_span']} semitones)")
    lines.append(f"- Median pitch: {summary['median_pitch']}")
    lines.append(f"- Average note duration: {summary['avg_duration_sec']} sec")
    lines.append(f"- Phrase count: {len(summary['phrases'])}")
    lines.append("")
    lines.append("## Harmony")
    lines.append(f"- Style profile: `{report['harmony']['style']}`")
    lines.append(f"- Selected candidate: `{harmony['name']}`")
    lines.append(f"- Chords: {' | '.join(harmony['symbols'])}")
    lines.append(f"- Roman numerals: {' | '.join(harmony['romans'])}")
    lines.append(f"- Score: {harmony['score']}")
    lines.append(f"- Chord-tone coverage: {harmony['chord_tone_coverage']}")
    lines.append(f"- Strong-beat coverage: {harmony['strong_beat_coverage']}")
    lines.append("")
    lines.append("## Arrangement Plan")
    lines.append("- Layer suggestions:")
    for layer in arrangement["layers"]:
        lines.append(
            f"  - {layer['role']}: {layer['instrument']} ({layer['register']}, {layer['pattern']})"
        )
    lines.append("- Section plan:")
    for section in arrangement["sections"]:
        lines.append(
            f"  - {section['name']}: bars {section['start_bar']}–{section['end_bar']} ({section['focus']})"
        )
    lines.append("")
    lines.append("## Validation")
    lines.append(f"- Passed: `{validation['passed']}`")
    metrics = validation["metrics"]
    lines.append(f"- chord_tone_coverage: {metrics['chord_tone_coverage']}")
    lines.append(f"- strong_beat_coverage: {metrics['strong_beat_coverage']}")
    lines.append(f"- max_bass_root_leap_semitones: {metrics['max_bass_root_leap_semitones']}")
    lines.append(f"- melody_range_semitones: {metrics['melody_range_semitones']}")
    if validation["warnings"]:
        lines.append("- Warnings:")
        for warning in validation["warnings"]:
            lines.append(f"  - {warning}")
    else:
        lines.append("- Warnings: none")

    lines.append("")
    lines.append(f"_Generated at {report['generated_at_utc']}_")
    return "\n".join(lines)
