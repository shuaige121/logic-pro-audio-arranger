from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path

from .models import NoteEvent


@dataclass(frozen=True)
class MidiTrack:
    name: str
    channel: int
    program: int
    notes: tuple[NoteEvent, ...]


def _varlen(value: int) -> bytes:
    if value < 0:
        raise ValueError("Variable-length quantity must be non-negative")
    data = [value & 0x7F]
    value >>= 7
    while value:
        data.append((value & 0x7F) | 0x80)
        value >>= 7
    return bytes(reversed(data))


def _seconds_to_ticks(seconds: float, tempo_bpm: float, ticks_per_beat: int) -> int:
    beats = max(0.0, seconds) * tempo_bpm / 60.0
    return int(round(beats * ticks_per_beat))


def _build_track_bytes(track: MidiTrack, tempo_bpm: float, ticks_per_beat: int) -> bytes:
    events: list[tuple[int, int, bytes]] = []
    channel = max(0, min(15, track.channel))
    program = max(0, min(127, track.program))

    name_bytes = track.name.encode("utf-8", errors="ignore")
    events.append((0, 0, bytes([0xFF, 0x03]) + _varlen(len(name_bytes)) + name_bytes))
    events.append((0, 1, bytes([0xC0 | channel, program])))

    for note in track.notes:
        start_tick = _seconds_to_ticks(note.start, tempo_bpm, ticks_per_beat)
        end_tick = _seconds_to_ticks(note.end, tempo_bpm, ticks_per_beat)
        if end_tick <= start_tick:
            end_tick = start_tick + 1
        pitch = max(0, min(127, note.pitch))
        velocity = max(1, min(127, note.velocity))
        events.append((start_tick, 2, bytes([0x90 | channel, pitch, velocity])))
        events.append((end_tick, 0, bytes([0x80 | channel, pitch, 0])))

    events.sort(key=lambda item: (item[0], item[1]))

    chunk = bytearray()
    previous_tick = 0
    for tick, _, payload in events:
        delta = tick - previous_tick
        chunk.extend(_varlen(delta))
        chunk.extend(payload)
        previous_tick = tick

    chunk.extend(_varlen(0))
    chunk.extend(bytes([0xFF, 0x2F, 0x00]))
    return bytes(chunk)


def write_multi_track_midi(
    path: str | Path,
    tracks: list[MidiTrack],
    tempo_bpm: float,
    ticks_per_beat: int = 480,
) -> None:
    if tempo_bpm <= 0:
        raise ValueError("tempo_bpm must be positive")
    if not tracks:
        raise ValueError("At least one track is required")

    tempo_us_per_qn = int(round(60_000_000.0 / tempo_bpm))
    tempo_meta = bytes(
        [0x00, 0xFF, 0x51, 0x03]
        + [
            (tempo_us_per_qn >> 16) & 0xFF,
            (tempo_us_per_qn >> 8) & 0xFF,
            tempo_us_per_qn & 0xFF,
        ]
        + [0x00, 0xFF, 0x2F, 0x00]
    )

    header = b"MThd" + struct.pack(">IHHH", 6, 1, len(tracks) + 1, ticks_per_beat)
    chunks = [b"MTrk" + struct.pack(">I", len(tempo_meta)) + tempo_meta]

    for track in tracks:
        payload = _build_track_bytes(track, tempo_bpm=tempo_bpm, ticks_per_beat=ticks_per_beat)
        chunks.append(b"MTrk" + struct.pack(">I", len(payload)) + payload)

    Path(path).write_bytes(header + b"".join(chunks))
