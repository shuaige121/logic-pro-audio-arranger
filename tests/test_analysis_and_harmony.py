from __future__ import annotations

import unittest

from melody_architect.analysis import estimate_key
from melody_architect.harmony import generate_harmony_candidates
from melody_architect.models import NoteEvent


class AnalysisHarmonyTests(unittest.TestCase):
    def test_estimate_key_c_major(self) -> None:
        notes = [
            NoteEvent(pitch=60, start=0.0, end=0.5),
            NoteEvent(pitch=62, start=0.5, end=1.0),
            NoteEvent(pitch=64, start=1.0, end=1.5),
            NoteEvent(pitch=65, start=1.5, end=2.0),
            NoteEvent(pitch=67, start=2.0, end=2.5),
            NoteEvent(pitch=69, start=2.5, end=3.0),
            NoteEvent(pitch=71, start=3.0, end=3.5),
            NoteEvent(pitch=72, start=3.5, end=4.0),
        ]
        key = estimate_key(notes)
        self.assertEqual(key.tonic_name, "C")
        self.assertEqual(key.mode, "major")

    def test_pop_primary_selected_for_c_major_hook(self) -> None:
        notes = [
            NoteEvent(pitch=60, start=0.0, end=0.5),
            NoteEvent(pitch=64, start=0.5, end=1.0),
            NoteEvent(pitch=67, start=2.0, end=2.5),
            NoteEvent(pitch=71, start=2.5, end=3.0),
            NoteEvent(pitch=69, start=4.0, end=4.5),
            NoteEvent(pitch=72, start=4.5, end=5.0),
            NoteEvent(pitch=65, start=6.0, end=6.5),
            NoteEvent(pitch=69, start=6.5, end=7.0),
        ]
        candidates = generate_harmony_candidates(
            notes=notes,
            tonic_pc=0,
            detected_mode="major",
            style="pop",
            bar_count=4,
            beats_per_bar=4,
            tempo_bpm=120.0,
        )
        self.assertEqual(candidates[0].name, "pop_primary")
        self.assertEqual([ch.symbol for ch in candidates[0].bars], ["C", "G", "Am", "F"])

    def test_mode_override_is_applied(self) -> None:
        notes = [
            NoteEvent(pitch=57, start=0.0, end=0.5),
            NoteEvent(pitch=60, start=0.5, end=1.0),
            NoteEvent(pitch=64, start=1.0, end=1.5),
            NoteEvent(pitch=65, start=1.5, end=2.0),
        ]
        candidates = generate_harmony_candidates(
            notes=notes,
            tonic_pc=9,  # A
            detected_mode="major",
            style="pop",
            bar_count=4,
            beats_per_bar=4,
            tempo_bpm=120.0,
            mode_override="minor",
        )
        self.assertTrue(all(candidate.mode == "minor" for candidate in candidates))


if __name__ == "__main__":
    unittest.main()
