from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from melody_architect.pipeline import analyze_file
from melody_architect.reporting import to_markdown


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = PROJECT_ROOT / "examples" / "c_major_hook.csv"


class PipelineAndCliTests(unittest.TestCase):
    def test_pipeline_generates_expected_structure(self) -> None:
        report = analyze_file(EXAMPLE, style="pop", bars=8)

        self.assertEqual(report["key_estimate"]["tonic"], "C")
        self.assertEqual(report["harmony"]["selected_candidate"]["name"], "pop_primary")
        self.assertIn("validation", report)
        self.assertIn("metrics", report["validation"])

        md = to_markdown(report)
        self.assertIn("Melody Architecture Report", md)
        self.assertIn("Selected candidate", md)

    def test_cli_analyze_writes_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_json = Path(tmpdir) / "out.json"
            out_md = Path(tmpdir) / "out.md"
            cmd = [
                "python3",
                "-m",
                "melody_architect",
                "analyze",
                str(EXAMPLE),
                "--style",
                "pop",
                "--bars",
                "8",
                "--out-json",
                str(out_json),
                "--out-md",
                str(out_md),
            ]
            result = subprocess.run(cmd, cwd=PROJECT_ROOT, text=True, capture_output=True, check=False)

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue(out_json.exists())
            self.assertTrue(out_md.exists())

            payload = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertEqual(payload["harmony"]["selected_candidate"]["name"], "pop_primary")

    def test_cli_logic_kit_writes_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cmd = [
                "python3",
                "-m",
                "melody_architect",
                "logic-kit",
                str(EXAMPLE),
                "--style",
                "pop",
                "--bars",
                "8",
                "--complexity",
                "rich",
                "--arrangement-bars",
                "24",
                "--project-name",
                "CLI Logic Song",
                "--output-dir",
                tmpdir,
            ]
            result = subprocess.run(cmd, cwd=PROJECT_ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            bundle_dir = Path(tmpdir) / "cli-logic-song"
            self.assertTrue(bundle_dir.exists())
            self.assertTrue((bundle_dir / "logic_arrangement.mid").exists())
            self.assertTrue((bundle_dir / "analysis_report.json").exists())
            self.assertTrue((bundle_dir / "open_in_logic.command").exists())
            track_map = json.loads((bundle_dir / "logic_track_map.json").read_text(encoding="utf-8"))
            self.assertEqual(track_map["complexity"], "rich")
            self.assertEqual(track_map["arrangement_bars"], 24)

    def test_cli_digitize_writes_composition(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "composition.json"
            cmd = [
                "python3",
                "-m",
                "melody_architect",
                "digitize",
                str(EXAMPLE),
                "--style",
                "pop",
                "--bars",
                "8",
                "--out",
                str(out),
            ]
            result = subprocess.run(cmd, cwd=PROJECT_ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue(out.exists())
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema"], "melody_architect.composition")


if __name__ == "__main__":
    unittest.main()
