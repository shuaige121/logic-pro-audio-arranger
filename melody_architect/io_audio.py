from __future__ import annotations

import aifc
import math
import struct
import wave
from pathlib import Path
from statistics import median

from .models import MelodyData, NoteEvent


def _pcm_to_float_samples(raw: bytes, sample_width: int, channels: int, big_endian: bool = False) -> list[float]:
    if channels <= 0:
        raise ValueError("channels must be positive")
    if sample_width not in (1, 2, 3, 4):
        raise ValueError(f"Unsupported PCM width: {sample_width}")

    samples: list[float] = []
    frame_width = sample_width * channels
    if frame_width == 0:
        return samples

    for frame_offset in range(0, len(raw) - frame_width + 1, frame_width):
        frame = raw[frame_offset : frame_offset + frame_width]
        acc = 0.0
        for ch in range(channels):
            offset = ch * sample_width
            chunk = frame[offset : offset + sample_width]
            if sample_width == 1:
                value = chunk[0] - 128
                peak = 127.0
            elif sample_width == 2:
                fmt = ">h" if big_endian else "<h"
                value = struct.unpack(fmt, chunk)[0]
                peak = 32767.0
            elif sample_width == 3:
                if big_endian:
                    signed = int.from_bytes(chunk, byteorder="big", signed=False)
                else:
                    signed = int.from_bytes(chunk, byteorder="little", signed=False)
                if signed & 0x800000:
                    signed -= 0x1000000
                value = signed
                peak = 8_388_607.0
            else:
                fmt = ">i" if big_endian else "<i"
                value = struct.unpack(fmt, chunk)[0]
                peak = 2_147_483_647.0
            acc += value / peak
        samples.append(acc / channels)
    return samples


def _read_wav(path: str | Path) -> tuple[list[float], int]:
    with wave.open(str(path), "rb") as handle:
        channels = handle.getnchannels()
        sample_width = handle.getsampwidth()
        rate = handle.getframerate()
        frames = handle.getnframes()
        raw = handle.readframes(frames)
    return _pcm_to_float_samples(raw, sample_width, channels, big_endian=False), rate


def _read_aiff(path: str | Path) -> tuple[list[float], int]:
    with aifc.open(str(path), "rb") as handle:
        channels = handle.getnchannels()
        sample_width = handle.getsampwidth()
        rate = handle.getframerate()
        frames = handle.getnframes()
        raw = handle.readframes(frames)
    return _pcm_to_float_samples(raw, sample_width, channels, big_endian=True), rate


def _rms(frame: list[float]) -> float:
    if not frame:
        return 0.0
    return math.sqrt(sum(sample * sample for sample in frame) / len(frame))


def _autocorr_pitch(frame: list[float], sample_rate: int, min_hz: float, max_hz: float) -> tuple[float | None, float]:
    if not frame:
        return None, 0.0
    centered = [sample - (sum(frame) / len(frame)) for sample in frame]

    min_lag = max(1, int(sample_rate / max_hz))
    max_lag = min(len(centered) - 1, int(sample_rate / min_hz))
    if max_lag <= min_lag:
        return None, 0.0

    best_corr = -1.0
    best_lag = min_lag
    zero_lag = sum(sample * sample for sample in centered) + 1e-9

    for lag in range(min_lag, max_lag + 1):
        corr = 0.0
        upper = len(centered) - lag
        for idx in range(upper):
            corr += centered[idx] * centered[idx + lag]
        if corr > best_corr:
            best_corr = corr
            best_lag = lag

    confidence = max(0.0, best_corr / zero_lag)
    if best_corr <= 0.0:
        return None, confidence
    return sample_rate / best_lag, confidence


def _hz_to_midi(hz: float) -> int:
    if hz <= 0:
        return 0
    return int(round(69 + 12 * math.log2(hz / 440.0)))


def _estimate_tempo(onsets: list[float]) -> float:
    if len(onsets) < 2:
        return 120.0
    intervals = [onsets[idx] - onsets[idx - 1] for idx in range(1, len(onsets)) if onsets[idx] > onsets[idx - 1]]
    if not intervals:
        return 120.0
    beat = median(intervals)
    if beat <= 0:
        return 120.0
    bpm = 60.0 / beat
    while bpm < 70.0:
        bpm *= 2.0
    while bpm > 180.0:
        bpm /= 2.0
    return bpm


def _merge_notes(notes: list[NoteEvent], max_gap_sec: float = 0.04, max_pitch_delta: int = 1) -> list[NoteEvent]:
    if not notes:
        return []
    merged: list[NoteEvent] = []
    current = notes[0]
    for note in notes[1:]:
        gap = note.start - current.end
        if gap <= max_gap_sec and abs(note.pitch - current.pitch) <= max_pitch_delta:
            merged_velocity = int(round((current.velocity + note.velocity) / 2))
            current = NoteEvent(
                pitch=int(round((current.pitch + note.pitch) / 2)),
                start=current.start,
                end=max(current.end, note.end),
                velocity=merged_velocity,
                track=current.track,
            )
        else:
            merged.append(current)
            current = note
    merged.append(current)
    return merged


