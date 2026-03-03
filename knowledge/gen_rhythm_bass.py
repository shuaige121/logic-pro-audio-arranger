#!/usr/bin/env python3
"""Generate drum rhythm and bass pattern knowledge with Brave search enrichment."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Any

try:
    from knowledge.brave_search import batch_search, search
    from knowledge.init_db import DB_PATH, init_db
except ModuleNotFoundError:
    import sys

    ROOT = Path(__file__).resolve().parent.parent
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from knowledge.brave_search import batch_search, search
    from knowledge.init_db import DB_PATH, init_db


STEPS = 16
DB_FILE = Path(DB_PATH)
WORKER = "codex-3"


def bits(bit_string: str) -> list[int]:
    cleaned = "".join(ch for ch in bit_string if ch in "01")
    if len(cleaned) != STEPS:
        raise ValueError(f"Pattern must be {STEPS} bits, got {len(cleaned)}: {bit_string}")
    return [int(ch) for ch in cleaned]


def rotate(values: list[int], n: int) -> list[int]:
    if not values:
        return values
    n = n % len(values)
    if n == 0:
        return values[:]
    return values[-n:] + values[:-n]


def stable_seed(text: str) -> int:
    return int(hashlib.sha1(text.encode("utf-8")).hexdigest()[:8], 16)


def validate_binary_sequence(values: list[int]) -> list[int]:
    if len(values) != STEPS:
        raise ValueError(f"Binary sequence must be {STEPS} steps, got {len(values)}")
    if any(v not in (0, 1) for v in values):
        raise ValueError(f"Binary sequence must only contain 0/1: {values}")
    return values


def validate_interval_sequence(values: list[int]) -> list[int]:
    if len(values) != STEPS:
        raise ValueError(f"Interval sequence must be {STEPS} steps, got {len(values)}")
    for v in values:
        if not isinstance(v, int):
            raise ValueError(f"Interval must be int: {values}")
        if v != -1 and not (-24 <= v <= 24):
            raise ValueError(f"Interval out of range: {values}")
    return values


def rhythm_payload(kick: list[int], snare: list[int], hihat: list[int]) -> str:
    payload = {
        "steps": STEPS,
        "kick": validate_binary_sequence(kick),
        "snare": validate_binary_sequence(snare),
        "hihat": validate_binary_sequence(hihat),
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def bass_payload(intervals: list[int]) -> str:
    payload = {
        "steps": STEPS,
        "intervals": validate_interval_sequence(intervals),
        "note": "intervals relative to chord root, -1 = rest",
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def make_rhythm(
    name: str,
    style: str,
    kick: list[int],
    snare: list[int],
    hihat: list[int],
    description: str,
    time_signature: str = "4/4",
    bpm_range: str = "80-140",
    source: str = "classic_rhythm_reference",
) -> dict[str, Any]:
    return {
        "name": name,
        "style": style,
        "instrument": "drums",
        "time_signature": time_signature,
        "bpm_range": bpm_range,
        "pattern_data": rhythm_payload(kick, snare, hihat),
        "description": description,
        "source": source,
    }


def make_bass(
    name: str,
    style: str,
    pattern_type: str,
    intervals: list[int],
    description: str,
    source: str = "classic_bass_reference",
) -> dict[str, Any]:
    return {
        "name": name,
        "style": style,
        "pattern_type": pattern_type,
        "pattern_data": bass_payload(intervals),
        "description": description,
        "source": source,
    }


RHYTHM_HARDCODED = [
    make_rhythm(
        "pop_basic_4_4",
        "pop",
        bits("1000000010000000"),
        bits("0000100000001000"),
        bits("1010101010101010"),
        "Standard 4/4 pop beat with backbeat on 2 and 4.",
        bpm_range="95-125",
    ),
    make_rhythm(
        "pop_driving",
        "pop",
        bits("1000010010100010"),
        bits("0000100000001000"),
        bits("1010101010101010"),
        "Driving pop groove with extra syncopated kicks.",
        bpm_range="110-140",
    ),
    make_rhythm(
        "rock_basic",
        "rock",
        bits("1000001010100000"),
        bits("0000100000001000"),
        bits("1010101010101010"),
        "Basic rock groove for medium tempo songs.",
        bpm_range="100-145",
    ),
    make_rhythm(
        "rock_half_time",
        "rock",
        bits("1000000010100000"),
        bits("0000000000001000"),
        bits("1010101010101010"),
        "Half-time rock feel with snare on beat 3.",
        bpm_range="75-105",
    ),
    make_rhythm(
        "rock_double_kick",
        "rock",
        bits("1010001010100010"),
        bits("0000100000001000"),
        bits("1010101010101010"),
        "Rock groove using double-kick accents.",
        bpm_range="130-180",
    ),
    make_rhythm(
        "jazz_swing",
        "jazz",
        bits("1000001000100000"),
        bits("0000100000001010"),
        bits("1001100110011001"),
        "Swing ride approximation in 16-step quantization.",
        bpm_range="120-220",
    ),
    make_rhythm(
        "jazz_bossa",
        "jazz",
        bits("1001000010100000"),
        bits("0000100000101000"),
        bits("1010101010101010"),
        "Jazz bossa groove with light syncopation.",
        bpm_range="110-160",
    ),
    make_rhythm(
        "jazz_waltz_3_4",
        "jazz",
        bits("1000010000100000"),
        bits("0001000010000100"),
        bits("1011010110101101"),
        "Jazz waltz phrasing mapped into 16-step grid.",
        time_signature="3/4",
        bpm_range="110-180",
    ),
    make_rhythm(
        "funk_basic",
        "funk",
        bits("1001001010100000"),
        bits("0000100000001000"),
        bits("1110111011101110"),
        "Pocket-oriented funk groove with 16th-note hats.",
        bpm_range="95-120",
    ),
    make_rhythm(
        "funk_syncopated",
        "funk",
        bits("1010010100100010"),
        bits("0000100000001000"),
        bits("1111011101110111"),
        "Syncopated funk groove with anticipations.",
        bpm_range="95-120",
    ),
    make_rhythm(
        "rnb_trap_influenced",
        "rnb",
        bits("1000000101010010"),
        bits("0000100000001000"),
        bits("1111110111111011"),
        "R&B groove influenced by trap hi-hat density.",
        bpm_range="120-150",
    ),
    make_rhythm(
        "rnb_neo_soul",
        "rnb",
        bits("1000001010010010"),
        bits("0000100000001000"),
        bits("1010111010101110"),
        "Loose neo-soul drum pocket with broken hats.",
        bpm_range="70-95",
    ),
    make_rhythm(
        "edm_four_on_floor",
        "edm",
        bits("1000100010001000"),
        bits("0000100000001000"),
        bits("0010001000100010"),
        "Four-on-the-floor EDM groove.",
        bpm_range="120-132",
    ),
    make_rhythm(
        "edm_breakbeat",
        "edm",
        bits("1100001010010000"),
        bits("0000100000001000"),
        bits("1110111011101110"),
        "EDM breakbeat with chopped kick placement.",
        bpm_range="125-145",
    ),
    make_rhythm(
        "edm_dnb",
        "edm",
        bits("1000000001100000"),
        bits("0000100000001000"),
        bits("1111111111111111"),
        "Drum-and-bass inspired two-step kick-snare shape.",
        bpm_range="160-176",
    ),
    make_rhythm(
        "edm_dubstep_half",
        "edm",
        bits("1000000010100000"),
        bits("0000000000001000"),
        bits("1111011111110111"),
        "Half-time dubstep groove.",
        bpm_range="138-150",
    ),
    make_rhythm(
        "latin_bossa_nova",
        "latin",
        bits("1001000010010000"),
        bits("0000100000101000"),
        bits("1010101010101010"),
        "Bossa nova drumset adaptation.",
        bpm_range="110-140",
    ),
    make_rhythm(
        "latin_samba",
        "latin",
        bits("1010001010100010"),
        bits("0000100000001000"),
        bits("1111111111111111"),
        "Samba-inspired driving 16th-note groove.",
        bpm_range="96-130",
    ),
    make_rhythm(
        "latin_reggaeton",
        "latin",
        bits("1001000010100000"),
        bits("0000100100001001"),
        bits("1010101010101010"),
        "Reggaeton dembow skeleton.",
        bpm_range="86-102",
    ),
    make_rhythm(
        "latin_salsa",
        "latin",
        bits("1000010010000100"),
        bits("0001001000100010"),
        bits("1011101010111010"),
        "Salsa-influenced drum kit orchestration.",
        bpm_range="150-220",
    ),
    make_rhythm(
        "blues_shuffle",
        "blues",
        bits("1000001010000010"),
        bits("0000100000001000"),
        bits("1001100110011001"),
        "Medium shuffle for blues progressions.",
        bpm_range="90-130",
    ),
    make_rhythm(
        "blues_slow",
        "blues",
        bits("1000000010000000"),
        bits("0000100000001000"),
        bits("1000100010001000"),
        "Slow blues pocket with sparse hats.",
        bpm_range="55-80",
    ),
    make_rhythm(
        "folk_fingerpick",
        "folk",
        bits("1000000010000000"),
        bits("0000100000001000"),
        bits("1010001010100010"),
        "Simple folk-oriented groove for fingerpicking songs.",
        bpm_range="70-105",
    ),
    make_rhythm(
        "folk_waltz",
        "folk",
        bits("1000010000100000"),
        bits("0001000010000100"),
        bits("1001001001001001"),
        "Folk waltz mapped to 16-step resolution.",
        time_signature="3/4",
        bpm_range="85-130",
    ),
    make_rhythm(
        "country_train_beat",
        "country",
        bits("1000000010000000"),
        bits("0000101000001010"),
        bits("1010101010101010"),
        "Train beat snare chatter in country style.",
        bpm_range="120-165",
    ),
    make_rhythm(
        "country_boom_chick",
        "country",
        bits("1000000010000000"),
        bits("0000100000001000"),
        bits("1000100010001000"),
        "Classic boom-chick feel.",
        bpm_range="90-130",
    ),
    make_rhythm(
        "hiphop_boom_bap",
        "hiphop",
        bits("1000001000100000"),
        bits("0000100000001000"),
        bits("1010111010101110"),
        "Boom bap groove with humanized hat spacing.",
        bpm_range="82-98",
    ),
    make_rhythm(
        "hiphop_trap",
        "hiphop",
        bits("1000000100110010"),
        bits("0000100000001000"),
        bits("1111110111111011"),
        "Trap-style drum skeleton with rolling hats.",
        bpm_range="130-155",
    ),
]


BASS_HARDCODED = [
    make_bass(
        "pop_root_fifth",
        "pop",
        "groove",
        [0, -1, 7, -1, 0, -1, 7, -1, 0, -1, 7, -1, 0, -1, 7, -1],
        "Alternating root and fifth support line.",
    ),
    make_bass(
        "rock_eighth_note",
        "rock",
        "pedal",
        [0, 0, -1, 0, 0, -1, 0, 0, 7, 7, -1, 7, 0, 0, -1, 0],
        "Rock eighth-note pedal with occasional fifth.",
    ),
    make_bass(
        "jazz_walking",
        "jazz",
        "walking",
        [0, 2, 4, 5, 7, 6, 5, 4, 3, 2, 1, 0, -1, -1, -1, -1],
        "Walking bass contour with scalar motion.",
    ),
    make_bass(
        "jazz_bossa_bass",
        "jazz",
        "latin",
        [0, -1, 5, -1, 7, -1, 5, -1, 0, -1, 5, -1, 7, -1, 5, -1],
        "Bossa-style two-feel root and fifth movement.",
    ),
    make_bass(
        "jazz_swing_bass",
        "jazz",
        "walking",
        [0, -1, 3, -1, 5, -1, 6, -1, 7, -1, 6, -1, 5, -1, 3, -1],
        "Swing bass with chord-tone targeting.",
    ),
    make_bass(
        "funk_slap",
        "funk",
        "slap",
        [0, -1, 7, 0, -1, 10, -1, 7, 0, -1, 5, -1, 7, -1, 10, -1],
        "Slap-oriented syncopated funk figure.",
    ),
    make_bass(
        "funk_syncopated",
        "funk",
        "groove",
        [0, -1, -1, 7, 0, -1, 5, -1, 7, -1, -1, 10, 7, -1, 5, -1],
        "Syncopated funk rhythm with ghost spaces.",
    ),
    make_bass(
        "rnb_smooth",
        "rnb",
        "subtle",
        [0, -1, -1, 7, -1, 5, -1, -1, 0, -1, -1, 4, -1, 5, -1, -1],
        "Smooth R&B supportive line with long rests.",
    ),
    make_bass(
        "rnb_sub_bass",
        "rnb",
        "sub",
        [0, -1, -1, -1, 0, -1, -1, -1, 7, -1, -1, -1, 5, -1, -1, -1],
        "Low-frequency sustained sub movement.",
    ),
    make_bass(
        "edm_sidechain",
        "edm",
        "sub",
        [0, -1, -1, -1, 0, -1, -1, -1, 0, -1, -1, -1, 0, -1, -1, -1],
        "Quarter-note EDM sub pulse for sidechain pumping.",
    ),
    make_bass(
        "edm_arpeggiated",
        "edm",
        "arpeggio",
        [0, 4, 7, 12, 7, 4, 0, -1, 0, 4, 7, 12, 7, 4, 0, -1],
        "Arpeggiated dance bass figure.",
    ),
    make_bass(
        "latin_tumbao",
        "latin",
        "tumbao",
        [0, -1, 5, -1, -1, 7, -1, 5, 0, -1, 5, -1, -1, 7, -1, 5],
        "Tumbao-like syncopated latin bass pulse.",
    ),
    make_bass(
        "latin_bossa_bass",
        "latin",
        "groove",
        [0, -1, 7, -1, 5, -1, 7, -1, 0, -1, 7, -1, 5, -1, 7, -1],
        "Bossa root-fifth alternation.",
    ),
    make_bass(
        "blues_shuffle_bass",
        "blues",
        "shuffle",
        [0, -1, 0, -1, 3, -1, 3, -1, 5, -1, 5, -1, 6, -1, 6, -1],
        "Shuffle bass emphasizing blues chord tones.",
    ),
    make_bass(
        "blues_walking",
        "blues",
        "walking",
        [0, 3, 5, 6, 7, 6, 5, 3, 0, 2, 4, 5, 6, 5, 4, 2],
        "12-bar compatible walking bass cell.",
    ),
    make_bass(
        "country_root_five",
        "country",
        "boom_chick",
        [0, -1, 7, -1, 0, -1, 7, -1, 5, -1, 7, -1, 0, -1, 7, -1],
        "Country root-five alternation pattern.",
    ),
    make_bass(
        "folk_simple",
        "folk",
        "pedal",
        [0, -1, -1, -1, 5, -1, -1, -1, 7, -1, -1, -1, 5, -1, -1, -1],
        "Sparse folk support bass.",
    ),
    make_bass(
        "reggae_offbeat",
        "reggae",
        "offbeat",
        [-1, 0, -1, 0, -1, 5, -1, 5, -1, 0, -1, 0, -1, 5, -1, 5],
        "Reggae offbeat low-end punctuation.",
    ),
    make_bass(
        "disco_octave",
        "disco",
        "octave",
        [0, 12, -1, 12, 0, 12, -1, 12, 0, 12, -1, 12, 0, 12, -1, 12],
        "Disco octave pulse for dance floor momentum.",
    ),
    make_bass(
        "hiphop_808_glide",
        "hiphop",
        "808",
        [0, -1, -1, 0, -2, -1, -1, -1, -5, -1, -1, -1, -7, -1, -1, -1],
        "808-style descending glide-ready intervals.",
    ),
]


RHYTHM_TEMPLATES = {
    "straight_backbeat": {
        "kick": bits("1000000010000000"),
        "snare": bits("0000100000001000"),
        "hihat": bits("1010101010101010"),
    },
    "syncopated_backbeat": {
        "kick": bits("1010010100100010"),
        "snare": bits("0000100000001000"),
        "hihat": bits("1111011101110111"),
    },
    "four_on_floor": {
        "kick": bits("1000100010001000"),
        "snare": bits("0000100000001000"),
        "hihat": bits("0010001000100010"),
    },
    "breakbeat": {
        "kick": bits("1100001010010000"),
        "snare": bits("0000100000001000"),
        "hihat": bits("1110111011101110"),
    },
    "halftime": {
        "kick": bits("1000000010100000"),
        "snare": bits("0000000000001000"),
        "hihat": bits("1111011111110111"),
    },
    "shuffle": {
        "kick": bits("1000001010000010"),
        "snare": bits("0000100000001000"),
        "hihat": bits("1001100110011001"),
    },
    "dembow": {
        "kick": bits("1001000010100000"),
        "snare": bits("0000100100001001"),
        "hihat": bits("1010101010101010"),
    },
    "waltz": {
        "kick": bits("1000010000100000"),
        "snare": bits("0001000010000100"),
        "hihat": bits("1001001001001001"),
    },
    "double_kick": {
        "kick": bits("1010001010100010"),
        "snare": bits("0000100000001000"),
        "hihat": bits("1110111011101110"),
    },
    "offbeat_hat": {
        "kick": bits("1000010010000010"),
        "snare": bits("0000100000001000"),
        "hihat": bits("0010001000100010"),
    },
}


BASS_TEMPLATES = {
    "root_fifth": [0, -1, 7, -1, 0, -1, 7, -1, 0, -1, 7, -1, 0, -1, 7, -1],
    "octave_pulse": [0, 12, -1, 12, 0, 12, -1, 12, 0, 12, -1, 12, 0, 12, -1, 12],
    "pedal_drive": [0, 0, -1, 0, 0, -1, 0, 0, 0, -1, 0, 0, -1, 0, 0, -1],
    "sub_808": [0, -1, -1, 0, -2, -1, -1, -1, -5, -1, -1, -1, -7, -1, -1, -1],
    "offbeat_reggae": [-1, 0, -1, 0, -1, 5, -1, 5, -1, 0, -1, 0, -1, 5, -1, 5],
    "arp_minor": [0, 3, 7, 10, 7, 3, 0, -1, 0, 3, 7, 10, 7, 3, 0, -1],
    "syncopated_root": [0, -1, 7, 0, -1, 5, -1, 7, 0, -1, 4, -1, 7, -1, 5, -1],
    "latin_tumbao": [0, -1, 5, -1, -1, 7, -1, 5, 0, -1, 5, -1, -1, 7, -1, 5],
    "gallop": [0, 0, -1, 0, 0, -1, 0, 0, -1, 0, 0, -1, 7, 7, -1, 7],
}


RHYTHM_SEARCH_SPECS = [
    {
        "style": "afrobeat",
        "query": "drum pattern afrobeat beat programming",
        "template": "syncopated_backbeat",
        "time_signature": "4/4",
        "bpm_range": "90-115",
    },
    {
        "style": "afro_cuban",
        "query": "afro cuban drum rhythm notation",
        "template": "offbeat_hat",
        "time_signature": "4/4",
        "bpm_range": "95-130",
    },
    {
        "style": "house_deep",
        "query": "deep house drum pattern beat programming",
        "template": "four_on_floor",
        "time_signature": "4/4",
        "bpm_range": "118-124",
    },
    {
        "style": "uk_garage",
        "query": "uk garage drum pattern 2 step beat",
        "template": "breakbeat",
        "time_signature": "4/4",
        "bpm_range": "128-136",
    },
    {
        "style": "jungle",
        "query": "jungle drum and bass breakbeat pattern",
        "template": "breakbeat",
        "time_signature": "4/4",
        "bpm_range": "160-174",
    },
    {
        "style": "lofi_hiphop",
        "query": "lofi hip hop drum groove pattern",
        "template": "straight_backbeat",
        "time_signature": "4/4",
        "bpm_range": "70-90",
    },
    {
        "style": "trap_metal",
        "query": "trap metal drum pattern tutorial",
        "template": "halftime",
        "time_signature": "4/4",
        "bpm_range": "130-155",
    },
    {
        "style": "synthwave",
        "query": "synthwave drum machine pattern",
        "template": "straight_backbeat",
        "time_signature": "4/4",
        "bpm_range": "90-118",
    },
    {
        "style": "disco_modern",
        "query": "disco drum pattern four on floor hi hat",
        "template": "four_on_floor",
        "time_signature": "4/4",
        "bpm_range": "110-128",
    },
    {
        "style": "techno",
        "query": "techno beat programming drum pattern",
        "template": "four_on_floor",
        "time_signature": "4/4",
        "bpm_range": "124-138",
    },
    {
        "style": "amapiano",
        "query": "amapiano drum pattern log drum groove",
        "template": "offbeat_hat",
        "time_signature": "4/4",
        "bpm_range": "108-114",
    },
    {
        "style": "baile_funk",
        "query": "baile funk drum pattern tamborzão",
        "template": "syncopated_backbeat",
        "time_signature": "4/4",
        "bpm_range": "120-135",
    },
    {
        "style": "dancehall",
        "query": "dancehall drum pattern one drop groove",
        "template": "halftime",
        "time_signature": "4/4",
        "bpm_range": "90-110",
    },
    {
        "style": "drill",
        "query": "drill drum pattern hi hat snare placement",
        "template": "halftime",
        "time_signature": "4/4",
        "bpm_range": "130-150",
    },
    {
        "style": "jersey_club",
        "query": "jersey club drum pattern kick triplets",
        "template": "breakbeat",
        "time_signature": "4/4",
        "bpm_range": "130-140",
    },
    {
        "style": "new_jack_swing",
        "query": "new jack swing drum pattern",
        "template": "syncopated_backbeat",
        "time_signature": "4/4",
        "bpm_range": "95-115",
    },
    {
        "style": "phonk",
        "query": "phonk cowbell drum pattern",
        "template": "syncopated_backbeat",
        "time_signature": "4/4",
        "bpm_range": "130-150",
    },
    {
        "style": "metalcore",
        "query": "metalcore double kick drum pattern",
        "template": "double_kick",
        "time_signature": "4/4",
        "bpm_range": "140-190",
    },
]


BASS_SEARCH_SPECS = [
    {
        "style": "afrobeat",
        "query": "afrobeat bass line pattern groove",
        "template": "syncopated_root",
        "pattern_type": "groove",
    },
    {
        "style": "house",
        "query": "house music bassline pattern root octave",
        "template": "octave_pulse",
        "pattern_type": "dance",
    },
    {
        "style": "techno",
        "query": "techno bass groove pattern",
        "template": "pedal_drive",
        "pattern_type": "ostinato",
    },
    {
        "style": "drum_and_bass",
        "query": "drum and bass reese bass pattern",
        "template": "sub_808",
        "pattern_type": "sub",
    },
    {
        "style": "dub_reggae",
        "query": "dub reggae bass guitar line pattern",
        "template": "offbeat_reggae",
        "pattern_type": "offbeat",
    },
    {
        "style": "disco",
        "query": "disco bassline octave pattern",
        "template": "octave_pulse",
        "pattern_type": "octave",
    },
    {
        "style": "synthwave",
        "query": "synthwave bass arpeggio pattern",
        "template": "arp_minor",
        "pattern_type": "arpeggio",
    },
    {
        "style": "amapiano",
        "query": "amapiano log drum bass pattern",
        "template": "syncopated_root",
        "pattern_type": "groove",
    },
    {
        "style": "drill_808",
        "query": "drill 808 bass pattern intervals",
        "template": "sub_808",
        "pattern_type": "808",
    },
    {
        "style": "salsa",
        "query": "salsa bass tumbao pattern",
        "template": "latin_tumbao",
        "pattern_type": "tumbao",
    },
    {
        "style": "funk_fingerstyle",
        "query": "funk bass guitar groove syncopated pattern",
        "template": "syncopated_root",
        "pattern_type": "funk",
    },
    {
        "style": "metal_gallop",
        "query": "metal bass gallop rhythm pattern",
        "template": "gallop",
        "pattern_type": "gallop",
    },
]


def build_rhythm_from_template(template: str, style_tag: str) -> tuple[list[int], list[int], list[int]]:
    seed = stable_seed(style_tag)
    base = RHYTHM_TEMPLATES[template]

    kick = rotate(base["kick"], seed % 4)
    snare = base["snare"][:]
    hihat = rotate(base["hihat"], ((seed // 5) % 2) * 2)

    if template in {"straight_backbeat", "syncopated_backbeat", "breakbeat", "four_on_floor", "offbeat_hat", "double_kick"}:
        snare[4] = 1
        snare[12] = 1
    if template == "halftime":
        snare = bits("0000000000001000")
    if template == "waltz":
        snare = rotate(snare, seed % 3)

    accent_slots = [2, 3, 5, 6, 7, 9, 10, 11, 13, 14, 15]
    kick[accent_slots[seed % len(accent_slots)]] = 1

    if template == "four_on_floor":
        for step in (0, 4, 8, 12):
            kick[step] = 1
    if template == "waltz":
        for step in (0, 5, 10):
            kick[step] = 1

    return (
        validate_binary_sequence(kick),
        validate_binary_sequence(snare),
        validate_binary_sequence(hihat),
    )


def build_bass_from_template(template: str, style_tag: str) -> list[int]:
    seed = stable_seed(style_tag)
    base = BASS_TEMPLATES[template]
    intervals = rotate(base, seed % 4)

    hit_steps = [i for i, v in enumerate(intervals) if v != -1]
    if hit_steps:
        idx = hit_steps[seed % len(hit_steps)]
        next_idx = (idx + 1) % STEPS
        if intervals[next_idx] == -1:
            step = 1 if ((seed // 3) % 2 == 0) else -1
            intervals[next_idx] = max(-12, min(12, intervals[idx] + step))

    if intervals[0] == -1:
        intervals[0] = 0

    return validate_interval_sequence(intervals)


def run_search_bundle(queries: list[str], fallback_suffix: str) -> tuple[dict[str, list[dict[str, str]]], list[tuple[str, int, str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    logs: list[tuple[str, int, str, str]] = []

    primary_results = batch_search(queries, count=6, delay=0.06)
    for result in primary_results:
        grouped[result.get("query", "")].append(result)

    for query in queries:
        results = grouped.get(query, [])
        if not results:
            fallback_query = f"{query} {fallback_suffix}"
            fallback_results = search(fallback_query, count=6)
            if fallback_results:
                grouped[query] = fallback_results
                logs.append(
                    (
                        fallback_query,
                        len(fallback_results),
                        "|".join(r.get("url", "") for r in fallback_results[:5] if r.get("url")),
                        WORKER,
                    )
                )
                continue

        logs.append(
            (
                query,
                len(results),
                "|".join(r.get("url", "") for r in results[:5] if r.get("url")),
                WORKER,
            )
        )

    return grouped, logs


def build_rhythm_search_patterns() -> tuple[list[dict[str, Any]], list[tuple[str, int, str, str]]]:
    queries = [item["query"] for item in RHYTHM_SEARCH_SPECS]
    results_by_query, logs = run_search_bundle(queries, "drum groove notation")
    records: list[dict[str, Any]] = []

    for spec in RHYTHM_SEARCH_SPECS:
        top = results_by_query.get(spec["query"], [{}])[0] if results_by_query.get(spec["query"]) else {}
        source_url = top.get("url", "no_result")
        title = top.get("title", "no_result")

        kick, snare, hihat = build_rhythm_from_template(spec["template"], spec["style"])
        records.append(
            make_rhythm(
                name=f"{spec['style']}_search_groove",
                style=spec["style"],
                kick=kick,
                snare=snare,
                hihat=hihat,
                description=f"Search-derived groove; reference title: {title[:120]}",
                time_signature=spec["time_signature"],
                bpm_range=spec["bpm_range"],
                source=f"Brave Search | {spec['query']} | {source_url}",
            )
        )

    return records, logs


def build_bass_search_patterns() -> tuple[list[dict[str, Any]], list[tuple[str, int, str, str]]]:
    queries = [item["query"] for item in BASS_SEARCH_SPECS]
    results_by_query, logs = run_search_bundle(queries, "bass line notation")
    records: list[dict[str, Any]] = []

    for spec in BASS_SEARCH_SPECS:
        top = results_by_query.get(spec["query"], [{}])[0] if results_by_query.get(spec["query"]) else {}
        source_url = top.get("url", "no_result")
        title = top.get("title", "no_result")

        intervals = build_bass_from_template(spec["template"], spec["style"])
        records.append(
            make_bass(
                name=f"{spec['style']}_search_bass",
                style=spec["style"],
                pattern_type=spec["pattern_type"],
                intervals=intervals,
                description=f"Search-derived bass line; reference title: {title[:120]}",
                source=f"Brave Search | {spec['query']} | {source_url}",
            )
        )

    return records, logs


def insert_patterns(
    conn: sqlite3.Connection,
    rhythm_patterns: list[dict[str, Any]],
    bass_patterns: list[dict[str, Any]],
    search_logs: list[tuple[str, int, str, str]],
) -> None:
    c = conn.cursor()

    c.execute("DELETE FROM rhythm_patterns")
    c.execute("DELETE FROM bass_patterns")

    c.executemany(
        """
        INSERT INTO rhythm_patterns (
            name, style, instrument, time_signature, bpm_range, pattern_data, description, source
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                item["name"],
                item["style"],
                item["instrument"],
                item["time_signature"],
                item["bpm_range"],
                item["pattern_data"],
                item["description"],
                item["source"],
            )
            for item in rhythm_patterns
        ],
    )

    c.executemany(
        """
        INSERT INTO bass_patterns (
            name, style, pattern_type, pattern_data, description, source
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (
                item["name"],
                item["style"],
                item["pattern_type"],
                item["pattern_data"],
                item["description"],
                item["source"],
            )
            for item in bass_patterns
        ],
    )

    c.executemany(
        """
        INSERT INTO search_log (query, result_count, source_urls, worker)
        VALUES (?, ?, ?, ?)
        """,
        search_logs,
    )

    conn.commit()


def main() -> None:
    init_db(DB_FILE)

    rhythm_search_patterns, rhythm_logs = build_rhythm_search_patterns()
    bass_search_patterns, bass_logs = build_bass_search_patterns()

    all_rhythm = RHYTHM_HARDCODED + rhythm_search_patterns
    all_bass = BASS_HARDCODED + bass_search_patterns

    if len(all_rhythm) < 40:
        raise RuntimeError(f"Expected >=40 rhythm patterns, got {len(all_rhythm)}")
    if len(all_bass) < 30:
        raise RuntimeError(f"Expected >=30 bass patterns, got {len(all_bass)}")

    conn = sqlite3.connect(str(DB_FILE))
    try:
        insert_patterns(conn, all_rhythm, all_bass, rhythm_logs + bass_logs)
        c = conn.cursor()
        rhythm_count = c.execute("SELECT COUNT(*) FROM rhythm_patterns").fetchone()[0]
        bass_count = c.execute("SELECT COUNT(*) FROM bass_patterns").fetchone()[0]
        print(f"rhythm_patterns records: {rhythm_count}")
        print(f"bass_patterns records: {bass_count}")
        print(f"search_log appended: {len(rhythm_logs) + len(bass_logs)}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
