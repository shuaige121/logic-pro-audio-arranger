from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import MelodyData, NoteEvent

COMPOSITION_SCHEMA_VERSION = "1.0.0"


def _note_to_dict(note: NoteEvent) -> dict[str, Any]:
    return {
        "pitch": note.pitch,
        "start": round(note.start, 6),
        "end": round(note.end, 6),
        "velocity": note.velocity,
        "track": note.track,
    }


def _dict_to_note(payload: dict[str, Any]) -> NoteEvent:
    return NoteEvent(
        pitch=int(payload["pitch"]),
        start=float(payload["start"]),
        end=float(payload["end"]),
        velocity=int(payload.get("velocity", 64)),
        track=payload.get("track"),
    )


def build_composition_document(data: MelodyData, report: dict[str, Any]) -> dict[str, Any]:
    now = datetime.now(tz=timezone.utc).isoformat()
    return {
        "schema": "melody_architect.composition",
        "schema_version": COMPOSITION_SCHEMA_VERSION,
        "created_at_utc": now,
        "source": {
            "input_path": data.source,
            "tempo_bpm": round(data.tempo_bpm, 6),
            "beats_per_bar": data.beats_per_bar,
            "beat_unit": data.beat_unit,
            "metadata": data.metadata,
        },
        "melody": {
            "note_count": len(data.notes),
            "notes": [_note_to_dict(note) for note in data.sorted_notes()],
        },
        # Keep full analysis evidence so AI/arranger can reason over structured context.
        "analysis_report": report,
    }


def composition_to_runtime(payload: dict[str, Any]) -> tuple[MelodyData, dict[str, Any]]:
    if payload.get("schema") != "melody_architect.composition":
        raise ValueError("Invalid composition schema")

    source = payload.get("source", {})
    melody = payload.get("melody", {})
    report = payload.get("analysis_report")
    if not isinstance(report, dict):
        raise ValueError("Composition is missing analysis_report")

    notes = [_dict_to_note(item) for item in melody.get("notes", [])]
    data = MelodyData(
        notes=notes,
        tempo_bpm=float(source.get("tempo_bpm", 120.0)),
        beats_per_bar=int(source.get("beats_per_bar", 4)),
        beat_unit=int(source.get("beat_unit", 4)),
        source=str(source.get("input_path", "")),
        metadata=dict(source.get("metadata", {})),
    )
    return data, report


def save_composition(path: str | Path, payload: dict[str, Any]) -> None:
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_composition(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))
