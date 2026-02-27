from __future__ import annotations

from pathlib import Path

from .logic_export import create_logic_project_bundle
from .pipeline import analyze_melody_data, load_input_file


def generate_midi_pack(
    input_path: str | Path,
    output_dir: str | Path,
    project_prefix: str = "MIDI Pack",
    styles: tuple[str, ...] = ("pop", "modal", "jazz"),
    arrangement_bars: tuple[int, ...] = (32, 64),
    tempo_override: float | None = None,
    beats_per_bar: int = 4,
    complexity: str = "rich",
) -> list[dict[str, str]]:
    bundles: list[dict[str, str]] = []
    data = load_input_file(input_path, tempo_override=tempo_override, beats_per_bar=beats_per_bar)

    for style in styles:
        report = analyze_melody_data(
            data=data,
            style=style,
            bars=None,
            top_k=3,
        )
        for bars in arrangement_bars:
            bundle = create_logic_project_bundle(
                data=data,
                report=report,
                output_dir=output_dir,
                project_name=f"{project_prefix} {style} {bars} bars",
                quantize_subdivisions=4,
                complexity=complexity,
                arrangement_bars=bars,
                loop_melody=True,
            )
            bundles.append(bundle)
    return bundles
