from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from .models import MelodyData, NoteEvent

STEP_TO_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def _local(tag: str) -> str:
    return tag.split("}", 1)[-1]


def _child_text(node: ET.Element, local_name: str) -> str | None:
    for child in node:
        if _local(child.tag) == local_name and child.text is not None:
            return child.text.strip()
    return None


def _has_child(node: ET.Element, local_name: str) -> bool:
    return any(_local(child.tag) == local_name for child in node)


def _find_child(node: ET.Element, local_name: str) -> ET.Element | None:
    for child in node:
        if _local(child.tag) == local_name:
            return child
    return None


def _pitch_to_midi(pitch_node: ET.Element) -> int:
    step = _child_text(pitch_node, "step")
    octave_text = _child_text(pitch_node, "octave")
    alter_text = _child_text(pitch_node, "alter")
    if step is None or octave_text is None:
        raise ValueError("Pitch node missing step or octave")
    alter = int(alter_text) if alter_text is not None else 0
    octave = int(octave_text)
    return (octave + 1) * 12 + STEP_TO_PC[step] + alter


def load_musicxml(path: str | Path, default_tempo: float = 120.0) -> MelodyData:
    source = str(path)
    suffix = Path(path).suffix.lower()
    if suffix == ".mxl":
        raise ValueError("Compressed .mxl is not supported yet; please export uncompressed .musicxml/.xml.")

    tree = ET.parse(path)
    root = tree.getroot()

    parts = [node for node in root if _local(node.tag) == "part"]
    if not parts:
        raise ValueError("No <part> found in MusicXML")

    part = parts[0]
    notes: list[NoteEvent] = []
    tempo = default_tempo
    divisions = 1.0
    beats_per_bar = 4
    beat_unit = 4
    current_time_sec = 0.0
    last_note_start_sec = 0.0

    for measure in part:
        if _local(measure.tag) != "measure":
            continue
        for item in measure:
            tag = _local(item.tag)

            if tag == "attributes":
                divisions_text = _child_text(item, "divisions")
                if divisions_text is not None:
                    divisions = max(1.0, float(divisions_text))

                time_node = _find_child(item, "time")
                if time_node is not None:
                    beats_text = _child_text(time_node, "beats")
                    beat_type_text = _child_text(time_node, "beat-type")
                    if beats_text is not None and beat_type_text is not None:
                        beats_per_bar = int(beats_text)
                        beat_unit = int(beat_type_text)

            elif tag == "direction":
                sound_node = _find_child(item, "sound")
                if sound_node is not None:
                    tempo_attr = sound_node.attrib.get("tempo")
                    if tempo_attr:
                        tempo = float(tempo_attr)

            elif tag in ("backup", "forward"):
                duration_text = _child_text(item, "duration")
                if duration_text is None:
                    continue
                duration_div = float(duration_text)
                duration_sec = duration_div / divisions * (60.0 / tempo)
                if tag == "backup":
                    current_time_sec = max(0.0, current_time_sec - duration_sec)
                else:
                    current_time_sec += duration_sec

            elif tag == "note":
                duration_text = _child_text(item, "duration")
                duration_div = float(duration_text) if duration_text is not None else 0.0
                duration_sec = duration_div / divisions * (60.0 / tempo)
                is_chord_note = _has_child(item, "chord")
                is_rest = _has_child(item, "rest")

                if is_chord_note:
                    start_sec = last_note_start_sec
                else:
                    start_sec = current_time_sec
                    last_note_start_sec = start_sec

                if not is_rest:
                    pitch_node = _find_child(item, "pitch")
                    if pitch_node is not None:
                        pitch = _pitch_to_midi(pitch_node)
                        velocity_text = _child_text(item, "velocity")
                        velocity = int(velocity_text) if velocity_text else 64
                        notes.append(
                            NoteEvent(
                                pitch=pitch,
                                start=start_sec,
                                end=start_sec + duration_sec,
                                velocity=velocity,
                            )
                        )

                if not is_chord_note:
                    current_time_sec += duration_sec

    return MelodyData(
        notes=sorted(notes, key=lambda n: (n.start, n.pitch, n.end)),
        tempo_bpm=tempo,
        beats_per_bar=beats_per_bar,
        beat_unit=beat_unit,
        source=source,
        metadata={"parts": len(parts)},
    )
