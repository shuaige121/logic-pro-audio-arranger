from __future__ import annotations

import math
import struct
import tempfile
import unittest
import wave
from pathlib import Path

from melody_architect.io_audio import load_audio


def _write_sine_note(handle: wave.Wave_write, hz: float, duration_sec: float, sample_rate: int, amplitude: float = 0.45) -> None:
    total = int(duration_sec * sample_rate)
    for idx in range(total):
        sample = amplitude * math.sin(2 * math.pi * hz * (idx / sample_rate))
        value = int(max(-1.0, min(1.0, sample)) * 32767)
        handle.writeframesraw(struct.pack("<h", value))


def _write_silence(handle: wave.Wave_write, duration_sec: float, sample_rate: int) -> None:
    total = int(duration_sec * sample_rate)
    for _ in range(total):
        handle.writeframesraw(struct.pack("<h", 0))


class AudioTranscriptionTests(unittest.TestCase):
    def test_wav_transcription_detects_basic_notes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            wav_path = Path(tmpdir) / "melody.wav"
            sr = 22050
            with wave.open(str(wav_path), "wb") as handle:
                handle.setnchannels(1)
                handle.setsampwidth(2)
                handle.setframerate(sr)
                _write_sine_note(handle, 261.63, 0.40, sr)  # C4
                _write_silence(handle, 0.08, sr)
                _write_sine_note(handle, 329.63, 0.40, sr)  # E4
                _write_silence(handle, 0.08, sr)
                _write_sine_note(handle, 392.00, 0.40, sr)  # G4

            data = load_audio(wav_path)

        self.assertGreaterEqual(len(data.notes), 3)
        pitches = [note.pitch for note in data.notes[:3]]
        self.assertTrue(any(abs(p - 60) <= 1 for p in pitches))
        self.assertTrue(any(abs(p - 64) <= 1 for p in pitches))
        self.assertTrue(any(abs(p - 67) <= 1 for p in pitches))


if __name__ == "__main__":
    unittest.main()
