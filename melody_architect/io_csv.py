from __future__ import annotations

import csv
from pathlib import Path

from .models import MelodyData, NoteEvent

PITCH_KEYS = ("pitch", "pitch_midi")
START_KEYS = ("start", "start_sec")
END_KEYS = ("end", "end_sec")
VELOCITY_KEYS = ("velocity",)


def _pick_first(row: dict[str, str], keys: tuple[str, ...], default: str | None = None) -> str:
    for key in keys:
        if key in row and row[key] != "":
            return row[key]
    if default is None:
        raise KeyError(f"Required column missing: one of {keys}")
    return default


def load_csv(path: str | Path, tempo_bpm: float = 120.0, beats_per_bar: int = 4) -> MelodyData:
    source = str(path)
    notes: list[NoteEvent] = []
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            pitch = int(float(_pick_first(row, PITCH_KEYS)))
            start = float(_pick_first(row, START_KEYS))
            end = float(_pick_first(row, END_KEYS))
            velocity = int(float(_pick_first(row, VELOCITY_KEYS, default="64")))
            notes.append(NoteEvent(pitch=pitch, start=start, end=end, velocity=velocity))

    return MelodyData(
        notes=sorted(notes, key=lambda n: (n.start, n.pitch, n.end)),
        tempo_bpm=tempo_bpm,
        beats_per_bar=beats_per_bar,
        source=source,
    )
