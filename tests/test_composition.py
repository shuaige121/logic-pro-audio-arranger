from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from melody_architect.composition import (
    build_composition_document,
    composition_to_runtime,
    load_composition,
    save_composition,
)
from melody_architect.pipeline import analyze_melody_data, load_input_file


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = PROJECT_ROOT / "examples" / "c_major_hook.csv"


class CompositionTests(unittest.TestCase):
    def test_composition_roundtrip(self) -> None:
        data = load_input_file(EXAMPLE)
        report = analyze_melody_data(data, style="pop", bars=8)
        composition = build_composition_document(data, report)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "composition.json"
            save_composition(path, composition)
            loaded = load_composition(path)

        restored_data, restored_report = composition_to_runtime(loaded)
        self.assertEqual(len(restored_data.notes), len(data.notes))
        self.assertEqual(restored_report["harmony"]["selected_candidate"]["name"], report["harmony"]["selected_candidate"]["name"])


if __name__ == "__main__":
    unittest.main()
