from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .analysis import estimate_key, infer_bar_count, melody_summary
from .arrangement import suggest_arrangement
from .harmony import generate_harmony_candidates
from .io_audio import load_audio
from .io_csv import load_csv
from .io_midi import load_midi
from .io_musicxml import load_musicxml
from .models import MelodyData
from .validation import validate_arrangement


def load_input_file(path: str | Path, tempo_override: float | None = None, beats_per_bar: int = 4) -> MelodyData:
    suffix = Path(path).suffix.lower()
    if suffix in {".csv"}:
        data = load_csv(path, tempo_bpm=tempo_override or 120.0, beats_per_bar=beats_per_bar)
    elif suffix in {".mid", ".midi"}:
        data = load_midi(path, beats_per_bar=beats_per_bar)
    elif suffix in {".xml", ".musicxml", ".mxl"}:
        data = load_musicxml(path, default_tempo=tempo_override or 120.0)
    elif suffix in {".wav", ".aif", ".aiff"}:
        data = load_audio(path, tempo_bpm=tempo_override, beats_per_bar=beats_per_bar)
    else:
        raise ValueError(f"Unsupported input type: {suffix}")

    if tempo_override is not None:
        data.tempo_bpm = tempo_override
    data.beats_per_bar = beats_per_bar
    return data


def analyze_melody_data(
    data: MelodyData,
    style: str = "pop",
    bars: int | None = None,
    forced_mode: str | None = None,
    include_borrowed_iv: bool = True,
    include_tritone_sub: bool = True,
    top_k: int = 3,
) -> dict[str, object]:
    notes = data.sorted_notes()
    if not notes:
        raise ValueError("No notes available for analysis")

    key = estimate_key(notes)
    summary = melody_summary(data)
    bar_count = bars if bars is not None else infer_bar_count(data)

    candidates = generate_harmony_candidates(
        notes=notes,
        tonic_pc=key.tonic_pc,
        detected_mode=key.mode,
        style=style,
        bar_count=bar_count,
        beats_per_bar=data.beats_per_bar,
        tempo_bpm=data.tempo_bpm,
        mode_override=forced_mode,
        include_borrowed_iv=include_borrowed_iv,
        include_tritone_sub=include_tritone_sub,
    )

    best = candidates[0]
    arrangement = suggest_arrangement(style, bar_count, int(summary["median_pitch"]), best.bars)
    validation = validate_arrangement(
        notes=notes,
        chords=best.bars,
        chord_tone_coverage=best.chord_tone_coverage,
        strong_beat_coverage=best.strong_beat_coverage,
    )

    candidate_rows = []
    for candidate in candidates[: max(1, top_k)]:
        candidate_rows.append(
            {
                "name": candidate.name,
                "mode": candidate.mode,
                "score": candidate.score,
                "chord_tone_coverage": candidate.chord_tone_coverage,
                "strong_beat_coverage": candidate.strong_beat_coverage,
                "romans": [chord.roman for chord in candidate.bars],
                "symbols": [chord.symbol for chord in candidate.bars],
            }
        )

    now = datetime.now(tz=timezone.utc).isoformat()
    return {
        "project": "melody-architecture-lab",
        "generated_at_utc": now,
        "input": {
            "source": data.source,
            "tempo_bpm": round(data.tempo_bpm, 4),
            "beats_per_bar": data.beats_per_bar,
            "beat_unit": data.beat_unit,
            "bar_count": bar_count,
            "note_count": len(notes),
            "metadata": data.metadata,
        },
        "key_estimate": {
            "tonic": key.tonic_name,
            "mode": key.mode,
            "score": round(key.score, 4),
            "margin": round(key.margin, 4),
        },
        "melody_summary": summary,
        "harmony": {
            "style": style,
            "selected_candidate": candidate_rows[0],
            "top_candidates": candidate_rows,
        },
        "arrangement": arrangement,
        "validation": validation,
    }


def analyze_file(
    path: str | Path,
    style: str = "pop",
    bars: int | None = None,
    tempo_override: float | None = None,
    beats_per_bar: int = 4,
    forced_mode: str | None = None,
    include_borrowed_iv: bool = True,
    include_tritone_sub: bool = True,
    top_k: int = 3,
) -> dict[str, object]:
    data = load_input_file(path, tempo_override=tempo_override, beats_per_bar=beats_per_bar)
    return analyze_melody_data(
        data=data,
        style=style,
        bars=bars,
        forced_mode=forced_mode,
        include_borrowed_iv=include_borrowed_iv,
        include_tritone_sub=include_tritone_sub,
        top_k=top_k,
    )
