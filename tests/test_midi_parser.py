from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from melody_architect.io_midi import load_midi


def encode_varlen(value: int) -> bytes:
    buffer = [value & 0x7F]
    value >>= 7
    while value:
        buffer.append((value & 0x7F) | 0x80)
        value >>= 7
    return bytes(reversed(buffer))


def build_simple_midi() -> bytes:
    ticks_per_beat = 480
    events = bytearray()

    # Tempo 120 BPM
    events += encode_varlen(0) + bytes([0xFF, 0x51, 0x03, 0x07, 0xA1, 0x20])
    # Note C4 on/off
    events += encode_varlen(0) + bytes([0x90, 60, 90])
    events += encode_varlen(480) + bytes([0x80, 60, 0])
    # Note E4 on/off
    events += encode_varlen(0) + bytes([0x90, 64, 80])
    events += encode_varlen(480) + bytes([0x80, 64, 0])
    # End of track
    events += encode_varlen(0) + bytes([0xFF, 0x2F, 0x00])

    header = b"MThd" + (6).to_bytes(4, "big") + (0).to_bytes(2, "big") + (1).to_bytes(2, "big") + ticks_per_beat.to_bytes(2, "big")
    track = b"MTrk" + len(events).to_bytes(4, "big") + bytes(events)
    return header + track


class MidiParserTests(unittest.TestCase):
    def test_load_simple_midi(self) -> None:
        data = build_simple_midi()
        with tempfile.TemporaryDirectory() as tmpdir:
            midi_path = Path(tmpdir) / "simple.mid"
            midi_path.write_bytes(data)

            parsed = load_midi(midi_path)

        self.assertEqual(len(parsed.notes), 2)
        self.assertAlmostEqual(parsed.tempo_bpm, 120.0, places=3)
        self.assertAlmostEqual(parsed.notes[0].start, 0.0, places=4)
        self.assertAlmostEqual(parsed.notes[0].end, 0.5, places=4)
        self.assertAlmostEqual(parsed.notes[1].start, 0.5, places=4)
        self.assertAlmostEqual(parsed.notes[1].end, 1.0, places=4)


if __name__ == "__main__":
    unittest.main()
