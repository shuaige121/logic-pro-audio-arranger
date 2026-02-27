from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from melody_architect.midi_pack import generate_midi_pack


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = PROJECT_ROOT / "examples" / "c_major_hook.csv"


class MidiPackTests(unittest.TestCase):
    def test_generate_midi_pack_minimal(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            bundles = generate_midi_pack(
                input_path=EXAMPLE,
                output_dir=tmpdir,
                project_prefix="TestPack",
                styles=("pop",),
                arrangement_bars=(8,),
                complexity="basic",
            )
            self.assertEqual(len(bundles), 1)
            bundle = bundles[0]
            self.assertTrue(Path(bundle["midi"]).exists())
            self.assertTrue(Path(bundle["report_json"]).exists())


if __name__ == "__main__":
    unittest.main()
