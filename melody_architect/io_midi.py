from __future__ import annotations

import struct
from bisect import bisect_right
from pathlib import Path

from .models import MelodyData, NoteEvent


class MidiParseError(RuntimeError):
    pass


def _read_varlen(data: bytes, pos: int) -> tuple[int, int]:
    value = 0
    while True:
        if pos >= len(data):
            raise MidiParseError("Unexpected EOF while reading variable-length quantity")
        byte = data[pos]
        pos += 1
        value = (value << 7) | (byte & 0x7F)
        if byte & 0x80 == 0:
            break
    return value, pos


class TickConverter:
    def __init__(self, tempo_events: list[tuple[int, int]], ticks_per_beat: int) -> None:
        if ticks_per_beat <= 0:
            raise ValueError("ticks_per_beat must be positive")
        if not tempo_events:
            tempo_events = [(0, 500000)]

        dedup: dict[int, int] = {tick: us for tick, us in tempo_events}
        events = sorted(dedup.items(), key=lambda item: item[0])
        if events[0][0] != 0:
            events.insert(0, (0, 500000))

        self.ticks_per_beat = ticks_per_beat
        self.ticks = [tick for tick, _ in events]
        self.us_per_qn = [us for _, us in events]
        self.start_secs: list[float] = []

        elapsed = 0.0
        for idx, tick in enumerate(self.ticks):
            if idx > 0:
                prev_tick = self.ticks[idx - 1]
                prev_us = self.us_per_qn[idx - 1]
                elapsed += (tick - prev_tick) * (prev_us / 1_000_000.0 / ticks_per_beat)
            self.start_secs.append(elapsed)

    @property
    def initial_tempo_bpm(self) -> float:
        return 60_000_000.0 / self.us_per_qn[0]

    def to_seconds(self, tick: int) -> float:
        idx = bisect_right(self.ticks, tick) - 1
        if idx < 0:
            idx = 0
        base_tick = self.ticks[idx]
        base_sec = self.start_secs[idx]
        sec_per_tick = self.us_per_qn[idx] / 1_000_000.0 / self.ticks_per_beat
        return base_sec + (tick - base_tick) * sec_per_tick


def _close_note(
    active_notes: dict[tuple[int, int], list[tuple[int, int, str]]],
    note_rows: list[tuple[int, int, int, int, str]],
    key: tuple[int, int],
    end_tick: int,
) -> None:
    stack = active_notes.get(key)
    if not stack:
        return
    start_tick, velocity, track_name = stack.pop(0)
    if end_tick <= start_tick:
        end_tick = start_tick + 1
    note_rows.append((start_tick, end_tick, key[1], velocity, track_name))


def _parse_track(
    track_data: bytes,
    track_index: int,
    tempo_events: list[tuple[int, int]],
    note_rows: list[tuple[int, int, int, int, str]],
) -> None:
    pos = 0
    tick = 0
    running_status: int | None = None
    track_name = f"track_{track_index + 1}"
    active_notes: dict[tuple[int, int], list[tuple[int, int, str]]] = {}

    while pos < len(track_data):
        delta, pos = _read_varlen(track_data, pos)
        tick += delta

        if pos >= len(track_data):
            break

        status_or_data = track_data[pos]
        if status_or_data < 0x80:
            if running_status is None:
                raise MidiParseError("Running status encountered before any status byte")
            status = running_status
        else:
            status = status_or_data
            running_status = status
            pos += 1

        if status == 0xFF:
            if pos >= len(track_data):
                raise MidiParseError("Truncated meta event")
            meta_type = track_data[pos]
            pos += 1
            length, pos = _read_varlen(track_data, pos)
            payload = track_data[pos : pos + length]
            pos += length

            if meta_type == 0x03:
                decoded = payload.decode("utf-8", errors="ignore").strip()
                if decoded:
                    track_name = decoded
            elif meta_type == 0x51 and len(payload) == 3:
                us_per_qn = (payload[0] << 16) | (payload[1] << 8) | payload[2]
                tempo_events.append((tick, us_per_qn))
            elif meta_type == 0x2F:
                break
            continue

        if status in (0xF0, 0xF7):
            length, pos = _read_varlen(track_data, pos)
            pos += length
            continue

        event_type = status & 0xF0
        channel = status & 0x0F
        data_len = 1 if event_type in (0xC0, 0xD0) else 2

        if pos >= len(track_data):
            break
        data1 = track_data[pos]
        pos += 1
        data2 = 0
        if data_len == 2:
            if pos >= len(track_data):
                break
            data2 = track_data[pos]
            pos += 1

        if event_type == 0x90:
            key = (channel, data1)
            if data2 == 0:
                _close_note(active_notes, note_rows, key, tick)
            else:
                active_notes.setdefault(key, []).append((tick, data2, track_name))
        elif event_type == 0x80:
            _close_note(active_notes, note_rows, (channel, data1), tick)

    for key, stack in active_notes.items():
        for start_tick, velocity, name in stack:
            note_rows.append((start_tick, start_tick + 1, key[1], velocity, name))


def load_midi(path: str | Path, beats_per_bar: int = 4) -> MelodyData:
    data = Path(path).read_bytes()
    if len(data) < 14 or data[:4] != b"MThd":
        raise MidiParseError("Not a valid MIDI file")

    header_len = struct.unpack(">I", data[4:8])[0]
    if header_len < 6:
        raise MidiParseError("Invalid MIDI header length")
    fmt, track_count, division = struct.unpack(">HHH", data[8:14])
    if fmt not in (0, 1):
        raise MidiParseError(f"Unsupported MIDI format: {fmt}")
    if division & 0x8000:
        raise MidiParseError("SMPTE time format is not supported")

    ticks_per_beat = division
    pos = 8 + header_len
    tempo_events: list[tuple[int, int]] = [(0, 500000)]
    note_rows: list[tuple[int, int, int, int, str]] = []

    for track_index in range(track_count):
        if pos + 8 > len(data) or data[pos : pos + 4] != b"MTrk":
            raise MidiParseError("Track chunk header missing")
        track_len = struct.unpack(">I", data[pos + 4 : pos + 8])[0]
        start = pos + 8
        end = start + track_len
        if end > len(data):
            raise MidiParseError("Track chunk exceeds file size")
        _parse_track(data[start:end], track_index, tempo_events, note_rows)
        pos = end

    converter = TickConverter(tempo_events, ticks_per_beat)
    notes = [
        NoteEvent(
            pitch=pitch,
            start=converter.to_seconds(start_tick),
            end=converter.to_seconds(end_tick),
            velocity=velocity,
            track=track_name,
        )
        for start_tick, end_tick, pitch, velocity, track_name in note_rows
    ]

    return MelodyData(
        notes=sorted(notes, key=lambda n: (n.start, n.pitch, n.end)),
        tempo_bpm=converter.initial_tempo_bpm,
        beats_per_bar=beats_per_bar,
        source=str(path),
        metadata={"ticks_per_beat": ticks_per_beat, "tempo_events": sorted(tempo_events)},
    )