def load_audio(
    path: str | Path,
    tempo_bpm: float | None = None,
    beats_per_bar: int = 4,
    min_hz: float = 82.0,
    max_hz: float = 1046.0,
    frame_size: int = 2048,
    hop_size: int = 512,
    min_note_sec: float = 0.08,
) -> MelodyData:
    suffix = Path(path).suffix.lower()
    if suffix in {".wav"}:
        samples, sample_rate = _read_wav(path)
    elif suffix in {".aif", ".aiff"}:
        samples, sample_rate = _read_aiff(path)
    else:
        raise ValueError("Unsupported audio format. Use WAV or AIFF exported from Logic.")

    if len(samples) < frame_size:
        raise ValueError("Audio is too short for pitch analysis")

    frame_count = 1 + (len(samples) - frame_size) // hop_size
    frame_rms: list[float] = []
    frame_pitch: list[float | None] = []
    frame_conf: list[float] = []
    onset_times: list[float] = []

    for frame_idx in range(frame_count):
        start = frame_idx * hop_size
        frame = samples[start : start + frame_size]
        rms = _rms(frame)
        frame_rms.append(rms)

        hz, confidence = _autocorr_pitch(frame, sample_rate, min_hz=min_hz, max_hz=max_hz)
        frame_pitch.append(hz)
        frame_conf.append(confidence)

    energy_floor = max(0.002, median(frame_rms) * 0.5)
    peak_rms = max(frame_rms) if frame_rms else 0.01

    prev_energy = frame_rms[0] if frame_rms else 0.0
    for idx in range(1, len(frame_rms)):
        growth = frame_rms[idx] - prev_energy
        if growth > max(0.01, energy_floor * 1.4) and frame_rms[idx] > energy_floor * 1.2:
            onset_times.append(idx * hop_size / sample_rate)
        prev_energy = frame_rms[idx]

    inferred_tempo = _estimate_tempo(onset_times)
    notes: list[NoteEvent] = []
    active_pitch: int | None = None
    active_start = 0.0
    active_velocity = 64
    active_last_time = 0.0

    for idx, (rms, hz, confidence) in enumerate(zip(frame_rms, frame_pitch, frame_conf)):
        current_time = idx * hop_size / sample_rate
        voiced = rms > energy_floor and hz is not None and confidence > 0.2

        if voiced:
            midi_pitch = _hz_to_midi(hz or 0.0)
            velocity = int(max(30, min(120, round((rms / max(1e-9, peak_rms)) * 95 + 25))))
            if active_pitch is None:
                active_pitch = midi_pitch
                active_start = current_time
                active_velocity = velocity
                active_last_time = current_time
            elif abs(midi_pitch - active_pitch) <= 1:
                active_pitch = int(round((active_pitch * 0.7) + (midi_pitch * 0.3)))
                active_velocity = int(round((active_velocity * 0.7) + (velocity * 0.3)))
                active_last_time = current_time
            else:
                end_time = active_last_time + (hop_size / sample_rate)
                if end_time - active_start >= min_note_sec:
                    notes.append(NoteEvent(pitch=active_pitch, start=active_start, end=end_time, velocity=active_velocity))
                active_pitch = midi_pitch
                active_start = current_time
                active_velocity = velocity
                active_last_time = current_time
        else:
            if active_pitch is not None:
                end_time = active_last_time + (hop_size / sample_rate)
                if end_time - active_start >= min_note_sec:
                    notes.append(NoteEvent(pitch=active_pitch, start=active_start, end=end_time, velocity=active_velocity))
                active_pitch = None

    if active_pitch is not None:
        end_time = active_last_time + (hop_size / sample_rate)
        if end_time - active_start >= min_note_sec:
            notes.append(NoteEvent(pitch=active_pitch, start=active_start, end=end_time, velocity=active_velocity))

    merged_notes = _merge_notes(sorted(notes, key=lambda note: note.start))
    tempo = tempo_bpm if tempo_bpm is not None else inferred_tempo

    return MelodyData(
        notes=merged_notes,
        tempo_bpm=tempo,
        beats_per_bar=beats_per_bar,
        source=str(path),
        metadata={
            "source_format": suffix.replace(".", ""),
            "sample_rate": sample_rate,
            "frame_size": frame_size,
            "hop_size": hop_size,
            "onset_count": len(onset_times),
            "estimated_tempo_bpm": round(inferred_tempo, 4),
            "transcription_engine": "autocorrelation_monophonic_v1",
        },
    )
