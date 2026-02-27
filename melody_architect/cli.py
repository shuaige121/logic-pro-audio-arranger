from __future__ import annotations

import argparse
import json
from pathlib import Path

from .composition import build_composition_document, save_composition
from .logic_export import create_logic_project_bundle
from .midi_pack import generate_midi_pack
from .pipeline import analyze_file, analyze_melody_data, load_input_file
from .reporting import to_markdown


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="melody-architect",
        description="Analyze symbolic melody and generate harmony/arrangement evidence reports.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze", help="Run the full analysis pipeline")
    analyze.add_argument("input", help="Path to input file (.csv/.mid/.midi/.musicxml/.xml/.wav/.aif/.aiff)")
    analyze.add_argument("--style", default="pop", choices=["pop", "modal", "jazz"], help="Harmony style profile")
    analyze.add_argument("--bars", type=int, default=None, help="Force bar count (default: inferred)")
    analyze.add_argument("--tempo", type=float, default=None, help="Override tempo BPM")
    analyze.add_argument("--beats-per-bar", type=int, default=4, help="Meter numerator, default 4")
    analyze.add_argument(
        "--mode",
        default=None,
        choices=["major", "minor", "dorian", "mixolydian"],
        help="Override tonal mode used for roman resolution",
    )
    analyze.add_argument("--top-k", type=int, default=3, help="Number of candidates kept in report")
    analyze.add_argument("--disable-borrowed-iv", action="store_true", help="Disable pop borrowed iv candidate")
    analyze.add_argument("--disable-tritone-sub", action="store_true", help="Disable jazz tritone-sub candidate")
    analyze.add_argument("--out-json", default="analysis_report.json", help="Output JSON path")
    analyze.add_argument("--out-md", default=None, help="Optional markdown report output path")

    logic_kit = subparsers.add_parser("logic-kit", help="Generate macOS Logic Pro import kit")
    logic_kit.add_argument("input", help="Path to melody input (.wav/.aiff/.mid/.musicxml/.csv)")
    logic_kit.add_argument("--style", default="pop", choices=["pop", "modal", "jazz"], help="Arrangement style")
    logic_kit.add_argument("--bars", type=int, default=None, help="Force bar count")
    logic_kit.add_argument("--tempo", type=float, default=None, help="Override tempo BPM")
    logic_kit.add_argument("--beats-per-bar", type=int, default=4, help="Meter numerator")
    logic_kit.add_argument("--mode", default=None, choices=["major", "minor", "dorian", "mixolydian"], help="Mode override")
    logic_kit.add_argument("--project-name", default="Melody Logic Project", help="Project display name")
    logic_kit.add_argument("--output-dir", default="logic_export", help="Output directory for Logic kit")
    logic_kit.add_argument("--complexity", default="rich", choices=["basic", "rich"], help="Arrangement complexity")
    logic_kit.add_argument("--arrangement-bars", type=int, default=None, help="Final arrangement length in bars")
    logic_kit.add_argument("--no-loop-melody", action="store_true", help="Do not loop melody to fill arrangement bars")
    logic_kit.add_argument("--top-k", type=int, default=3, help="Number of harmony candidates kept in report")
    logic_kit.add_argument("--disable-borrowed-iv", action="store_true", help="Disable pop borrowed iv candidate")
    logic_kit.add_argument("--disable-tritone-sub", action="store_true", help="Disable jazz tritone-sub candidate")
    logic_kit.add_argument("--quantize-subdiv", type=int, default=4, help="Quantization subdivisions per beat (default 4)")

    digitize = subparsers.add_parser("digitize", help="Convert input to composition JSON for AI arrangement")
    digitize.add_argument("input", help="Path to melody input (.wav/.aiff/.mid/.musicxml/.csv)")
    digitize.add_argument("--style", default="pop", choices=["pop", "modal", "jazz"], help="Analysis style profile")
    digitize.add_argument("--bars", type=int, default=None, help="Force bar count")
    digitize.add_argument("--tempo", type=float, default=None, help="Override tempo BPM")
    digitize.add_argument("--beats-per-bar", type=int, default=4, help="Meter numerator")
    digitize.add_argument("--mode", default=None, choices=["major", "minor", "dorian", "mixolydian"], help="Mode override")
    digitize.add_argument("--out", default="composition.json", help="Output composition JSON path")

    midi_pack = subparsers.add_parser("midi-pack", help="Generate multiple MIDI arrangement packs")
    midi_pack.add_argument("input", help="Path to melody input")
    midi_pack.add_argument("--output-dir", default="midi_packs", help="Output directory")
    midi_pack.add_argument("--project-prefix", default="MIDI Pack", help="Project prefix")
    midi_pack.add_argument("--tempo", type=float, default=None, help="Override tempo BPM")
    midi_pack.add_argument("--beats-per-bar", type=int, default=4, help="Meter numerator")
    midi_pack.add_argument("--complexity", default="rich", choices=["basic", "rich"], help="Arrangement complexity")

    studio = subparsers.add_parser("studio", help="Run local frontend + API studio")
    studio.add_argument("--host", default="127.0.0.1", help="Host")
    studio.add_argument("--port", type=int, default=8765, help="Port")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "analyze":
        report = analyze_file(
            path=args.input,
            style=args.style,
            bars=args.bars,
            tempo_override=args.tempo,
            beats_per_bar=args.beats_per_bar,
            forced_mode=args.mode,
            include_borrowed_iv=not args.disable_borrowed_iv,
            include_tritone_sub=not args.disable_tritone_sub,
            top_k=args.top_k,
        )
        out_json = Path(args.out_json)
        out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

        if args.out_md:
            out_md = Path(args.out_md)
            out_md.write_text(to_markdown(report), encoding="utf-8")

        print(f"[ok] JSON report: {out_json}")
        if args.out_md:
            print(f"[ok] Markdown report: {args.out_md}")
        print(
            "[summary] key={tonic} {mode}, candidate={candidate}, validation={passed}".format(
                tonic=report["key_estimate"]["tonic"],
                mode=report["key_estimate"]["mode"],
                candidate=report["harmony"]["selected_candidate"]["name"],
                passed=report["validation"]["passed"],
            )
        )
        return 0

    if args.command == "logic-kit":
        data = load_input_file(args.input, tempo_override=args.tempo, beats_per_bar=args.beats_per_bar)
        report = analyze_melody_data(
            data=data,
            style=args.style,
            bars=args.bars,
            forced_mode=args.mode,
            include_borrowed_iv=not args.disable_borrowed_iv,
            include_tritone_sub=not args.disable_tritone_sub,
            top_k=args.top_k,
        )
        bundle = create_logic_project_bundle(
            data=data,
            report=report,
            output_dir=args.output_dir,
            project_name=args.project_name,
            quantize_subdivisions=max(1, args.quantize_subdiv),
            complexity=args.complexity,
            arrangement_bars=args.arrangement_bars,
            loop_melody=not args.no_loop_melody,
        )

        print(f"[ok] Logic kit created: {bundle['bundle_dir']}")
        print(f"[ok] MIDI arrangement: {bundle['midi']}")
        print(f"[ok] mac launcher: {bundle['logic_launcher']}")
        print(
            "[summary] key={tonic} {mode}, candidate={candidate}, validation={passed}".format(
                tonic=report["key_estimate"]["tonic"],
                mode=report["key_estimate"]["mode"],
                candidate=report["harmony"]["selected_candidate"]["name"],
                passed=report["validation"]["passed"],
            )
        )
        return 0

    if args.command == "digitize":
        data = load_input_file(args.input, tempo_override=args.tempo, beats_per_bar=args.beats_per_bar)
        report = analyze_melody_data(
            data=data,
            style=args.style,
            bars=args.bars,
            forced_mode=args.mode,
            top_k=5,
        )
        composition = build_composition_document(data, report)
        out = Path(args.out)
        save_composition(out, composition)
        print(f"[ok] Composition JSON: {out}")
        print(
            "[summary] key={tonic} {mode}, candidate={candidate}, notes={notes}".format(
                tonic=report["key_estimate"]["tonic"],
                mode=report["key_estimate"]["mode"],
                candidate=report["harmony"]["selected_candidate"]["name"],
                notes=report["input"]["note_count"],
            )
        )
        return 0

    if args.command == "midi-pack":
        bundles = generate_midi_pack(
            input_path=args.input,
            output_dir=args.output_dir,
            project_prefix=args.project_prefix,
            tempo_override=args.tempo,
            beats_per_bar=args.beats_per_bar,
            complexity=args.complexity,
        )
        print(f"[ok] Generated {len(bundles)} bundles in {args.output_dir}")
        return 0

    if args.command == "studio":
        import uvicorn

        print(f"[ok] Studio running on http://{args.host}:{args.port}")
        uvicorn.run("melody_architect.webapp:app", host=args.host, port=args.port, reload=False)
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
