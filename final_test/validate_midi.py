#!/usr/bin/env python3
from __future__ import annotations

import csv
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pretty_midi

BASE_DIR = Path(__file__).resolve().parent
INPUT_CSV = Path("examples/c_major_hook.csv")
LEVELS = ("conservative", "balanced", "creative")
BARS_MAP = {"conservative": "16", "balanced": "32", "creative": "64"}
STYLE_MAP = {"conservative": "pop", "balanced": "pop", "creative": "jazz"}
COMPLEXITY_MAP = {"conservative": "basic", "balanced": "rich", "creative": "rich"}


@dataclass
class TrackInfo:
    index: int
    name: str
    notes: int
    bytes_len: int


@dataclass
class MidiValidationResult:
    level: str
    path: Path
    exists: bool = False
    non_empty: bool = False
    valid_magic: bool = False
    parse_ok: bool = False
    copied_from: Path | None = None
    error: str | None = None
    file_size: int = 0
    midi_format: int | None = None
    num_tracks_header: int | None = None
    division: int | None = None
    tracks: list[TrackInfo] = field(default_factory=list)

    @property
    def total_notes(self) -> int:
        return sum(track.notes for track in self.tracks)

    @property
    def num_tracks(self) -> int:
        return len(self.tracks)

    @property
    def has_multiple_tracks(self) -> bool:
        return self.num_tracks >= 3

    @property
    def passed(self) -> bool:
        return (
            self.exists
            and self.non_empty
            and self.valid_magic
            and self.parse_ok
            and self.has_multiple_tracks
        )


def parse_midi_basic(path: Path) -> dict:
    """Parse a MIDI file using pretty-midi and return structured info."""
    pm = pretty_midi.PrettyMIDI(str(path))
    file_size = path.stat().st_size

    tracks: list[TrackInfo] = []
    for idx, inst in enumerate(pm.instruments):
        tracks.append(
            TrackInfo(
                index=idx + 1,
                name=inst.name or f"track_{idx + 1}",
                notes=len(inst.notes),
                bytes_len=0,  # not meaningful with pretty-midi, kept for compat
            )
        )

    # pretty-midi doesn't directly expose format/division, but we can read
    # the raw header for those fields if needed for the report
    data = path.read_bytes()
    midi_format = 1
    division = 480
    num_tracks_raw = len(pm.instruments)
    if len(data) >= 14 and data[:4] == b"MThd":
        import struct
        midi_format = struct.unpack(">H", data[8:10])[0]
        num_tracks_raw = struct.unpack(">H", data[10:12])[0]
        division = struct.unpack(">H", data[12:14])[0]

    return {
        "format": midi_format,
        "num_tracks": num_tracks_raw,
        "division": division,
        "file_size": file_size,
        "tracks": tracks,
    }


def resolve_midi_path(level: str) -> tuple[Path, Path | None]:
    output_path = BASE_DIR / f"output_{level}.mid"
    if output_path.exists() and output_path.stat().st_size > 0:
        return output_path, None

    fallback_path = BASE_DIR / level / "logic_arrangement.mid"
    if fallback_path.exists() and fallback_path.stat().st_size > 0:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(fallback_path, output_path)
        return output_path, fallback_path

    return output_path, None


def validate_level(level: str) -> MidiValidationResult:
    output_path, copied_from = resolve_midi_path(level)
    result = MidiValidationResult(level=level, path=output_path, copied_from=copied_from)

    result.exists = output_path.exists()
    if not result.exists:
        result.error = (
            f"missing final_test/output_{level}.mid and final_test/{level}/logic_arrangement.mid"
        )
        return result

    result.file_size = output_path.stat().st_size
    result.non_empty = result.file_size > 0
    if not result.non_empty:
        result.error = "file is empty"
        return result

    with output_path.open("rb") as midi_file:
        result.valid_magic = midi_file.read(4) == b"MThd"
    if not result.valid_magic:
        result.error = "invalid MIDI magic bytes (expected MThd)"
        return result

    try:
        parsed = parse_midi_basic(output_path)
    except Exception as exc:  # pragma: no cover - defensive path
        result.error = f"parse failed: {exc}"
        return result

    result.parse_ok = True
    result.midi_format = parsed["format"]
    result.num_tracks_header = parsed["num_tracks"]
    result.division = parsed["division"]
    result.tracks = parsed["tracks"]

    if not result.has_multiple_tracks:
        result.error = f"track count too low: {result.num_tracks} (<3 expected)"

    return result


def count_input_notes(csv_path: Path) -> int:
    if not csv_path.exists():
        return 0

    with csv_path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.reader(file)
        _ = next(reader, None)
        return sum(1 for _ in reader)


