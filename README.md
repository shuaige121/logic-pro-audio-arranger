# Melody Architecture Lab

Audio-to-Logic Pro arrangement toolkit: import melody audio/MIDI, analyze tonality, generate harmony + arrangement tracks, and export a macOS Logic-ready project kit.

## What It Does

- Input formats:
  - `WAV / AIFF` (automatic monophonic melody transcription)
  - `MIDI / MusicXML / CSV` (symbolic analysis)
- Analysis:
  - key estimation, phrase summary, harmony candidate ranking (`pop / modal / jazz`)
- Output:
  - JSON evidence report
  - Markdown report
  - Logic import kit (multi-track MIDI + macOS launcher scripts)

This project targets real workflows like:
- `logic pro audio to midi`
- `automatic arrangement for Logic Pro`
- `melody harmonization and orchestration planning`

## Quick Start

```bash
cd /home/leonard/melody-architecture-lab
python3 -m melody_architect analyze examples/c_major_hook.csv --style pop --out-json out.json --out-md out.md
```

Generate Logic kit directly:

```bash
python3 -m melody_architect logic-kit examples/c_major_hook.csv \
  --style pop \
  --complexity rich \
  --arrangement-bars 32 \
  --project-name "Demo Song" \
  --output-dir ./logic_export
```

## How To Convert Audio To Logic Pro Project

```bash
python3 -m melody_architect logic-kit INPUT.wav \
  --style pop \
  --complexity rich \
  --arrangement-bars 64 \
  --project-name "My Song" \
  --output-dir ./logic_export
```

Then run `open_in_logic.command` in the output folder on macOS.

## CLI Commands

### `analyze`

```bash
python3 -m melody_architect analyze INPUT --style pop --out-json report.json --out-md report.md
```

`INPUT` supports `.csv/.mid/.midi/.musicxml/.xml/.wav/.aif/.aiff`.

### `logic-kit`

```bash
python3 -m melody_architect logic-kit INPUT.wav \
  --style pop \
  --complexity rich \
  --arrangement-bars 32 \
  --project-name "My Song" \
  --output-dir ./logic_export
```

Output bundle includes:

- `logic_arrangement.mid`
- `analysis_report.json`
- `analysis_report.md`
- `logic_track_map.json`
- `open_in_logic.command` (macOS)
- `create_logic_project.applescript` (macOS)

For denser productions:
- use `--complexity rich` for extra instruments (sub bass, arp, strings, counter melody, rhythm guitar, percussion)
- use `--arrangement-bars 32` or `64` for longer form
- default behavior loops melody motif to fill target length (disable via `--no-loop-melody`)

## Can It Create `.logicx` Automatically?

Not by directly writing Logic's private project format.

Current behavior:
- auto-generates a Logic-ready arrangement MIDI and opens Logic Pro via script
- then prompts you to save as `.logicx`

This avoids reverse-engineering proprietary `.logicx` internals while keeping workflow near one-click.

## Input Notes

### CSV columns

- required: `pitch` or `pitch_midi`
- required: `start` or `start_sec`
- required: `end` or `end_sec`
- optional: `velocity`

### MusicXML

- supports uncompressed `.musicxml/.xml`
- `.mxl` should be re-exported as uncompressed XML first

### Audio transcription scope

- optimized for monophonic melody sources (vocal lead, solo instrument, top line)
- best quality from clean stems exported from Logic

## macOS App Packaging

Build GUI app on macOS:

```bash
cd /home/leonard/melody-architecture-lab
./scripts/build_macos_app.sh
```

Artifacts:

- `dist/macos/MelodyLogicBuilder.app`
- `dist/macos/open_terminal_cli.command`

## GUI

Launch local GUI:

```bash
python3 -m melody_architect.gui
```

## Testing

Run full test suite:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

## SEO and Launch Assets

- SEO checklist: `docs/SEO.md`
- basic landing metadata:
  - `site/index.html`
  - `site/robots.txt`
  - `site/sitemap.xml`
