#!/usr/bin/env python3
"""Generate deterministic music-theory data and write to knowledge.db."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from init_db import DB_PATH, init_db

NOTES_SHARP = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
ENHARMONIC_ALIAS = {"C#": "Db", "D#": "Eb", "F#": "Gb", "G#": "Ab", "A#": "Bb"}
SOURCE_TAG = "generated:knowledge/gen_theory_data.py"


def intervals_to_str(intervals: list[int]) -> str:
    return ",".join(str(i) for i in intervals)


def note_list_for(root: str, intervals: list[int]) -> str:
    root_index = NOTES_SHARP.index(root)
    notes = [NOTES_SHARP[(root_index + interval) % 12] for interval in intervals]
    return ",".join(notes)


def root_aliases(root: str) -> str:
    alias = ENHARMONIC_ALIAS.get(root)
    return alias if alias else ""


def generate_scales_modes() -> list[dict[str, str]]:
    scales: list[dict[str, str]] = []

    family_specs = [
        (
            "Major",
            "major",
            [0, 2, 4, 5, 7, 9, 11],
            "Ionian major scale formula used for tonal harmony.",
        ),
        (
            "Natural Minor",
            "natural_minor",
            [0, 2, 3, 5, 7, 8, 10],
            "Aeolian natural minor formula with lowered 3rd, 6th, and 7th.",
        ),
        (
            "Harmonic Minor",
            "harmonic_minor",
            [0, 2, 3, 5, 7, 8, 11],
            "Minor scale with raised 7th to create dominant pull.",
        ),
        (
            "Melodic Minor",
            "melodic_minor",
            [0, 2, 3, 5, 7, 9, 11],
            "Jazz melodic minor ascending form with raised 6th and 7th.",
        ),
    ]

    for root in NOTES_SHARP:
        root_alt = root_aliases(root)
        for scale_name, category, intervals, description in family_specs:
            aliases = []
            if root_alt:
                aliases.append(f"{root_alt} {scale_name}")
            if scale_name == "Major":
                aliases.append(f"{root} Ionian")
            if scale_name == "Natural Minor":
                aliases.append(f"{root} Aeolian")
            scales.append(
                {
                    "name": f"{root} {scale_name}",
                    "aliases": ",".join(aliases),
                    "intervals": intervals_to_str(intervals),
                    "notes_from_c": note_list_for(root, intervals),
                    "category": category,
                    "description": description,
                }
            )

    c_mode_specs = [
        (
            "C Ionian",
            "major mode",
            [0, 2, 4, 5, 7, 9, 11],
            "mode",
            "Church mode I; same interval structure as major scale.",
        ),
        (
            "C Dorian",
            "minor mode",
            [0, 2, 3, 5, 7, 9, 10],
            "mode",
            "Church mode II; minor with natural 6.",
        ),
        (
            "C Phrygian",
            "minor mode",
            [0, 1, 3, 5, 7, 8, 10],
            "mode",
            "Church mode III; minor with flat 2.",
        ),
        (
            "C Lydian",
            "major mode",
            [0, 2, 4, 6, 7, 9, 11],
            "mode",
            "Church mode IV; major with sharp 4.",
        ),
        (
            "C Mixolydian",
            "dominant mode",
            [0, 2, 4, 5, 7, 9, 10],
            "mode",
            "Church mode V; major with flat 7.",
        ),
        (
            "C Aeolian",
            "natural minor mode",
            [0, 2, 3, 5, 7, 8, 10],
            "mode",
            "Church mode VI; same structure as natural minor.",
        ),
        (
            "C Locrian",
            "diminished mode",
            [0, 1, 3, 5, 6, 8, 10],
            "mode",
            "Church mode VII; minor with flat 2 and flat 5.",
        ),
    ]

    for name, aliases, intervals, category, description in c_mode_specs:
        scales.append(
            {
                "name": name,
                "aliases": aliases,
                "intervals": intervals_to_str(intervals),
                "notes_from_c": note_list_for("C", intervals),
                "category": category,
                "description": description,
            }
        )

    common_specs = [
        (
            "C Blues Scale",
            "minor blues",
            [0, 3, 5, 6, 7, 10],
            "blues",
            "Hexatonic blues scale with chromatic blue note.",
        ),
        (
            "C Pentatonic Major",
            "major pentatonic",
            [0, 2, 4, 7, 9],
            "pentatonic",
            "Five-note major pentatonic scale.",
        ),
        (
            "C Pentatonic Minor",
            "minor pentatonic",
            [0, 3, 5, 7, 10],
            "pentatonic",
            "Five-note minor pentatonic scale.",
        ),
        (
            "C Whole Tone",
            "augmented scale",
            [0, 2, 4, 6, 8, 10],
            "symmetric",
            "Symmetric whole-step collection used for augmented color.",
        ),
        (
            "C Diminished Half-Whole",
            "octatonic HW",
            [0, 1, 3, 4, 6, 7, 9, 10],
            "symmetric",
            "Octatonic scale alternating half-step then whole-step.",
        ),
        (
            "C Diminished Whole-Half",
            "octatonic WH",
            [0, 2, 3, 5, 6, 8, 9, 11],
            "symmetric",
            "Octatonic scale alternating whole-step then half-step.",
        ),
        (
            "C Chromatic",
            "12-tone chromatic",
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
            "chromatic",
            "All 12 pitch classes in semitone steps.",
        ),
        (
            "C Bebop Dominant",
            "mixolydian bebop",
            [0, 2, 4, 5, 7, 9, 10, 11],
            "bebop",
            "Dominant bebop scale with added major 7 passing tone.",
        ),
        (
            "C Bebop Major",
            "major bebop",
            [0, 2, 4, 5, 7, 8, 9, 11],
            "bebop",
            "Major bebop scale with added flat 6 passing tone.",
        ),
        (
            "C Hungarian Minor",
            "gypsy minor",
            [0, 2, 3, 6, 7, 8, 11],
            "exotic",
            "Minor scale with raised 4 and raised 7.",
        ),
        (
            "C Double Harmonic",
            "Byzantine,Arabic",
            [0, 1, 4, 5, 7, 8, 11],
            "exotic",
            "Scale with two augmented-second gaps for dramatic color.",
        ),
        (
            "C Phrygian Dominant",
            "Spanish gypsy",
            [0, 1, 4, 5, 7, 8, 10],
            "exotic",
            "5th mode of harmonic minor with major 3 and flat 2.",
        ),
    ]

    for name, aliases, intervals, category, description in common_specs:
        scales.append(
            {
                "name": name,
                "aliases": aliases,
                "intervals": intervals_to_str(intervals),
                "notes_from_c": note_list_for("C", intervals),
                "category": category,
                "description": description,
            }
        )

    return scales


def generate_chord_types() -> list[dict[str, str]]:
    chord_specs = [
        ("major", "", [0, 4, 7], "triad", "Major triad."),
        ("minor", "m", [0, 3, 7], "triad", "Minor triad."),
        ("diminished", "dim", [0, 3, 6], "triad", "Diminished triad."),
        ("augmented", "aug", [0, 4, 8], "triad", "Augmented triad."),
        ("sus2", "sus2", [0, 2, 7], "triad", "Suspended triad with major second."),
        ("sus4", "sus4", [0, 5, 7], "triad", "Suspended triad with perfect fourth."),
        ("dom7", "7", [0, 4, 7, 10], "seventh", "Dominant seventh chord."),
        ("maj7", "maj7", [0, 4, 7, 11], "seventh", "Major seventh chord."),
        ("min7", "m7", [0, 3, 7, 10], "seventh", "Minor seventh chord."),
        ("min(maj7)", "m(maj7)", [0, 3, 7, 11], "seventh", "Minor-major seventh chord."),
        ("dim7", "dim7", [0, 3, 6, 9], "seventh", "Fully diminished seventh chord."),
        ("half-dim7(m7b5)", "m7b5", [0, 3, 6, 10], "seventh", "Half-diminished seventh chord."),
        ("aug7", "7#5", [0, 4, 8, 10], "seventh", "Dominant seventh with augmented fifth."),
        ("augmaj7", "maj7#5", [0, 4, 8, 11], "seventh", "Major seventh with augmented fifth."),
        ("6", "6", [0, 4, 7, 9], "sixth", "Major sixth chord."),
        ("min6", "m6", [0, 3, 7, 9], "sixth", "Minor sixth chord."),
        ("9", "9", [0, 4, 7, 10, 14], "ninth", "Dominant ninth chord."),
        ("maj9", "maj9", [0, 4, 7, 11, 14], "ninth", "Major ninth chord."),
        ("min9", "m9", [0, 3, 7, 10, 14], "ninth", "Minor ninth chord."),
        ("add9", "add9", [0, 4, 7, 14], "ninth", "Major triad with added ninth."),
        ("11", "11", [0, 4, 7, 10, 14, 17], "eleventh", "Dominant eleventh chord."),
        ("min11", "m11", [0, 3, 7, 10, 14, 17], "eleventh", "Minor eleventh chord."),
        ("13", "13", [0, 4, 7, 10, 14, 17, 21], "thirteenth", "Dominant thirteenth chord."),
        ("maj13", "maj13", [0, 4, 7, 11, 14, 17, 21], "thirteenth", "Major thirteenth chord."),
        ("min13", "m13", [0, 3, 7, 10, 14, 17, 21], "thirteenth", "Minor thirteenth chord."),
        ("7#5", "7#5", [0, 4, 8, 10], "altered", "Dominant seventh with sharp five."),
        ("7b5", "7b5", [0, 4, 6, 10], "altered", "Dominant seventh with flat five."),
        ("7#9", "7#9", [0, 4, 7, 10, 15], "altered", "Dominant seventh with sharp nine."),
        ("7b9", "7b9", [0, 4, 7, 10, 13], "altered", "Dominant seventh with flat nine."),
        ("7#11", "7#11", [0, 4, 7, 10, 18], "altered", "Dominant seventh with sharp eleven."),
        ("5", "5", [0, 7], "power", "Power chord (root and fifth)."),
        ("6/9", "6/9", [0, 4, 7, 9, 14], "extended", "Major sixth chord with added ninth."),
        ("min6/9", "m6/9", [0, 3, 7, 9, 14], "extended", "Minor sixth chord with added ninth."),
        ("7sus4", "7sus4", [0, 5, 7, 10], "suspended", "Dominant seventh with suspended fourth."),
        ("9sus4", "9sus4", [0, 5, 7, 10, 14], "suspended", "Dominant ninth with suspended fourth."),
        ("maj7#11", "maj7#11", [0, 4, 7, 11, 18], "extended", "Major seventh chord with sharp eleven."),
        ("add11", "add11", [0, 4, 7, 17], "added-tone", "Major triad with added eleventh."),
        ("minadd9", "madd9", [0, 3, 7, 14], "added-tone", "Minor triad with added ninth."),
        ("7b13", "7b13", [0, 4, 7, 10, 20], "altered", "Dominant seventh with flat thirteen."),
        ("7alt", "7alt", [0, 4, 7, 10, 13, 15], "altered", "Dominant altered shell including b9 and #9."),
    ]

    return [
        {
            "name": name,
            "symbol": symbol,
            "intervals": intervals_to_str(intervals),
            "category": category,
            "description": description,
        }
        for name, symbol, intervals, category, description in chord_specs
    ]


GM_INSTRUMENT_NAMES = [
    "Acoustic Grand Piano",
    "Bright Acoustic Piano",
    "Electric Grand Piano",
    "Honky-tonk Piano",
    "Electric Piano 1",
    "Electric Piano 2",
    "Harpsichord",
    "Clavinet",
    "Celesta",
    "Glockenspiel",
    "Music Box",
    "Vibraphone",
    "Marimba",
    "Xylophone",
    "Tubular Bells",
    "Dulcimer",
    "Drawbar Organ",
    "Percussive Organ",
    "Rock Organ",
    "Church Organ",
    "Reed Organ",
    "Accordion",
    "Harmonica",
    "Tango Accordion",
    "Acoustic Guitar (nylon)",
    "Acoustic Guitar (steel)",
    "Electric Guitar (jazz)",
    "Electric Guitar (clean)",
    "Electric Guitar (muted)",
    "Overdriven Guitar",
    "Distortion Guitar",
    "Guitar Harmonics",
    "Acoustic Bass",
    "Electric Bass (finger)",
    "Electric Bass (pick)",
    "Fretless Bass",
    "Slap Bass 1",
    "Slap Bass 2",
    "Synth Bass 1",
    "Synth Bass 2",
    "Violin",
    "Viola",
    "Cello",
    "Contrabass",
    "Tremolo Strings",
    "Pizzicato Strings",
    "Orchestral Harp",
    "Timpani",
    "String Ensemble 1",
    "String Ensemble 2",
    "Synth Strings 1",
    "Synth Strings 2",
    "Choir Aahs",
    "Voice Oohs",
    "Synth Voice",
    "Orchestra Hit",
    "Trumpet",
    "Trombone",
    "Tuba",
    "Muted Trumpet",
    "French Horn",
    "Brass Section",
    "Synth Brass 1",
    "Synth Brass 2",
    "Soprano Sax",
    "Alto Sax",
    "Tenor Sax",
    "Baritone Sax",
    "Oboe",
    "English Horn",
    "Bassoon",
    "Clarinet",
    "Piccolo",
    "Flute",
    "Recorder",
    "Pan Flute",
    "Blown Bottle",
    "Shakuhachi",
    "Whistle",
    "Ocarina",
    "Lead 1 (square)",
    "Lead 2 (sawtooth)",
    "Lead 3 (calliope)",
    "Lead 4 (chiff)",
    "Lead 5 (charang)",
    "Lead 6 (voice)",
    "Lead 7 (fifths)",
    "Lead 8 (bass + lead)",
    "Pad 1 (new age)",
    "Pad 2 (warm)",
    "Pad 3 (polysynth)",
    "Pad 4 (choir)",
    "Pad 5 (bowed)",
    "Pad 6 (metallic)",
    "Pad 7 (halo)",
    "Pad 8 (sweep)",
    "FX 1 (rain)",
    "FX 2 (soundtrack)",
    "FX 3 (crystal)",
    "FX 4 (atmosphere)",
    "FX 5 (brightness)",
    "FX 6 (goblins)",
    "FX 7 (echoes)",
    "FX 8 (sci-fi)",
    "Sitar",
    "Banjo",
    "Shamisen",
    "Koto",
    "Kalimba",
    "Bag pipe",
    "Fiddle",
    "Shanai",
    "Tinkle Bell",
    "Agogo",
    "Steel Drums",
    "Woodblock",
    "Taiko Drum",
    "Melodic Tom",
    "Synth Drum",
    "Reverse Cymbal",
    "Guitar Fret Noise",
    "Breath Noise",
    "Seashore",
    "Bird Tweet",
    "Telephone Ring",
    "Helicopter",
    "Applause",
    "Gunshot",
]

GM_FAMILIES = [
    "Piano",
    "Chromatic Percussion",
    "Organ",
    "Guitar",
    "Bass",
    "Strings",
    "Ensemble",
    "Brass",
    "Reed",
    "Pipe",
    "Synth Lead",
    "Synth Pad",
    "Synth Effects",
    "Ethnic",
    "Percussive",
    "Sound Effects",
]

FAMILY_PROFILES = {
    "Piano": ("A0", "C8", "C3-C6", "classical,jazz,pop,ballad", "harmony,melody"),
    "Chromatic Percussion": (
        "C3",
        "C8",
        "C4-C6",
        "film,jazz,ambient,children",
        "color,counter-melody",
    ),
    "Organ": ("C2", "C6", "C3-C5", "gospel,rock,jazz,church", "harmony,pad"),
    "Guitar": ("E2", "E6", "A2-D5", "rock,pop,jazz,folk", "rhythm,lead"),
    "Bass": ("B0", "C5", "E1-G3", "funk,rock,pop,jazz", "bassline,groove"),
    "Strings": ("C2", "A7", "G3-E6", "orchestral,film,pop", "melody,harmony"),
    "Ensemble": ("C2", "C7", "C3-G5", "cinematic,pop,ambient", "pad,texture"),
    "Brass": ("E1", "C6", "G2-C5", "jazz,film,latin,rock", "stabs,melody"),
    "Reed": ("Bb1", "F6", "D3-C5", "jazz,folk,classical", "melody,riffs"),
    "Pipe": ("C4", "C7", "D4-A5", "folk,new-age,classical", "melody,ornament"),
    "Synth Lead": ("C1", "C7", "C3-C6", "edm,synthwave,pop", "lead,hook"),
    "Synth Pad": ("C1", "C7", "C2-C5", "ambient,edm,film", "pad,atmosphere"),
    "Synth Effects": ("C1", "C7", "C3-C6", "soundtrack,game,fx", "texture,transitions"),
    "Ethnic": ("C2", "C7", "C3-C5", "world,film,fusion", "melody,color"),
    "Percussive": ("C1", "C6", "C2-C4", "latin,world,score", "rhythm,accents"),
    "Sound Effects": ("C1", "C7", "C3-C5", "fx,game,film", "one-shots,transitions"),
}

PROGRAM_OVERRIDES = {
    40: ("G3", "A7", "D4-E6"),
    41: ("C3", "E6", "G3-C5"),
    42: ("C2", "C6", "G2-A4"),
    43: ("E1", "E5", "A1-D3"),
    46: ("C1", "G7", "C3-C6"),
    47: ("D2", "A3", "F2-F3"),
    56: ("F#3", "D6", "A3-A5"),
    57: ("E2", "Bb4", "A2-F4"),
    58: ("D1", "F4", "A1-C4"),
    60: ("B1", "F5", "F2-C5"),
    64: ("Ab3", "E6", "C4-C6"),
    65: ("Db3", "Ab5", "G3-F5"),
    66: ("Ab2", "E5", "C3-C5"),
    67: ("C2", "C5", "G2-G4"),
    68: ("Bb3", "A6", "C4-G5"),
    69: ("E3", "C6", "A3-G5"),
    70: ("Bb1", "E5", "C2-C4"),
    71: ("D3", "A6", "G3-E5"),
    72: ("D5", "C8", "G5-G7"),
    73: ("C4", "D7", "E4-A6"),
    109: ("A3", "A5", "D4-F5"),
    110: ("G3", "E7", "A3-D6"),
}

DRUM_NOTE_MAP = {
    35: "Acoustic Bass Drum",
    36: "Bass Drum 1",
    37: "Side Stick",
    38: "Acoustic Snare",
    39: "Hand Clap",
    40: "Electric Snare",
    41: "Low Floor Tom",
    42: "Closed Hi-Hat",
    43: "High Floor Tom",
    44: "Pedal Hi-Hat",
    45: "Low Tom",
    46: "Open Hi-Hat",
    47: "Low-Mid Tom",
    48: "Hi-Mid Tom",
    49: "Crash Cymbal 1",
    50: "High Tom",
    51: "Ride Cymbal 1",
    52: "Chinese Cymbal",
    53: "Ride Bell",
    54: "Tambourine",
    55: "Splash Cymbal",
    56: "Cowbell",
    57: "Crash Cymbal 2",
    58: "Vibraslap",
    59: "Ride Cymbal 2",
    60: "Hi Bongo",
    61: "Low Bongo",
    62: "Mute Hi Conga",
    63: "Open Hi Conga",
    64: "Low Conga",
    65: "High Timbale",
    66: "Low Timbale",
    67: "High Agogo",
    68: "Low Agogo",
    69: "Cabasa",
    70: "Maracas",
    71: "Short Whistle",
    72: "Long Whistle",
    73: "Short Guiro",
    74: "Long Guiro",
    75: "Claves",
    76: "Hi Wood Block",
    77: "Low Wood Block",
    78: "Mute Cuica",
    79: "Open Cuica",
    80: "Mute Triangle",
    81: "Open Triangle",
}


def generate_instrumentation() -> list[dict[str, str | int]]:
    instruments: list[dict[str, str | int]] = []

    for program, name in enumerate(GM_INSTRUMENT_NAMES):
        family = GM_FAMILIES[program // 8]
        range_low, range_high, sweet_spot, styles, role = FAMILY_PROFILES[family]

        if program in PROGRAM_OVERRIDES:
            o_low, o_high, o_spot = PROGRAM_OVERRIDES[program]
            range_low, range_high, sweet_spot = o_low, o_high, o_spot

        instruments.append(
            {
                "name": name,
                "gm_program": program,
                "family": family,
                "range_low": range_low,
                "range_high": range_high,
                "sweet_spot": sweet_spot,
                "styles": styles,
                "role": role,
                "description": (
                    f"GM program {program} in {family}; typical use: {role} for {styles}."
                ),
            }
        )

    drum_summary = "; ".join(f"{note}:{drum}" for note, drum in sorted(DRUM_NOTE_MAP.items()))
    instruments.append(
        {
            "name": "GM Drum Map (Channel 10)",
            "gm_program": -1,
            "family": "Percussive",
            "range_low": "B1",
            "range_high": "A5",
            "sweet_spot": "C2-C4",
            "styles": "all styles,drum programming,midi",
            "role": "rhythm,groove,accents",
            "description": f"General MIDI channel 10 percussion mapping: {drum_summary}",
        }
    )

    return instruments


def write_data(db_path: Path) -> None:
    scales = generate_scales_modes()
    chords = generate_chord_types()
    instruments = generate_instrumentation()

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    cursor.execute("DELETE FROM scales_modes")
    cursor.execute("DELETE FROM chord_types")
    cursor.execute("DELETE FROM instrumentation")

    cursor.executemany(
        """
        INSERT INTO scales_modes (
            name, aliases, intervals, notes_from_c, category, description, source
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                row["name"],
                row["aliases"],
                row["intervals"],
                row["notes_from_c"],
                row["category"],
                row["description"],
                SOURCE_TAG,
            )
            for row in scales
        ],
    )

    cursor.executemany(
        """
        INSERT INTO chord_types (
            name, symbol, intervals, category, description, source
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (
                row["name"],
                row["symbol"],
                row["intervals"],
                row["category"],
                row["description"],
                SOURCE_TAG,
            )
            for row in chords
        ],
    )

    cursor.executemany(
        """
        INSERT INTO instrumentation (
            name, gm_program, family, range_low, range_high, sweet_spot,
            styles, role, description, source
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                row["name"],
                row["gm_program"],
                row["family"],
                row["range_low"],
                row["range_high"],
                row["sweet_spot"],
                row["styles"],
                row["role"],
                row["description"],
                SOURCE_TAG,
            )
            for row in instruments
        ],
    )

    conn.commit()

    table_counts = {}
    for table in ("scales_modes", "chord_types", "instrumentation"):
        table_counts[table] = cursor.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

    conn.close()

    print(f"scales_modes: {table_counts['scales_modes']}")
    print(f"chord_types: {table_counts['chord_types']}")
    print(f"instrumentation: {table_counts['instrumentation']}")


def main() -> None:
    init_db(DB_PATH)
    write_data(DB_PATH)


if __name__ == "__main__":
    main()