def metric_file_size(result: MidiValidationResult) -> str:
    if not result.exists:
        return "N/A"
    return f"{result.file_size} bytes"


def metric_tracks(result: MidiValidationResult) -> str:
    if not result.parse_ok:
        return "N/A"
    return str(result.num_tracks)


def metric_notes(result: MidiValidationResult) -> str:
    if not result.parse_ok:
        return "N/A"
    return str(result.total_notes)


def summarize_level_diff(result: MidiValidationResult) -> str:
    level_label = result.level.capitalize()
    if not result.parse_ok:
        return f"{level_label}: 未完成验证（{result.error or '未知错误'}）。"

    densest_track = max(result.tracks, key=lambda track: track.notes, default=None)
    if densest_track:
        densest = f"主导轨道 {densest_track.name}({densest_track.notes} notes)"
    else:
        densest = "未解析到有效音符轨"

    copy_hint = ""
    if result.copied_from is not None:
        copy_hint = f"，由 {result.copied_from} 自动复制"

    return (
        f"{level_label}: 轨道 {result.num_tracks}，总音符 {result.total_notes}，"
        f"{densest}{copy_hint}。"
    )


def build_track_section(result: MidiValidationResult) -> str:
    title = result.level.capitalize()
    status = "✅ 通过" if result.passed else "❌ 失败"

    lines = [f"### {title}", f"- 路径: {result.path}", f"- 状态: {status}"]
    if result.copied_from is not None:
        lines.append(f"- 来源: 自动复制自 {result.copied_from}")
    if result.error:
        lines.append(f"- 错误: {result.error}")

    if not result.tracks:
        lines.append("- 轨道详情: 无")
        lines.append("")
        return "\n".join(lines)

    lines.extend(
        [
            "",
            "| 轨道序号 | 轨道名 | 音符数 | 字节数 |",
            "|---------|--------|--------|--------|",
        ]
    )
    for track in result.tracks:
        lines.append(
            f"| {track.index} | {track.name or '-'} | {track.notes} | {track.bytes_len} |"
        )
    lines.append("")
    return "\n".join(lines)


def write_report(results: list[MidiValidationResult]) -> Path:
    by_level = {result.level: result for result in results}
    input_notes = count_input_notes(INPUT_CSV)

    conservative = by_level["conservative"]
    balanced = by_level["balanced"]
    creative = by_level["creative"]

    all_passed = all(result.passed for result in results)
    conclusion = "✅ 验证通过" if all_passed else "❌ 验证失败"

    report_lines = [
        "# 编曲测试验证报告",
        "",
        "## 输入",
        "- 文件: examples/c_major_hook.csv",
        "- 调性: C major",
        "- 速度: 120 BPM",
        f"- 音符数: {input_notes}",
        "",
        "## MIDI 输出对比",
        "",
        "| 指标 | Conservative | Balanced | Creative |",
        "|------|-------------|----------|----------|",
        f"| 文件大小 | {metric_file_size(conservative)} | {metric_file_size(balanced)} | {metric_file_size(creative)} |",
        f"| 轨道数 | {metric_tracks(conservative)} | {metric_tracks(balanced)} | {metric_tracks(creative)} |",
        f"| 总音符数 | {metric_notes(conservative)} | {metric_notes(balanced)} | {metric_notes(creative)} |",
        f"| 编曲小节 | {BARS_MAP['conservative']} | {BARS_MAP['balanced']} | {BARS_MAP['creative']} |",
        f"| 风格 | {STYLE_MAP['conservative']} | {STYLE_MAP['balanced']} | {STYLE_MAP['creative']} |",
        f"| 复杂度 | {COMPLEXITY_MAP['conservative']} | {COMPLEXITY_MAP['balanced']} | {COMPLEXITY_MAP['creative']} |",
        "",
        "## 轨道详情",
        "",
        build_track_section(conservative),
        build_track_section(balanced),
        build_track_section(creative),
        "## 档位差异分析",
        f"- {summarize_level_diff(conservative)}",
        f"- {summarize_level_diff(balanced)}",
        f"- {summarize_level_diff(creative)}",
        "",
        "## 结论",
        conclusion,
        "",
    ]

    report_path = BASE_DIR / "test_report.md"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")
    return report_path


def main() -> int:
    results = [validate_level(level) for level in LEVELS]
    report_path = write_report(results)

    print(f"[INFO] 测试报告已生成: {report_path}")
    for result in results:
        state = "PASS" if result.passed else "FAIL"
        print(
            f"[{state}] {result.level}: "
            f"exists={result.exists}, non_empty={result.non_empty}, "
            f"magic={result.valid_magic}, tracks={result.num_tracks}, notes={result.total_notes}"
        )
        if result.error:
            print(f"  -> {result.error}")

    return 0 if all(result.passed for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
