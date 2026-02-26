from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from melody_architect.io_midi import load_midi
from melody_architect.logic_export import create_logic_project_bundle
from melody_architect.pipeline import analyze_melody_data, load_input_file


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = PROJECT_ROOT / "examples" / "c_major_hook.csv"


class LogicExportTests(unittest.TestCase):
    def test_create_logic_project_bundle(self) -> None:
        data = load_input_file(EXAMPLE)
        report = analyze_melody_data(data, style="pop", bars=8)

        with tempfile.TemporaryDirectory() as tmpdir:
            bundle = create_logic_project_bundle(
                data=data,
                report=report,
                output_dir=tmpdir,
                project_name="Unit Test Song",
            )
            bundle_dir = Path(bundle["bundle_dir"])

            self.assertTrue(bundle_dir.exists())
            self.assertTrue(Path(bundle["midi"]).exists())
            self.assertTrue(Path(bundle["logic_launcher"]).exists())
            self.assertTrue((bundle_dir / "analysis_report.json").exists())

            payload = json.loads((bundle_dir / "logic_track_map.json").read_text(encoding="utf-8"))
            self.assertIn("tracks", payload)
            self.assertGreaterEqual(len(payload["tracks"]), 4)

            midi_data = load_midi(bundle["midi"])
            self.assertGreater(len(midi_data.notes), len(data.notes))
            track_names = {note.track for note in midi_data.notes}
            self.assertTrue(any(name and "Lead Melody" in name for name in track_names))
            self.assertTrue(any(name and "Bass" in name for name in track_names))
            self.assertTrue(any(name and "Harmony" in name for name in track_names))


if __name__ == "__main__":
    unittest.main()
