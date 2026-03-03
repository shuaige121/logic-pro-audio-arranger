#!/usr/bin/env python3
"""Generate deterministic mood mappings and seed the mood_mappings table."""

from __future__ import annotations

import html
import json
import re
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Any

try:
    from knowledge.init_db import DB_PATH, init_db
except ModuleNotFoundError:
    from init_db import DB_PATH, init_db  # type: ignore

DB_FILE = Path(DB_PATH)
REFERENCE_FILE = Path(__file__).resolve().parent / "extracted" / "mood_music_enriched.json"
SOURCE_TAG = "generated:knowledge/gen_mood_mappings.py"

MOOD_COLUMNS = [
    "mood",
    "mood_cn",
    "tempo_range",
    "key_preference",
    "mode_preference",
    "chord_types",
    "rhythm_density",
    "dynamics",
    "register",
    "instruments",
    "texture",
    "articulation",
    "harmonic_rhythm",
    "example_progressions",
    "description",
    "source",
]

BASE_MAPPINGS: list[dict[str, Any]] = [
    {
        "mood": "happy",
        "mood_cn": "快乐/喜悦",
        "tempo_range": "120-145",
        "key_preference": "major keys, especially C, G, D, A",
        "mode_preference": "Ionian, Lydian",
        "chord_types": "major, maj7, add9, 6",
        "rhythm_density": "medium-high, steady eighths with light syncopation",
        "dynamics": "moderate to loud, bright accents",
        "register": "mid to high",
        "instruments": "acoustic guitar, piano, brass stabs, claps, light percussion",
        "texture": "layered homophonic with hook doubling",
        "articulation": "legato and light staccato mix",
        "harmonic_rhythm": "changes every 1-2 bars",
        "example_progressions": "I-V-vi-IV, I-IV-V-I",
        "description": "Bright tonic-dominant gravity and clear rhythmic lift create immediate joy.",
        "reference_query": "music emotion mood tempo key mode mapping",
        "reference_terms": ["joyful", "bright", "stable"],
    },
    {
        "mood": "sad",
        "mood_cn": "悲伤/忧郁",
        "tempo_range": "60-85",
        "key_preference": "minor keys, especially A minor, E minor, D minor",
        "mode_preference": "Aeolian, Dorian",
        "chord_types": "minor, m7, add9, sus2",
        "rhythm_density": "low-medium, sparse pulse with rests",
        "dynamics": "soft to moderate, expressive swells",
        "register": "mid-low",
        "instruments": "piano, strings, acoustic guitar, soft pads",
        "texture": "sparse homophonic, open spacing",
        "articulation": "legato, sustained phrasing",
        "harmonic_rhythm": "changes every 2-4 bars",
        "example_progressions": "i-VI-III-VII, i-iv-v-i",
        "description": "Minor color, descending motion, and slower pacing support melancholy affect.",
        "reference_query": "sad music characteristics tempo key instruments",
        "reference_terms": ["minor chords", "slow tempo", "melancholic"],
    },
    {
        "mood": "angry",
        "mood_cn": "愤怒/攻击性",
        "tempo_range": "130-180",
        "key_preference": "minor centers with b2 or chromatic tones",
        "mode_preference": "Phrygian, Aeolian, Locrian touches",
        "chord_types": "power chords, minor, diminished, tritone clusters",
        "rhythm_density": "high, dense sixteenth-note drive",
        "dynamics": "loud, compressed, heavily accented",
        "register": "low-mid with piercing highs",
        "instruments": "distorted guitar, electric bass, aggressive drums, synth leads",
        "texture": "thick layered wall with riff focus",
        "articulation": "staccatissimo, palm-muted attacks",
        "harmonic_rhythm": "changes every beat to 2 beats",
        "example_progressions": "i-bII-i, i-bVI-bVII-i",
        "description": "Fast subdivision, harsh timbre, and dissonant anchors produce aggression.",
        "reference_query": "music emotion mood tempo key mode mapping",
        "reference_terms": ["angry", "intensity", "tempo"],
    },
    {
        "mood": "peaceful",
        "mood_cn": "平和/宁静",
        "tempo_range": "55-80",
        "key_preference": "major keys with soft color tones, especially C, F, G",
        "mode_preference": "Ionian, Lydian",
        "chord_types": "maj7, add9, sus2, 6",
        "rhythm_density": "low, sustained patterns",
        "dynamics": "soft, stable, low contrast",
        "register": "mid-high airy range",
        "instruments": "piano, harp, soft pads, flute",
        "texture": "transparent and lightly layered",
        "articulation": "legato, long release tails",
        "harmonic_rhythm": "changes every 2-4 bars",
        "example_progressions": "I-ii-IV-I, I-IVmaj7-I",
        "description": "Open voicing and slow harmonic turnover reduce tension and invite calm.",
        "reference_query": "dreamy ethereal music production techniques",
        "reference_terms": ["serene", "atmosphere", "sustained"],
    },
    {
        "mood": "tense",
        "mood_cn": "紧张/悬疑",
        "tempo_range": "80-120",
        "key_preference": "minor or unstable tonal centers with chromatic pressure",
        "mode_preference": "Phrygian, Locrian, octatonic colors",
        "chord_types": "diminished, m7b5, sus4, dominant b9",
        "rhythm_density": "medium-high, ostinato and pulse repetition",
        "dynamics": "moderate to very loud, frequent crescendos",
        "register": "low drones with high ostinato accents",
        "instruments": "low strings, piano ostinato, synth pulses, percussion hits",
        "texture": "layered with pedal points and dissonant overlays",
        "articulation": "marcato, tremolo, short stabs",
        "harmonic_rhythm": "changes every beat to 1 bar",
        "example_progressions": "i-bII-i, iio7-V7alt-i",
        "description": "Dissonance and delayed resolution create expectation and threat.",
        "reference_query": "tense suspenseful music harmony dissonance",
        "reference_terms": ["tension", "dissonance", "suspense"],
    },
    {
        "mood": "romantic",
        "mood_cn": "浪漫/爱意",
        "tempo_range": "70-105",
        "key_preference": "warm major/minor keys, especially Eb, Ab, F, D minor",
        "mode_preference": "Ionian, Aeolian, Dorian",
        "chord_types": "maj7, m7, 6, 9, sus4",
        "rhythm_density": "medium, flowing pulse with triplet feel options",
        "dynamics": "soft to moderate, frequent swells",
        "register": "mid register focus",
        "instruments": "piano, strings, acoustic guitar, soft sax",
        "texture": "lush homophonic with countermelody",
        "articulation": "legato, light portamento",
        "harmonic_rhythm": "changes every 2 bars",
        "example_progressions": "I-vi-ii-V, vi-IV-I-V",
        "description": "Extended tertian harmony and singing inner lines support intimacy.",
        "reference_query": "romantic music arrangement characteristics",
        "reference_terms": ["romantic", "emotional depth", "arrangement"],
    },
    {
        "mood": "epic",
        "mood_cn": "史诗/凯旋",
        "tempo_range": "90-140",
        "key_preference": "minor centers with heroic major lifts",
        "mode_preference": "Aeolian, Dorian, Lydian colors",
        "chord_types": "power chords, minor add9, sus4, broad major triads",
        "rhythm_density": "medium-high, driving ostinatos",
        "dynamics": "wide dynamic range with long builds",
        "register": "full spectrum from sub bass to high brass/choir",
        "instruments": "orchestral strings, brass, choir, taiko, hybrid synths",
        "texture": "dense layered cinematic blocks",
        "articulation": "marcato accents with legato pads",
        "harmonic_rhythm": "changes every 1 bar with pedal anchors",
        "example_progressions": "i-bVI-bIII-bVII, i-VI-III-VII",
        "description": "Large registral span and incremental layering produce triumph and scale.",
        "reference_query": "epic cinematic music arrangement techniques",
        "reference_terms": ["epic", "cinematic", "majestic"],
    },
    {
        "mood": "mysterious",
        "mood_cn": "神秘/暗色",
        "tempo_range": "70-110",
        "key_preference": "minor keys with chromatic mediants and modal ambiguity",
        "mode_preference": "Dorian, Phrygian, Lydian #4 hints",
        "chord_types": "m(add9), diminished, quartal, sus2",
        "rhythm_density": "medium, irregular pulse spacing",
        "dynamics": "soft to moderate with sudden accents",
        "register": "low-mid shadows with high detail",
        "instruments": "bass clarinet, prepared piano, reverse pads, low strings",
        "texture": "thin-to-layered with negative space",
        "articulation": "tenuto, tremolo, harmonic overtones",
        "harmonic_rhythm": "changes every 2 bars, often with pedal",
        "example_progressions": "i-bVI-i, i-bII-v",
        "description": "Ambiguous function and unusual color tones preserve uncertainty.",
        "reference_query": "tense suspenseful music harmony dissonance",
        "reference_terms": ["mystery", "suspense", "unresolved"],
    },
    {
        "mood": "playful",
        "mood_cn": "俏皮/轻快",
        "tempo_range": "100-145",
        "key_preference": "major keys, especially C, G, D",
        "mode_preference": "Ionian, Mixolydian",
        "chord_types": "major, 6, maj7, dominant 7",
        "rhythm_density": "medium-high, bouncy syncopation",
        "dynamics": "moderate with short accents",
        "register": "mid-high",
        "instruments": "pizzicato strings, marimba, ukulele, claps, woodwinds",
        "texture": "light contrapuntal interlock",
        "articulation": "staccato, spiccato",
        "harmonic_rhythm": "changes every 1-2 bars",
        "example_progressions": "I-vi-ii-V, I-IV-I-V",
        "description": "Short-note articulation and elastic rhythm drive a lighthearted tone.",
        "reference_query": "music emotion mood tempo key mode mapping",
        "reference_terms": ["lively", "positive", "poppy"],
    },
    {
        "mood": "dreamy",
        "mood_cn": "梦幻/空灵",
        "tempo_range": "65-100",
        "key_preference": "major/minor ambiguity with sustained tonal center",
        "mode_preference": "Lydian, major pentatonic, Dorian",
        "chord_types": "maj7#11, add9, sus2, no3 voicings",
        "rhythm_density": "low-medium, flowing and diffuse",
        "dynamics": "soft with gradual swells",
        "register": "mid-high and high",
        "instruments": "synth pads, electric piano, reverb guitar, airy vocals",
        "texture": "washed layered ambient bed",
        "articulation": "legato, long tails, blurred attacks",
        "harmonic_rhythm": "changes every 2-4 bars",
        "example_progressions": "Imaj7-IIImaj7-IVmaj7, vi-IV-I-V (slow)",
        "description": "Sustained textures and color extensions create floating perception.",
        "reference_query": "dreamy ethereal music production techniques",
        "reference_terms": ["ethereal", "synth pads", "atmospheres"],
    },
    {
        "mood": "nostalgic",
        "mood_cn": "怀旧/苦甜",
        "tempo_range": "75-110",
        "key_preference": "major-minor mixture, often relative key motion",
        "mode_preference": "Ionian with borrowed iv, Dorian",
        "chord_types": "maj7, m6, add9, secondary dominants",
        "rhythm_density": "medium, steady pulse",
        "dynamics": "moderate with softened transients",
        "register": "mid-focused",
        "instruments": "piano, strings, tape keys, clean guitar",
        "texture": "warm layered but not dense",
        "articulation": "legato with occasional detached pickup",
        "harmonic_rhythm": "changes every 1-2 bars",
        "example_progressions": "I-IV-ii-V, I-vi-IV-V",
        "description": "Borrowed harmony and familiar cadential loops evoke memory and longing.",
        "reference_query": "melancholy nostalgic music chord progressions",
        "reference_terms": ["nostalgic", "memories", "melancholy"],
    },
    {
        "mood": "energetic",
        "mood_cn": "活力/高能",
        "tempo_range": "125-170",
        "key_preference": "strong tonal centers in major or natural minor",
        "mode_preference": "Ionian, Mixolydian, Aeolian",
        "chord_types": "major/minor triads, power chords, dominant hooks",
        "rhythm_density": "high, continuous drive and syncopation",
        "dynamics": "loud and consistent with peak accents",
        "register": "full with bright upper hook",
        "instruments": "drums, synth lead, bass, guitar, brass stabs",
        "texture": "dense layered groove stack",
        "articulation": "accented staccato and tight legato",
        "harmonic_rhythm": "changes every 1 bar",
        "example_progressions": "I-V-vi-IV, i-bVII-bVI-bVII",
        "description": "Fast tempo and high rhythmic occupancy maximize kinetic momentum.",
        "reference_query": "music emotion mood tempo key mode mapping",
        "reference_terms": ["upbeat", "tempo", "intensity"],
    },
    {
        "mood": "lonely",
        "mood_cn": "孤独/隔离",
        "tempo_range": "50-75",
        "key_preference": "minor keys with sparse tonic reinforcement",
        "mode_preference": "Aeolian, Dorian",
        "chord_types": "minor, m(add9), sus2, open fifths",
        "rhythm_density": "low, many rests and long tones",
        "dynamics": "very soft to soft",
        "register": "low-mid",
        "instruments": "solo piano, cello, distant pad, soft guitar",
        "texture": "monophonic to sparse homophonic",
        "articulation": "legato, unhurried phrasing",
        "harmonic_rhythm": "changes every 4 bars or slower",
        "example_progressions": "i-iv-i, i-VI-iv-i",
        "description": "Minimal layering and long empty spaces amplify isolation.",
        "reference_query": "sad music characteristics tempo key instruments",
        "reference_terms": ["slow tempo", "minimal instrumentation", "sad"],
    },
    {
        "mood": "hopeful",
        "mood_cn": "希望/振奋",
        "tempo_range": "90-125",
        "key_preference": "major keys with bright upper extensions",
        "mode_preference": "Ionian, Lydian",
        "chord_types": "major, add9, maj7, sus2",
        "rhythm_density": "medium, forward-moving pulse",
        "dynamics": "moderate with clear crescendos",
        "register": "mid-high",
        "instruments": "piano, guitar, strings, bells, light synth",
        "texture": "layered rising contours",
        "articulation": "legato with accented pickups",
        "harmonic_rhythm": "changes every 1-2 bars",
        "example_progressions": "I-V-vi-IV, IV-I-V-vi",
        "description": "Stable cadences plus upward melodic contour communicate uplift.",
        "reference_query": "music emotion mood tempo key mode mapping",
        "reference_terms": ["hopeful", "uplifting", "positive"],
    },
    {
        "mood": "fearful",
        "mood_cn": "恐惧/焦虑",
        "tempo_range": "70-115",
        "key_preference": "unstable minor centers, chromatic tension notes",
        "mode_preference": "Locrian, Phrygian, octatonic",
        "chord_types": "diminished, m7b5, clusters, tritone dyads",
        "rhythm_density": "medium-high, irregular pulse with heartbeat motifs",
        "dynamics": "extreme jumps from pp to ff",
        "register": "very low rumbles with high spikes",
        "instruments": "low strings, fx percussion, synth drones, prepared piano",
        "texture": "dissonant layered with sudden gaps",
        "articulation": "tremolo, sul ponticello, sharp stabs",
        "harmonic_rhythm": "changes every beat or held drone then hit",
        "example_progressions": "io-bII-i, i-viio-i",
        "description": "Volatile dynamics and unstable harmony heighten threat response.",
        "reference_query": "tense suspenseful music harmony dissonance",
        "reference_terms": ["anxious", "tension", "release"],
    },
    {
        "mood": "powerful",
        "mood_cn": "强大/自信",
        "tempo_range": "95-135",
        "key_preference": "minor or mixolydian tonal centers with strong root motion",
        "mode_preference": "Aeolian, Mixolydian, Dorian",
        "chord_types": "power chords, dominant 7, sus4, add9",
        "rhythm_density": "medium-high, heavy quarter/eighth drive",
        "dynamics": "loud, controlled, punchy",
        "register": "low-mid emphasis with high support",
        "instruments": "drums, electric bass, guitars, brass, low synth",
        "texture": "thick homophonic blocks",
        "articulation": "marcato and accented sustain",
        "harmonic_rhythm": "changes every 1-2 bars",
        "example_progressions": "i-bVII-bVI-bVII, I-bVII-IV-I",
        "description": "Strong downbeats and registral weight support confident energy.",
        "reference_query": "epic cinematic music arrangement techniques",
        "reference_terms": ["heroic", "epic", "drama"],
    },
    {
        "mood": "gentle",
        "mood_cn": "温柔/细腻",
        "tempo_range": "60-90",
        "key_preference": "major keys and relative minor with soft color tones",
        "mode_preference": "Ionian, Dorian",
        "chord_types": "major, maj7, m7, sus2",
        "rhythm_density": "low-medium, delicate arpeggios",
        "dynamics": "soft and even",
        "register": "mid-high",
        "instruments": "nylon guitar, piano, flute, light strings",
        "texture": "light transparent support",
        "articulation": "legato and brushed attacks",
        "harmonic_rhythm": "changes every 2-4 bars",
        "example_progressions": "I-iii-IV-I, vi-IV-I-V",
        "description": "Low dynamic pressure and consonant voicings convey tenderness.",
        "reference_query": "emotional ballad arrangement techniques instruments",
        "reference_terms": ["ballad", "less is more", "soft"],
    },
    {
        "mood": "wild",
        "mood_cn": "狂野/失控",
        "tempo_range": "130-190",
        "key_preference": "chromatic or minor-centric with modal shifts",
        "mode_preference": "Phrygian, Locrian, whole-tone fragments",
        "chord_types": "power chords, diminished, augmented, clusters",
        "rhythm_density": "very high, polymetric and syncopated",
        "dynamics": "extreme, abrupt peaks",
        "register": "full and rapidly shifting",
        "instruments": "distorted guitars, synths, heavy drums, aggressive bass",
        "texture": "chaotic multilayer with overlaps",
        "articulation": "staccatissimo, glissandi, abrupt cuts",
        "harmonic_rhythm": "changes nearly every beat",
        "example_progressions": "i-bII-bIII-bII, chromatic mediant chains",
        "description": "Frequent metric surprises and dense timbral change read as unruly.",
        "reference_query": "music emotion mood tempo key mode mapping",
        "reference_terms": ["intensity", "dark", "lively"],
    },
    {
        "mood": "spiritual",
        "mood_cn": "灵性/冥想",
        "tempo_range": "50-85",
        "key_preference": "modal centers with sustained drones",
        "mode_preference": "Dorian, Mixolydian, pentatonic",
        "chord_types": "sus2, sus4, add9, open fifth drone",
        "rhythm_density": "low, repetitive chant-like pulse",
        "dynamics": "soft to moderate, long crescendos",
        "register": "mid-high over low drone",
        "instruments": "choir, strings, handpan, harmonium, bells",
        "texture": "drone plus slowly evolving layers",
        "articulation": "legato, sustained resonance",
        "harmonic_rhythm": "changes every 4 bars or slower",
        "example_progressions": "i-bVII-i, I-IV-I (drone-based)",
        "description": "Modal drone harmony and gradual evolution support meditative focus.",
        "reference_query": "dreamy ethereal music production techniques",
        "reference_terms": ["ethereal", "serene", "ambient"],
    },
    {
        "mood": "groovy",
        "mood_cn": "律动/放克感",
        "tempo_range": "90-120",
        "key_preference": "minor or mixolydian centers",
        "mode_preference": "Dorian, Mixolydian, blues scale",
        "chord_types": "m7, 9, 13, dominant 7, sus",
        "rhythm_density": "medium-high, syncopated sixteenth pocket",
        "dynamics": "moderate with ghost-note accents",
        "register": "mid-low groove register",
        "instruments": "electric bass, clavinet, guitar, drums, brass hits",
        "texture": "interlocking rhythmic polyphony",
        "articulation": "tight staccato and muted attacks",
        "harmonic_rhythm": "changes every 1 bar",
        "example_progressions": "i7-IV7, I7-IV7, ii7-V7",
        "description": "Micro-timing and syncopation define groove more than complex harmony.",
        "reference_query": "music emotion mood tempo key mode mapping",
        "reference_terms": ["tempo", "rhythm", "intensity"],
    },
    {
        "mood": "majestic",
        "mood_cn": "庄严/宏伟",
        "tempo_range": "70-110",
        "key_preference": "major keys, often Eb, Bb, Db for orchestral weight",
        "mode_preference": "Ionian, Lydian",
        "chord_types": "major, maj7, sus4, add9",
        "rhythm_density": "medium, broad rhythmic values",
        "dynamics": "wide crescendos to forte/fortissimo",
        "register": "full range with strong upper brass",
        "instruments": "orchestra, brass, choir, timpani",
        "texture": "grand layered homophony",
        "articulation": "legato with strong marcato peaks",
        "harmonic_rhythm": "changes every 2 bars",
        "example_progressions": "I-IV-vi-V, I-V-IV-I",
        "description": "Wide voicing and ceremonial pacing communicate grandeur.",
        "reference_query": "epic cinematic music arrangement techniques",
        "reference_terms": ["majestic", "cinematic", "heroic"],
    },
    {
        "mood": "whimsical",
        "mood_cn": "奇趣/古怪",
        "tempo_range": "95-135",
        "key_preference": "major/modal centers with chromatic passing color",
        "mode_preference": "Lydian, Mixolydian, Dorian",
        "chord_types": "6, add9, sus2, passing diminished",
        "rhythm_density": "medium, offbeat and playful accents",
        "dynamics": "moderate with sudden light accents",
        "register": "high-mid",
        "instruments": "celesta, pizz strings, woodwinds, accordion, toy piano",
        "texture": "light contrapuntal with pointillistic layers",
        "articulation": "staccato, spiccato, short tenuto",
        "harmonic_rhythm": "changes every 1-2 bars",
        "example_progressions": "I-II-IV-I (Lydian), I-vi-ii-V",
        "description": "Unexpected color tones and playful orchestration create quirky charm.",
        "reference_query": "music emotion mood tempo key mode mapping",
        "reference_terms": ["modes", "characteristics", "emotion"],
    },
    {
        "mood": "haunting",
        "mood_cn": "阴森/幽魅",
        "tempo_range": "60-95",
        "key_preference": "minor centers with static bass pedals",
        "mode_preference": "Aeolian, Phrygian, Dorian",
        "chord_types": "m(add9), diminished, sus2, open fifths",
        "rhythm_density": "low-medium, slow repeated figures",
        "dynamics": "soft with sudden swells",
        "register": "low drones and thin high overtones",
        "instruments": "choir, strings, prepared piano, reverb guitar",
        "texture": "sparse reverberant layers",
        "articulation": "legato, tremolo, breathy attacks",
        "harmonic_rhythm": "changes every 2-4 bars",
        "example_progressions": "i-bVI-i, i-v-iv-i",
        "description": "Persistent pedal tones and unresolved color tones create eerie pull.",
        "reference_query": "tense suspenseful music harmony dissonance",
        "reference_terms": ["suspense", "dissonance", "unrest"],
    },
    {
        "mood": "passionate",
        "mood_cn": "炽烈/强烈",
        "tempo_range": "95-145",
        "key_preference": "minor keys with dramatic dominant pull",
        "mode_preference": "Aeolian, harmonic minor, Phrygian dominant hints",
        "chord_types": "minor, dominant 7, b9, augmented color",
        "rhythm_density": "medium-high, driving with rubato pushes",
        "dynamics": "large swells and strong accents",
        "register": "mid-high lead with grounded bass",
        "instruments": "piano, strings, guitar, hand percussion, vocal lead",
        "texture": "thick melodic foreground with harmonic bed",
        "articulation": "legato with emphatic accents",
        "harmonic_rhythm": "changes every 1-2 bars",
        "example_progressions": "i-VI-iv-V, i-bVII-bVI-V",
        "description": "Dominant tension and expressive dynamic contour maximize emotional heat.",
        "reference_query": "romantic music arrangement characteristics",
        "reference_terms": ["romantic", "drama", "emotional depth"],
    },
    {
        "mood": "serene",
        "mood_cn": "安然/恬静",
        "tempo_range": "55-78",
        "key_preference": "major keys and pentatonic color sets",
        "mode_preference": "Ionian, Lydian, major pentatonic",
        "chord_types": "maj7, 6, add9, sus2",
        "rhythm_density": "low, sustained slow pulse",
        "dynamics": "very soft and stable",
        "register": "mid-high",
        "instruments": "piano, harp, airy pads, flute",
        "texture": "clear and uncluttered",
        "articulation": "legato, no hard attacks",
        "harmonic_rhythm": "changes every 4 bars",
        "example_progressions": "I-IVmaj7-I, I-ii-I",
        "description": "Consonant color extensions and low contrast preserve tranquility.",
        "reference_query": "dreamy ethereal music production techniques",
        "reference_terms": ["serene", "dreamlike", "lush background"],
    },
    {
        "mood": "rebellious",
        "mood_cn": "反叛/不羁",
        "tempo_range": "120-175",
        "key_preference": "minor and mixolydian rock centers",
        "mode_preference": "Aeolian, Phrygian, Mixolydian",
        "chord_types": "power chords, bVII, bIII, sus4",
        "rhythm_density": "high, driving syncopation",
        "dynamics": "loud, raw, low compression polish",
        "register": "low-mid riff focus",
        "instruments": "distorted guitars, bass, live drums, shouted vocals",
        "texture": "thick riff-based homophony",
        "articulation": "aggressive staccato and accented downstrokes",
        "harmonic_rhythm": "changes every 1 bar",
        "example_progressions": "i-bVII-bVI-bVII, I-bVII-IV-I",
        "description": "Riff repetition, saturation, and modal flat-seven color signal defiance.",
        "reference_query": "music emotion mood tempo key mode mapping",
        "reference_terms": ["angry", "rocky", "dark"],
    },
    {
        "mood": "celebratory",
        "mood_cn": "庆典/欢庆",
        "tempo_range": "110-150",
        "key_preference": "major keys with strong dominant returns",
        "mode_preference": "Ionian, Mixolydian",
        "chord_types": "major, dominant 7, add9, sus4",
        "rhythm_density": "high, danceable straight groove",
        "dynamics": "loud and bright with crowd-style accents",
        "register": "full, hook in mid-high",
        "instruments": "brass, percussion, drums, guitar, synths, claps",
        "texture": "anthemic layered chorus texture",
        "articulation": "accented legato-staccato blend",
        "harmonic_rhythm": "changes every 1-2 bars",
        "example_progressions": "I-IV-V-I, I-V-vi-IV",
        "description": "Regular cadential payoff and festive timbre combinations support celebration.",
        "reference_query": "music emotion mood tempo key mode mapping",
        "reference_terms": ["bright", "positive", "stable"],
    },
    {
        "mood": "introspective",
        "mood_cn": "内省/反思",
        "tempo_range": "60-95",
        "key_preference": "minor or mixed mode centers with gentle cadences",
        "mode_preference": "Aeolian, Dorian, borrowed-chord major",
        "chord_types": "m7, maj7, add9, sus2",
        "rhythm_density": "low-medium, sparse rhythmic framing",
        "dynamics": "soft to moderate, restrained peaks",
        "register": "mid",
        "instruments": "piano, electric piano, ambient guitar, soft strings",
        "texture": "sparse layered with room for melody",
        "articulation": "legato and breath-like phrasing",
        "harmonic_rhythm": "changes every 2-4 bars",
        "example_progressions": "vi-IV-I-V, i-iv-VI-V",
        "description": "Gentle harmonic color and space-heavy phrasing encourage reflection.",
        "reference_query": "melancholy nostalgic music chord progressions",
        "reference_terms": ["emotion", "minor chords", "introspection"],
    },
    {
        "mood": "dramatic",
        "mood_cn": "戏剧化/电影感",
        "tempo_range": "80-130",
        "key_preference": "minor keys with chromatic mediants and strong dominant events",
        "mode_preference": "Aeolian, Phrygian, harmonic minor",
        "chord_types": "minor, diminished, augmented, dominant b9",
        "rhythm_density": "medium-high, ostinato plus impact hits",
        "dynamics": "extreme contrast and sudden climaxes",
        "register": "very wide range",
        "instruments": "orchestra, hybrid percussion, brass, strings, synth layers",
        "texture": "dense cinematic stack with transient accents",
        "articulation": "marcato, sforzando, tremolo transitions",
        "harmonic_rhythm": "changes every 1-2 beats at climax",
        "example_progressions": "i-bVI-III-V, i-iv-V-i",
        "description": "Contrast-driven dynamics and expanded orchestration produce narrative drama.",
        "reference_query": "epic cinematic music arrangement techniques",
        "reference_terms": ["cinematic", "suspenseful", "epic"],
    },
    {
        "mood": "chill",
        "mood_cn": "松弛/放松",
        "tempo_range": "70-105",
        "key_preference": "major/minor centers with soft color harmony",
        "mode_preference": "Dorian, Mixolydian, major pentatonic",
        "chord_types": "m7, maj7, 9, sus2",
        "rhythm_density": "low-medium, laid-back groove",
        "dynamics": "soft, controlled, low transient sharpness",
        "register": "mid-low with airy highs",
        "instruments": "electric piano, lofi drums, sub bass, guitar, pads",
        "texture": "minimal layered pocket",
        "articulation": "legato with light ghost-note punctuation",
        "harmonic_rhythm": "changes every 2 bars",
        "example_progressions": "ii7-V7-Imaj7-vi7, i7-IV7",
        "description": "Relaxed micro-timing and mellow timbre sustain an easy listening state.",
        "reference_query": "dreamy ethereal music production techniques",
        "reference_terms": ["atmospheric", "serene", "pads"],
    },
]

TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")


def clean_text(text: str, limit: int | None = None) -> str:
    cleaned = SPACE_RE.sub(" ", text).strip()
    if limit is None or len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3].rstrip() + "..."


def clean_html_text(text: str) -> str:
    return clean_text(TAG_RE.sub(" ", html.unescape(text or "")))


def normalize(text: str) -> str:
    return clean_text(text).casefold()


def load_references(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing reference file: {path}")

    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("Reference JSON must be a list")

    refs: list[dict[str, str]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        refs.append(
            {
                "title": clean_html_text(str(item.get("title", ""))),
                "url": clean_text(str(item.get("url", ""))),
                "description": clean_html_text(str(item.get("description", ""))),
                "query": clean_text(str(item.get("query", ""))),
                "page_excerpt": clean_html_text(str(item.get("page_excerpt", ""))),
            }
        )
    return refs


def score_reference(ref: dict[str, str], terms: list[str]) -> float:
    blob = normalize(
        " ".join(
            [
                ref.get("title", ""),
                ref.get("description", ""),
                ref.get("query", ""),
                ref.get("page_excerpt", "")[:1200],
            ]
        )
    )
    score = 0.0
    for term in terms:
        token = normalize(term)
        if token and token in blob:
            score += 3.0

    if "fetch_error" in blob:
        score -= 6.0
    if ref.get("url", "").startswith("http"):
        score += 1.0
    score += min(len(ref.get("description", "")), 260) / 260.0
    return score


def pick_reference(
    refs_by_query: dict[str, list[dict[str, str]]],
    all_refs: list[dict[str, str]],
    query: str,
    terms: list[str],
) -> dict[str, str]:
    candidates = refs_by_query.get(query) or all_refs
    if not candidates:
        return {"title": "", "url": "", "description": "", "query": "", "page_excerpt": ""}
    return max(candidates, key=lambda ref: score_reference(ref, terms))


def build_seed_rows(references: list[dict[str, str]]) -> list[dict[str, str]]:
    refs_by_query: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in references:
        refs_by_query[row.get("query", "")].append(row)

    rows: list[dict[str, str]] = []
    for base in BASE_MAPPINGS:
        query = str(base.get("reference_query", ""))
        terms = [str(base.get("mood", ""))] + [str(x) for x in base.get("reference_terms", [])]
        ref = pick_reference(refs_by_query, references, query, terms)

        snippet = clean_text(ref.get("description", "") or ref.get("title", ""), limit=220)
        desc_with_ref = (
            f"{base['description']} Search reference: {snippet}"
            if snippet
            else str(base["description"])
        )
        source = (
            f"{SOURCE_TAG}|query={ref.get('query', '')}|url={ref.get('url', '')}"
            if ref.get("url")
            else f"{SOURCE_TAG}|query={ref.get('query', '')}|url=missing"
        )

        row: dict[str, str] = {
            "mood": str(base["mood"]),
            "mood_cn": str(base["mood_cn"]),
            "tempo_range": str(base["tempo_range"]),
            "key_preference": str(base["key_preference"]),
            "mode_preference": str(base["mode_preference"]),
            "chord_types": str(base["chord_types"]),
            "rhythm_density": str(base["rhythm_density"]),
            "dynamics": str(base["dynamics"]),
            "register": str(base["register"]),
            "instruments": str(base["instruments"]),
            "texture": str(base["texture"]),
            "articulation": str(base["articulation"]),
            "harmonic_rhythm": str(base["harmonic_rhythm"]),
            "example_progressions": str(base["example_progressions"]),
            "description": clean_text(desc_with_ref, limit=500),
            "source": clean_text(source, limit=500),
        }
        rows.append(row)

    deduped: dict[str, dict[str, str]] = {}
    for row in rows:
        deduped[row["mood"].casefold()] = row
    return list(deduped.values())


def seed_mood_mappings(rows: list[dict[str, str]]) -> int:
    conn = sqlite3.connect(str(DB_FILE))
    cur = conn.cursor()
    cur.execute("DELETE FROM mood_mappings")
    cur.executemany(
        """
        INSERT INTO mood_mappings (
            mood, mood_cn, tempo_range, key_preference, mode_preference, chord_types,
            rhythm_density, dynamics, register, instruments, texture, articulation,
            harmonic_rhythm, example_progressions, description, source
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [tuple(row[col] for col in MOOD_COLUMNS) for row in rows],
    )
    conn.commit()
    count = cur.execute("SELECT COUNT(*) FROM mood_mappings").fetchone()[0]
    conn.close()
    return int(count)


def main() -> None:
    init_db(DB_FILE)
    references = load_references(REFERENCE_FILE)
    rows = build_seed_rows(references)
    if len(rows) < 30:
        raise ValueError(f"Expected at least 30 rows, got {len(rows)}")

    count = seed_mood_mappings(rows)
    print(f"search references loaded: {len(references)}")
    print(f"mood mappings prepared: {len(rows)}")
    print(f"mood_mappings records: {count}")
    if count < 30:
        raise RuntimeError(f"mood_mappings count is below requirement: {count}")


if __name__ == "__main__":
    main()
