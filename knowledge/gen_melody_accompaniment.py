#!/usr/bin/env python3
"""Generate melody-accompaniment relationship knowledge into SQLite."""

from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path
from typing import Any

try:
    from knowledge.init_db import DB_PATH, init_db
except ModuleNotFoundError:
    from init_db import DB_PATH, init_db


SOURCE_PREFIX = "gen_melody_accompaniment"
ENRICHED_JSON_PATH = Path(__file__).parent / "extracted" / "melody_accompaniment_enriched.json"
DB_FILE = Path(DB_PATH)

ALLOWED_RELATIONSHIPS = {
    "rhythmic_complement",
    "rhythmic_unison",
    "call_response",
    "sustained_pad",
    "countermelody",
    "doubling",
    "rhythmic_ostinato",
    "harmonic_support",
    "bass_foundation",
    "textural_fill",
}
ALLOWED_SECTION_TYPES = {"verse", "chorus", "bridge", "general"}
ALLOWED_TENSION = {"low", "medium", "high"}

RELATIONSHIP_HINTS: dict[str, tuple[str, ...]] = {
    "rhythmic_complement": ("complement", "space", "accent", "texture", "rhythm"),
    "rhythmic_unison": ("unison", "same rhythm", "hit", "lock", "together"),
    "call_response": ("call", "response", "answer", "fill", "gap"),
    "sustained_pad": ("pad", "sustain", "long", "background", "support"),
    "countermelody": ("countermelody", "counterpoint", "independent", "line"),
    "doubling": ("double", "octave", "unison", "layer"),
    "rhythmic_ostinato": ("ostinato", "repeating", "loop", "pattern"),
    "harmonic_support": ("harmony", "chord", "comping", "accompaniment"),
    "bass_foundation": ("bass", "root", "foundation", "low end", "walking"),
    "textural_fill": ("texture", "fill", "ornament", "density"),
}

STOP_TOKENS = {
    "and",
    "the",
    "with",
    "for",
    "under",
    "line",
    "lead",
    "general",
    "style",
    "music",
    "pattern",
}


def rec(
    *,
    name: str,
    style: str,
    section_type: str,
    melody_instrument: str,
    accomp_instrument: str,
    relationship: str,
    rhythm_relation: str,
    register_relation: str,
    dynamic_relation: str,
    mood: str,
    tension_level: str,
    description: str,
    example_song: str,
) -> dict[str, str]:
    return {
        "name": name,
        "style": style,
        "section_type": section_type,
        "melody_instrument": melody_instrument,
        "accomp_instrument": accomp_instrument,
        "relationship": relationship,
        "rhythm_relation": rhythm_relation,
        "register_relation": register_relation,
        "dynamic_relation": dynamic_relation,
        "mood": mood,
        "tension_level": tension_level,
        "description": description,
        "example_song": example_song,
    }


BASE_PATTERNS: list[dict[str, str]] = [
    # Vocal + Piano (arpeggio / block chords / broken chords across verse+chorus)
    rec(
        name="piano_arpeggio_under_vocal_verse_pop",
        style="pop_ballad",
        section_type="verse",
        melody_instrument="vocal",
        accomp_instrument="piano",
        relationship="rhythmic_complement",
        rhythm_relation="vocal holds longer notes while right-hand piano fills eighth-note arpeggios between syllables",
        register_relation="accompaniment sits 1 octave below melody with occasional upper passing tones",
        dynamic_relation="accompaniment 15-20% quieter than melody",
        mood="intimate and reflective",
        tension_level="low",
        description="Classic verse texture where vocal phrase clarity leads and piano motion keeps pulse without crowding lyrics.",
        example_song="Adele - Someone Like You",
    ),
    rec(
        name="piano_arpeggio_under_vocal_chorus_pop",
        style="pop_ballad",
        section_type="chorus",
        melody_instrument="vocal",
        accomp_instrument="piano",
        relationship="rhythmic_ostinato",
        rhythm_relation="continuous sixteenth-note arpeggio loop supports repeated chorus hook rhythm",
        register_relation="left hand anchors low roots, right hand cycles in middle register below melody",
        dynamic_relation="accompaniment 10-15% quieter than melody but denser than verse",
        mood="uplift with momentum",
        tension_level="medium",
        description="Ostinato arpeggios increase motion in chorus while preserving harmonic clarity under the hook.",
        example_song="Coldplay - Fix You (live piano arrangement feel)",
    ),
    rec(
        name="piano_block_chords_under_vocal_verse_rnb",
        style="rnb",
        section_type="verse",
        melody_instrument="vocal",
        accomp_instrument="piano",
        relationship="harmonic_support",
        rhythm_relation="short syncopated chord stabs answer lyric endings",
        register_relation="block chords in mid register leave top register for vocal ad-libs",
        dynamic_relation="accompaniment 20% quieter than melody, soft attack",
        mood="warm and conversational",
        tension_level="low",
        description="Sparse block chords provide harmonic landmarks while preserving pocket and vocal intimacy.",
        example_song="H.E.R. - Focus",
    ),
    rec(
        name="piano_block_chords_under_vocal_chorus_soul",
        style="soul_pop",
        section_type="chorus",
        melody_instrument="vocal",
        accomp_instrument="piano",
        relationship="rhythmic_unison",
        rhythm_relation="piano hits important lyric accents in near-unison with vocal rhythm",
        register_relation="chords centered in middle C area, melody stays above for focus",
        dynamic_relation="accompaniment 10% quieter on average, swells with chorus accents",
        mood="assertive and anthemic",
        tension_level="medium",
        description="Chord punches aligned with vocal accents make the chorus feel direct and communal.",
        example_song="Alicia Keys - If I Ain't Got You",
    ),
    rec(
        name="piano_broken_chords_under_vocal_verse_folk",
        style="folk",
        section_type="verse",
        melody_instrument="vocal",
        accomp_instrument="piano",
        relationship="call_response",
        rhythm_relation="vocal phrases leave quarter-note gaps where broken-chord fragments respond",
        register_relation="melody in upper-mid range, accompaniment in low-mid range with occasional high echo notes",
        dynamic_relation="accompaniment 20-25% quieter than melody",
        mood="storytelling and spacious",
        tension_level="low",
        description="Broken chord responses reinforce phrase endings and maintain organic singer-songwriter flow.",
        example_song="Sara Bareilles - Gravity",
    ),
    rec(
        name="piano_broken_chords_under_vocal_chorus_pop",
        style="pop",
        section_type="chorus",
        melody_instrument="vocal",
        accomp_instrument="piano",
        relationship="harmonic_support",
        rhythm_relation="alternating root-third-fifth pattern supports steady quarter-note vocal hook",
        register_relation="left hand doubles roots below, right hand broken triads stay below vocal band",
        dynamic_relation="accompaniment 10-15% quieter than melody",
        mood="bright and open",
        tension_level="medium",
        description="Broken triads widen harmonic space and keep chorus buoyant without over-compressing rhythm.",
        example_song="Keane - Somewhere Only We Know",
    ),
    rec(
        name="piano_octave_doubling_vocal_hook_chorus",
        style="pop_ballad",
        section_type="chorus",
        melody_instrument="vocal",
        accomp_instrument="piano",
        relationship="doubling",
        rhythm_relation="piano doubles hook rhythm on downbeats and sustains between vocal syllables",
        register_relation="doubling one octave below vocal line to increase weight",
        dynamic_relation="accompaniment 5-10% quieter than melody to avoid masking consonants",
        mood="emotional climax",
        tension_level="high",
        description="Selective octave doubling emphasizes the catchiest notes and raises chorus impact.",
        example_song="Lewis Capaldi - Someone You Loved",
    ),
    rec(
        name="piano_sparse_stabs_vocal_bridge",
        style="pop",
        section_type="bridge",
        melody_instrument="vocal",
        accomp_instrument="piano",
        relationship="textural_fill",
        rhythm_relation="single-beat stabs punctuate long vocal tones and transitional lyrics",
        register_relation="stabs in lower-mid register leave top register empty for vocal lift",
        dynamic_relation="accompaniment 20% quieter than melody, with brief accent peaks",
        mood="suspended and anticipatory",
        tension_level="medium",
        description="Bridge texture strips density so punctuating stabs frame lyric pivots and setup final chorus.",
        example_song="Sam Smith - Stay With Me",
    ),
    # Vocal + Guitar
    rec(
        name="acoustic_strum_under_vocal_verse_pop",
        style="acoustic_pop",
        section_type="verse",
        melody_instrument="vocal",
        accomp_instrument="acoustic_guitar",
        relationship="harmonic_support",
        rhythm_relation="light down-up strum on beats 1 and 3 with syncopated lift into beat 4",
        register_relation="guitar occupies low-mid strumming range under vocal chest register",
        dynamic_relation="accompaniment 18% quieter than melody",
        mood="casual and warm",
        tension_level="low",
        description="Gentle strums stabilize harmony while keeping enough negative space for lyric detail.",
        example_song="Ed Sheeran - Photograph",
    ),
    rec(
        name="acoustic_strum_under_vocal_chorus_country",
        style="country_pop",
        section_type="chorus",
        melody_instrument="vocal",
        accomp_instrument="acoustic_guitar",
        relationship="rhythmic_unison",
        rhythm_relation="bigger open strums align with chorus lyric accents and backbeat",
        register_relation="guitar mids broaden under vocal while upper harmonics sit below sibilance zone",
        dynamic_relation="accompaniment 8-12% quieter than melody",
        mood="open-road uplift",
        tension_level="medium",
        description="Wide strumming and accent alignment make chorus feel communal and singalong-ready.",
        example_song="Lady A - Need You Now",
    ),
    rec(
        name="fingerstyle_guitar_under_vocal_verse_folk",
        style="folk",
        section_type="verse",
        melody_instrument="vocal",
        accomp_instrument="acoustic_guitar",
        relationship="rhythmic_complement",
        rhythm_relation="thumb alternates bass roots while fingers fill offbeats around vocal syllables",
        register_relation="bass notes two octaves below melody, treble plucks one octave below",
        dynamic_relation="accompaniment 20% quieter than melody",
        mood="earthy and intimate",
        tension_level="low",
        description="Fingerstyle pattern creates independent pulse and subtle motion around a narrative vocal line.",
        example_song="The Lumineers - Cleopatra",
    ),
    rec(
        name="fingerstyle_guitar_under_vocal_bridge_indie",
        style="indie_folk",
        section_type="bridge",
        melody_instrument="vocal",
        accomp_instrument="acoustic_guitar",
        relationship="call_response",
        rhythm_relation="vocal phrase endings leave rests for short high-string reply motifs",
        register_relation="response motifs rise into upper guitar register while vocal stays mid-high",
        dynamic_relation="accompaniment 15-20% quieter than melody",
        mood="fragile and exposed",
        tension_level="medium",
        description="Bridge call-response gives conversational contour before returning to full chorus texture.",
        example_song="Bon Iver - Skinny Love",
    ),
    rec(
        name="clean_electric_arpeggio_under_vocal_chorus_indie",
        style="indie_pop",
        section_type="chorus",
        melody_instrument="vocal",
        accomp_instrument="electric_guitar_clean",
        relationship="rhythmic_ostinato",
        rhythm_relation="syncopated eighth-note arpeggio loop repeats beneath sustained chorus vocal notes",
        register_relation="arpeggio sits in high-mid register, one octave below vocal peaks",
        dynamic_relation="accompaniment 12-15% quieter than melody with bright transient",
        mood="shimmering and forward",
        tension_level="medium",
        description="Repeating clean-guitar figure adds drive and sparkle while vocal carries thematic focus.",
        example_song="The 1975 - Somebody Else",
    ),
    rec(
        name="nylon_bossa_comp_under_vocal_verse_jazz",
        style="jazz_bossa",
        section_type="verse",
        melody_instrument="vocal",
        accomp_instrument="nylon_guitar",
        relationship="rhythmic_complement",
        rhythm_relation="anticipated chord attacks on offbeats complement laid-back vocal phrasing",
        register_relation="mid register chord shells under airy vocal top line",
        dynamic_relation="accompaniment 18% quieter than melody",
        mood="cool and fluid",
        tension_level="low",
        description="Bossa comping pattern supports harmony and groove while letting vocal float over the pulse.",
        example_song="Stan Getz & Joao Gilberto - The Girl from Ipanema",
    ),
    rec(
        name="palm_muted_guitar_under_vocal_verse_poprock",
        style="pop_rock",
        section_type="verse",
        melody_instrument="vocal",
        accomp_instrument="electric_guitar_muted",
        relationship="textural_fill",
        rhythm_relation="muted sixteenth-note chugs fill subdivisions between vocal accents",
        register_relation="guitar stays low-mid to avoid conflict with vocal intelligibility band",
        dynamic_relation="accompaniment 20% quieter than melody",
        mood="contained tension",
        tension_level="medium",
        description="Palm-muted texture thickens rhythm bed while preserving verse restraint.",
        example_song="Maroon 5 - She Will Be Loved (band arrangement style)",
    ),
    rec(
        name="wide_open_strum_under_vocal_chorus_rock",
        style="rock",
        section_type="chorus",
        melody_instrument="vocal",
        accomp_instrument="electric_guitar_rhythm",
        relationship="harmonic_support",
        rhythm_relation="open power-chord strums reinforce backbeat and sustain between lyric hooks",
        register_relation="rhythm guitar in mid-low register beneath high vocal belt",
        dynamic_relation="accompaniment 10% quieter than melody but with wider stereo image",
        mood="energetic and bold",
        tension_level="high",
        description="Open-chord rhythm guitar broadens chorus and creates heavier harmonic scaffolding.",
        example_song="Paramore - Still Into You",
    ),
    # Vocal + Strings
    rec(
        name="strings_pad_under_vocal_verse_ballad",
        style="cinematic_pop",
        section_type="verse",
        melody_instrument="vocal",
        accomp_instrument="strings_ensemble",
        relationship="sustained_pad",
        rhythm_relation="long legato string chords hold through full vocal lines",
        register_relation="violas/cellos below vocal, violins lightly above in low dynamics",
        dynamic_relation="accompaniment 20-25% quieter than melody",
        mood="tender and cinematic",
        tension_level="low",
        description="Sustained strings provide emotional bed and glue harmony without rhythmic competition.",
        example_song="Christina Perri - A Thousand Years",
    ),
    rec(
        name="strings_counterline_against_vocal_chorus_cinematic",
        style="cinematic_pop",
        section_type="chorus",
        melody_instrument="vocal",
        accomp_instrument="strings_ensemble",
        relationship="countermelody",
        rhythm_relation="violins weave shorter counter-phrases between held vocal notes",
        register_relation="counterline 3rd-6th above vocal center with careful avoidance of lyric peaks",
        dynamic_relation="accompaniment 12-18% quieter than melody",
        mood="expansive and dramatic",
        tension_level="high",
        description="Countermelodic strings expand chorus width while preserving main vocal identity.",
        example_song="Muse - Exogenesis motifs in pop context",
    ),
    rec(
        name="strings_unison_with_vocal_chorus_pop",
        style="orchestral_pop",
        section_type="chorus",
        melody_instrument="vocal",
        accomp_instrument="strings_ensemble",
        relationship="doubling",
        rhythm_relation="violins double hook rhythm at phrase starts then release to sustains",
        register_relation="unison or octave-above doubling focused on hook notes only",
        dynamic_relation="accompaniment 8-12% quieter than melody",
        mood="anthemic and polished",
        tension_level="high",
        description="Selective string doubling increases chorus memorability and perceived size.",
        example_song="Sia - Chandelier (live orchestral arrangements)",
    ),
    rec(
        name="strings_call_response_vocal_bridge",
        style="film_ballad",
        section_type="bridge",
        melody_instrument="vocal",
        accomp_instrument="strings_ensemble",
        relationship="call_response",
        rhythm_relation="short string swells answer end of each vocal sentence",
        register_relation="responses in upper strings while vocal remains center-high",
        dynamic_relation="accompaniment 15-20% quieter than melody",
        mood="questioning and dramatic",
        tension_level="medium",
        description="Bridge dialogue between voice and strings creates narrative turn before final refrain.",
        example_song="James Newton Howard style ballad bridges",
    ),
    rec(
        name="strings_pizzicato_under_vocal_verse_chamberpop",
        style="chamber_pop",
        section_type="verse",
        melody_instrument="vocal",
        accomp_instrument="strings_pizzicato",
        relationship="rhythmic_ostinato",
        rhythm_relation="pizzicato quarter-eighth ostinato supports speech-like lyric rhythm",
        register_relation="cello pizz roots low, viola/violin pizz mid register",
        dynamic_relation="accompaniment 18% quieter than melody",
        mood="playful and articulate",
        tension_level="medium",
        description="Pizzicato ostinato gives pointillistic motion and keeps verse transparent.",
        example_song="Regina Spektor chamber-pop arrangements",
    ),
    rec(
        name="strings_swell_under_vocal_chorus_ballad",
        style="power_ballad",
        section_type="chorus",
        melody_instrument="vocal",
        accomp_instrument="strings_ensemble",
        relationship="sustained_pad",
        rhythm_relation="crescendo swells follow bar-level harmony changes under long vocal belts",
        register_relation="full strings span from bass octave to airy high violins below vocal top",
        dynamic_relation="accompaniment 10-15% quieter than melody, rising at phrase peaks",
        mood="soaring and emotional",
        tension_level="high",
        description="Layered string swells raise emotional contour and smooth harmonic transitions in big choruses.",
        example_song="Celine Dion - My Heart Will Go On",
    ),
    # Vocal + Synth Pad
    rec(
        name="synth_pad_under_vocal_verse_edmpop",
        style="edm_pop",
        section_type="verse",
        melody_instrument="vocal",
        accomp_instrument="synth_pad",
        relationship="sustained_pad",
        rhythm_relation="slow pad chords held over 1-2 bars with minimal rhythmic motion",
        register_relation="pad centered below vocal formant range around low-mid frequencies",
        dynamic_relation="accompaniment 20% quieter than melody",
        mood="floating and modern",
        tension_level="low",
        description="Minimal pad support keeps verse spacious and prepares later rhythmic buildup.",
        example_song="Zedd & Alessia Cara - Stay",
    ),
    rec(
        name="sidechained_pad_under_vocal_chorus_edm",
        style="edm",
        section_type="chorus",
        melody_instrument="vocal",
        accomp_instrument="synth_pad",
        relationship="rhythmic_complement",
        rhythm_relation="pad ducks on every kick creating pump that leaves pocket for vocal attack",
        register_relation="wide stereo pad in mid band while vocal occupies mono center high-mid",
        dynamic_relation="accompaniment 10-15% quieter than melody after sidechain gain reduction",
        mood="euphoric and driving",
        tension_level="high",
        description="Kick-triggered pad pumping adds kinetic energy without colliding with vocal onsets.",
        example_song="Avicii - Wake Me Up (EDM chorus texture)",
    ),
    rec(
        name="airy_pad_under_vocal_bridge_ambient",
        style="ambient_pop",
        section_type="bridge",
        melody_instrument="vocal",
        accomp_instrument="synth_pad",
        relationship="textural_fill",
        rhythm_relation="very slow attack pads bloom between lyric phrases",
        register_relation="high airy pad above melody with low-cut filtering",
        dynamic_relation="accompaniment 25-30% quieter than melody",
        mood="dreamy and suspended",
        tension_level="low",
        description="Bridge uses texture-first pad motion to create breath and contrast before final lift.",
        example_song="Lorde - Liability (ambient remix style)",
    ),
    rec(
        name="retro_poly_pad_under_vocal_chorus_synthwave",
        style="synthwave",
        section_type="chorus",
        melody_instrument="vocal",
        accomp_instrument="poly_synth_pad",
        relationship="harmonic_support",
        rhythm_relation="straight quarter-note chord re-articulation supports steady vocal hook",
        register_relation="pad spans mid-high range one octave below and above vocal center",
        dynamic_relation="accompaniment 12% quieter than melody",
        mood="nostalgic and glossy",
        tension_level="medium",
        description="Retro poly-pad chords frame chorus harmony while maintaining 80s-inspired width.",
        example_song="The Weeknd - Blinding Lights",
    ),
    rec(
        name="dark_pad_under_vocal_verse_altrnb",
        style="alt_rnb",
        section_type="verse",
        melody_instrument="vocal",
        accomp_instrument="synth_pad",
        relationship="sustained_pad",
        rhythm_relation="subtle evolving pad under sparse vocal phrasing and delayed ad-libs",
        register_relation="pad mostly below melody with muted top harmonics",
        dynamic_relation="accompaniment 22% quieter than melody",
        mood="moody and nocturnal",
        tension_level="medium",
        description="Dark sustained pad keeps harmonic gravity and emotional depth in minimalist verses.",
        example_song="The Weeknd - Call Out My Name",
    ),
    # Melody + Bass (root follow / walking / groove lock)
    rec(
        name="vocal_melody_root_follow_bass_pop",
        style="pop",
        section_type="general",
        melody_instrument="vocal",
        accomp_instrument="bass_guitar",
        relationship="bass_foundation",
        rhythm_relation="bass emphasizes chord roots on strong beats under vocal contour",
        register_relation="bass remains 2 octaves below melody across sections",
        dynamic_relation="accompaniment 12-18% quieter than melody",
        mood="grounded and stable",
        tension_level="low",
        description="Root-led bass gives tonal certainty and supports singable top-line melodies.",
        example_song="Imagine Dragons - Demons",
    ),
    rec(
        name="sax_melody_walking_bass_jazz",
        style="jazz",
        section_type="general",
        melody_instrument="tenor_sax",
        accomp_instrument="upright_bass",
        relationship="countermelody",
        rhythm_relation="walking bass quarter notes create independent linear motion under sax phrases",
        register_relation="bass stays low register with occasional upper approach tones",
        dynamic_relation="accompaniment 15% quieter than melody soloist",
        mood="swinging and conversational",
        tension_level="medium",
        description="Walking bass functions as harmonic engine and contrapuntal partner to melodic improvisation.",
        example_song="Miles Davis - So What (acoustic bass role)",
    ),
    rec(
        name="lead_synth_melody_subbass_lock_edm",
        style="edm",
        section_type="chorus",
        melody_instrument="lead_synth",
        accomp_instrument="sub_bass",
        relationship="rhythmic_unison",
        rhythm_relation="sub bass follows key lead rhythm accents on downbeats and syncopated pickups",
        register_relation="sub anchors low octave while lead occupies upper-mid spectral zone",
        dynamic_relation="accompaniment at near-equal RMS but 5% lower peak than melody",
        mood="massive and energetic",
        tension_level="high",
        description="Rhythmic lock between lead and sub creates drop impact and dancefloor clarity.",
        example_song="Martin Garrix - Animals",
    ),
    rec(
        name="guitar_melody_syncopated_bass_funk",
        style="funk",
        section_type="general",
        melody_instrument="electric_guitar_lead",
        accomp_instrument="electric_bass",
        relationship="rhythmic_complement",
        rhythm_relation="bass anticipates upbeats while melody lands on backbeat accents",
        register_relation="bass in low register, guitar melody in high-mid with wah articulation",
        dynamic_relation="accompaniment 5-10% quieter than melody during hooks",
        mood="groovy and tight",
        tension_level="medium",
        description="Interlocking syncopation between lead guitar and bass defines funk pocket.",
        example_song="Jamiroquai - Canned Heat",
    ),
    rec(
        name="piano_melody_pedal_bass_cinematic",
        style="cinematic",
        section_type="general",
        melody_instrument="piano",
        accomp_instrument="low_strings_bass",
        relationship="bass_foundation",
        rhythm_relation="pedal bass holds tonic under slow-changing piano melody",
        register_relation="bass drone 2-3 octaves below melody line",
        dynamic_relation="accompaniment 20% quieter than melody",
        mood="solemn and expansive",
        tension_level="medium",
        description="Pedal foundation creates continuity while melody and harmony evolve overhead.",
        example_song="Hans Zimmer - Time (texture principle)",
    ),
    rec(
        name="trumpet_melody_counter_bass_latinjazz",
        style="latin_jazz",
        section_type="general",
        melody_instrument="trumpet",
        accomp_instrument="upright_bass",
        relationship="countermelody",
        rhythm_relation="bass tumbao-like syncopation answers melodic rests and anticipates chord movement",
        register_relation="bass low register, trumpet high register with wide vertical spacing",
        dynamic_relation="accompaniment 10-15% quieter than melody",
        mood="agile and bright",
        tension_level="high",
        description="Counter-moving bass line keeps groove and harmonic pull under horn melody statements.",
        example_song="Arturo Sandoval latin-jazz ensemble settings",
    ),
    rec(
        name="vocal_melody_groove_locked_bass_rnb",
        style="rnb",
        section_type="chorus",
        melody_instrument="vocal",
        accomp_instrument="electric_bass",
        relationship="rhythmic_unison",
        rhythm_relation="bass locks with key vocal rhythm motifs at phrase onsets",
        register_relation="bass sits low-mid while vocal riff occupies upper-mid",
        dynamic_relation="accompaniment 10-12% quieter than melody",
        mood="confident and sensual",
        tension_level="medium",
        description="Groove-locked bass doubles hook rhythm selectively to reinforce memorability.",
        example_song="Dua Lipa - Don't Start Now",
    ),
    # Melody + Drums
    rec(
        name="vocal_melody_backbeat_drums_pop",
        style="pop",
        section_type="general",
        melody_instrument="vocal",
        accomp_instrument="drum_kit",
        relationship="rhythmic_complement",
        rhythm_relation="drums keep steady backbeat while vocal uses syncopated pickups and ties",
        register_relation="drums are non-pitched; snare emphasis supports melody stress points",
        dynamic_relation="accompaniment 8-15% quieter than lead vocal average",
        mood="steady and clear",
        tension_level="medium",
        description="Backbeat framework lets vocal rhythm move freely while preserving listener orientation.",
        example_song="Taylor Swift - Anti-Hero",
    ),
    rec(
        name="rap_melody_kick_lock_drums_trap",
        style="trap",
        section_type="verse",
        melody_instrument="rap_vocal",
        accomp_instrument="trap_drums",
        relationship="rhythmic_unison",
        rhythm_relation="kick placements align with key rap syllabic accents and pauses",
        register_relation="808 and kick low, vocal center-mid with transient-focused presence",
        dynamic_relation="accompaniment near-equal level with vocal, but kick transient controlled",
        mood="urgent and punchy",
        tension_level="high",
        description="Kick-vocal alignment sharpens cadence and gives trap verses percussive articulation.",
        example_song="Travis Scott - SICKO MODE",
    ),
    rec(
        name="lead_synth_melody_four_on_floor_edm",
        style="edm",
        section_type="chorus",
        melody_instrument="lead_synth",
        accomp_instrument="edm_drums",
        relationship="rhythmic_unison",
        rhythm_relation="lead attack points align to kick grid while snare marks phrase midpoints",
        register_relation="drums occupy low/high transient bands, lead in upper-mid body",
        dynamic_relation="accompaniment and melody near parity, lead 5% louder at hooks",
        mood="driving and ecstatic",
        tension_level="high",
        description="Kick-grid alignment between melody and drums maximizes drop coherence and impact.",
        example_song="Calvin Harris - Summer",
    ),
    rec(
        name="guitar_melody_snare_response_rock",
        style="rock",
        section_type="bridge",
        melody_instrument="electric_guitar_lead",
        accomp_instrument="drum_kit",
        relationship="call_response",
        rhythm_relation="lead phrase endings answered by tom/snare fills every two bars",
        register_relation="non-pitched fills stay out of guitar frequency center by using tom tuning spread",
        dynamic_relation="accompaniment equal at fill hits then drops below lead",
        mood="aggressive transition",
        tension_level="high",
        description="Bridge call-response between lead guitar and fills creates momentum toward final section.",
        example_song="Foo Fighters bridge arrangements",
    ),
    rec(
        name="piano_melody_brush_swing_jazz",
        style="jazz_ballad",
        section_type="general",
        melody_instrument="piano",
        accomp_instrument="brush_drums",
        relationship="rhythmic_complement",
        rhythm_relation="brushes outline triplet pulse while piano melody floats rubato over bar lines",
        register_relation="drums non-pitched texture supports mid-high piano singing register",
        dynamic_relation="accompaniment 20% quieter than melody",
        mood="late-night and elegant",
        tension_level="low",
        description="Brush texture supplies subtle swing reference without constraining melodic rubato.",
        example_song="Bill Evans Trio ballad style",
    ),
    rec(
        name="string_melody_taiko_hits_cinematic",
        style="trailer",
        section_type="chorus",
        melody_instrument="strings_high",
        accomp_instrument="cinematic_drums",
        relationship="rhythmic_unison",
        rhythm_relation="melody rhythm reinforced by taiko downbeat hits in 2-bar cycles",
        register_relation="drums low and wide, melody high and piercing for contrast",
        dynamic_relation="accompaniment equal or slightly louder during impact accents",
        mood="heroic and intense",
        tension_level="high",
        description="Impact-oriented unison accents tie melodic motif to large cinematic pulse.",
        example_song="Two Steps From Hell style cues",
    ),
    rec(
        name="flute_melody_perc_ostinato_world",
        style="world_fusion",
        section_type="general",
        melody_instrument="flute",
        accomp_instrument="hand_percussion",
        relationship="rhythmic_ostinato",
        rhythm_relation="frame drum and shaker loop repeats while flute plays longer modal phrases",
        register_relation="percussion broadband low-mid; flute occupies upper-mid band",
        dynamic_relation="accompaniment 15% quieter than melody",
        mood="earthy and hypnotic",
        tension_level="medium",
        description="Percussion ostinato establishes trance-like pulse for free melodic ornamentation.",
        example_song="Anoushka Shankar fusion arrangements",
    ),
    # Lead + Rhythm Guitar
    rec(
        name="lead_guitar_with_rhythm_powerchords_rock",
        style="rock",
        section_type="chorus",
        melody_instrument="electric_guitar_lead",
        accomp_instrument="electric_guitar_rhythm",
        relationship="harmonic_support",
        rhythm_relation="rhythm guitar sustains power chords while lead states hook melody",
        register_relation="rhythm guitar low-mid, lead one octave above center",
        dynamic_relation="accompaniment 10% quieter than lead",
        mood="strong and direct",
        tension_level="high",
        description="Classic lead-rhythm split where harmonic bed supports melodic riffs in chorus.",
        example_song="Bon Jovi - Livin' on a Prayer",
    ),
    rec(
        name="lead_guitar_with_funk_chank_rhythm",
        style="funk",
        section_type="verse",
        melody_instrument="electric_guitar_lead",
        accomp_instrument="electric_guitar_rhythm",
        relationship="rhythmic_complement",
        rhythm_relation="muted 16th chanks on rhythm guitar leave pockets for lead lick placements",
        register_relation="rhythm comp in mid register; lead higher with sharper attack",
        dynamic_relation="accompaniment 12-18% quieter than lead phrases",
        mood="tight and danceable",
        tension_level="medium",
        description="Complementary subdivision roles prevent masking and increase groove precision.",
        example_song="Prince band arrangements",
    ),
    rec(
        name="lead_guitar_with_arpeggio_rhythm_indie",
        style="indie_rock",
        section_type="bridge",
        melody_instrument="electric_guitar_lead",
        accomp_instrument="electric_guitar_rhythm_clean",
        relationship="textural_fill",
        rhythm_relation="rhythm guitar arpeggiates triads in gaps around sustained lead notes",
        register_relation="rhythm slightly lower and wider stereo, lead centered and brighter",
        dynamic_relation="accompaniment 15% quieter than lead",
        mood="atmospheric and searching",
        tension_level="medium",
        description="Arpeggiated rhythm layer fills harmonic texture while lead retains melodic spotlight.",
        example_song="U2 - Where the Streets Have No Name (guitar layering approach)",
    ),
    rec(
        name="lead_guitar_octave_doubled_rhythm_metal",
        style="metal",
        section_type="chorus",
        melody_instrument="electric_guitar_lead",
        accomp_instrument="electric_guitar_rhythm",
        relationship="doubling",
        rhythm_relation="rhythm guitar doubles selected lead motif in lower octave on key hits",
        register_relation="doubling one octave below lead plus palm-muted low-string reinforcement",
        dynamic_relation="accompaniment near-equal level with lead in heavy sections",
        mood="powerful and aggressive",
        tension_level="high",
        description="Octave doubling thickens melodic riff and helps translation in dense distorted mixes.",
        example_song="Metallica harmonized riff sections",
    ),
    # Piano + Strings
    rec(
        name="piano_melody_strings_pad_cinematic",
        style="cinematic",
        section_type="general",
        melody_instrument="piano",
        accomp_instrument="strings_ensemble",
        relationship="sustained_pad",
        rhythm_relation="piano states motif while strings hold long harmony tones underneath",
        register_relation="strings mainly below piano right hand with high violin sheen at phrase ends",
        dynamic_relation="accompaniment 18% quieter than piano melody",
        mood="lyrical and expansive",
        tension_level="low",
        description="Sustained strings support piano narrative line and smooth harmonic continuity.",
        example_song="Yiruma-style piano with orchestral backing",
    ),
    rec(
        name="piano_chords_strings_counterline_romantic",
        style="romantic_orchestral",
        section_type="bridge",
        melody_instrument="piano",
        accomp_instrument="strings_ensemble",
        relationship="countermelody",
        rhythm_relation="left-hand piano chords pulse on beats while violins draw lyrical counterline",
        register_relation="counterline above piano melody by a third to an octave",
        dynamic_relation="accompaniment 10-15% quieter than piano thematic line",
        mood="yearning and expressive",
        tension_level="medium",
        description="Countermelodic strings enrich harmonic narrative and lift bridge emotional arc.",
        example_song="Rachmaninoff-inspired crossover ballad textures",
    ),
    rec(
        name="piano_hook_strings_unison_popballad",
        style="pop_ballad",
        section_type="chorus",
        melody_instrument="piano",
        accomp_instrument="strings_ensemble",
        relationship="doubling",
        rhythm_relation="strings double piano hook rhythm in legato bowing with slight delay",
        register_relation="doubling at unison and upper octave around hook apex",
        dynamic_relation="accompaniment 8-12% quieter than piano hook",
        mood="romantic and grand",
        tension_level="high",
        description="Unison doubling helps piano hook project like a vocal refrain in orchestral pop.",
        example_song="David Foster style power ballads",
    ),
    rec(
        name="piano_ostinato_strings_stabs_trailer",
        style="hybrid_trailer",
        section_type="chorus",
        melody_instrument="piano",
        accomp_instrument="strings_staccato",
        relationship="rhythmic_ostinato",
        rhythm_relation="piano ostinato repeats sixteenth grid while strings accent every second beat",
        register_relation="ostinato mid register, string stabs low and high split for width",
        dynamic_relation="accompaniment near-equal with melody for impact moments",
        mood="tense and propulsive",
        tension_level="high",
        description="Hybrid trailer texture uses ostinato repetition plus orchestral accents for momentum.",
        example_song="Audiomachine hybrid cue style",
    ),
    # Style-specific pairings
    rec(
        name="jazz_horn_with_piano_comping_general",
        style="jazz",
        section_type="general",
        melody_instrument="horn_section",
        accomp_instrument="piano",
        relationship="harmonic_support",
        rhythm_relation="piano comping shells on offbeats support syncopated horn melody phrasing",
        register_relation="comping in mid register below horn lead lines",
        dynamic_relation="accompaniment 15% quieter than horns",
        mood="swinging and sophisticated",
        tension_level="medium",
        description="Piano comping voices guide harmonic motion and leave rhythmic air for horn articulation.",
        example_song="Count Basie big band comping practice",
    ),
    rec(
        name="jazz_horn_with_piano_response_hits",
        style="jazz_bigband",
        section_type="bridge",
        melody_instrument="trumpet_lead",
        accomp_instrument="piano",
        relationship="call_response",
        rhythm_relation="short piano comp hits answer trumpet lines in 2-bar exchanges",
        register_relation="piano chords in middle register, trumpet lead above staff",
        dynamic_relation="accompaniment 12-18% quieter than lead horn",
        mood="playful and conversational",
        tension_level="medium",
        description="Alternating melodic calls and comp responses sharpen phrasing and ensemble dialogue.",
        example_song="Duke Ellington arrangement techniques",
    ),
    rec(
        name="edm_lead_synth_with_arp_pluck_drop",
        style="edm",
        section_type="chorus",
        melody_instrument="lead_synth",
        accomp_instrument="arp_pluck",
        relationship="rhythmic_ostinato",
        rhythm_relation="high-rate arpeggiator repeats 1/16 pattern under sustained lead notes",
        register_relation="arp one octave above lead, filtered to avoid harsh masking",
        dynamic_relation="accompaniment 10-15% quieter than lead",
        mood="bright and energetic",
        tension_level="high",
        description="Arp pluck ostinato supplies motion and sparkle that frames drop melody.",
        example_song="Swedish House Mafia style drops",
    ),
    rec(
        name="edm_lead_synth_with_stack_layer",
        style="future_bass",
        section_type="chorus",
        melody_instrument="lead_synth",
        accomp_instrument="supersaw_stack",
        relationship="doubling",
        rhythm_relation="stack layer doubles lead rhythm with wider voicing and slower attack",
        register_relation="double at unison plus octave-above shimmer layer",
        dynamic_relation="accompaniment near-equal level but with lower transient edge than lead",
        mood="massive and euphoric",
        tension_level="high",
        description="Layered supersaw doubling enlarges drop hooks while preserving lead articulation.",
        example_song="Illenium melodic bass arrangements",
    ),
    rec(
        name="latin_flute_with_piano_montuno",
        style="latin",
        section_type="general",
        melody_instrument="flute",
        accomp_instrument="piano",
        relationship="rhythmic_complement",
        rhythm_relation="piano montuno syncopation interlocks around flute phrase starts and rests",
        register_relation="montuno in mid register, flute melody above one octave",
        dynamic_relation="accompaniment 12-18% quieter than flute",
        mood="bright and danceable",
        tension_level="medium",
        description="Montuno pattern provides clave-aligned grid while flute carries lyrical contour.",
        example_song="Buena Vista Social Club latin piano approach",
    ),
    rec(
        name="lofi_keys_with_guitar_texture",
        style="lofi",
        section_type="general",
        melody_instrument="electric_piano",
        accomp_instrument="electric_guitar_clean",
        relationship="textural_fill",
        rhythm_relation="lazy swung guitar swells fill spaces between simple key melody notes",
        register_relation="guitar high-mid haze above key melody but low-passed",
        dynamic_relation="accompaniment 20% quieter than melody",
        mood="nostalgic and mellow",
        tension_level="low",
        description="Soft guitar texture adds width and movement around minimal lo-fi keyboard lead.",
        example_song="lofi study beat arrangement conventions",
    ),
    rec(
        name="afrobeats_vocal_with_guitar_pluck",
        style="afrobeats",
        section_type="verse",
        melody_instrument="vocal",
        accomp_instrument="electric_guitar_highlife",
        relationship="call_response",
        rhythm_relation="short guitar plucks answer each vocal phrase on offbeats",
        register_relation="guitar upper-mid register, vocal center-mid",
        dynamic_relation="accompaniment 15-20% quieter than melody",
        mood="bouncy and conversational",
        tension_level="medium",
        description="Highlife-inspired guitar replies create elastic groove around vocal topline.",
        example_song="Wizkid afrobeats arrangement style",
    ),
    rec(
        name="kpop_vocal_with_synth_stabs_chorus",
        style="kpop",
        section_type="chorus",
        melody_instrument="vocal",
        accomp_instrument="synth_stabs",
        relationship="rhythmic_unison",
        rhythm_relation="stacked synth stabs hit exactly with chant-like vocal hook rhythm",
        register_relation="stabs mid-high, vocal center-high with layered doubles",
        dynamic_relation="accompaniment near-equal during hook accents",
        mood="bold and catchy",
        tension_level="high",
        description="Unison stab-hook writing reinforces rhythmic identity in high-energy choruses.",
        example_song="TWICE chorus production style",
    ),
]


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def tokenize(text: str) -> list[str]:
    return [
        token
        for token in re.findall(r"[a-z0-9_+#]+", normalize(text))
        if len(token) > 2 and token not in STOP_TOKENS
    ]


def load_reference_results(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing reference file: {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("Reference JSON must be a list.")
    refs: list[dict[str, str]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        refs.append(
            {
                "title": str(item.get("title", "")),
                "url": str(item.get("url", "")),
                "description": str(item.get("description", "")),
                "page_excerpt": str(item.get("page_excerpt", "")),
            }
        )
    return refs


def pick_reference_url(pattern: dict[str, str], refs: list[dict[str, str]]) -> str:
    if not refs:
        return ""
    tokens = set(
        tokenize(
            " ".join(
                [
                    pattern["style"],
                    pattern["melody_instrument"],
                    pattern["accomp_instrument"],
                    pattern["name"],
                    pattern["relationship"],
                ]
            )
        )
    )
    tokens.update(RELATIONSHIP_HINTS.get(pattern["relationship"], ()))

    best_score = -1
    best_url = ""
    for ref in refs:
        corpus = normalize(" ".join([ref["title"], ref["description"], ref["page_excerpt"]]))
        score = 0
        for token in tokens:
            if token in corpus:
                score += 1
        if ref["url"] and score > best_score:
            best_score = score
            best_url = ref["url"]
    if best_url:
        return best_url
    for ref in refs:
        if ref["url"]:
            return ref["url"]
    return ""


def validate_patterns(rows: list[dict[str, str]]) -> None:
    if len(rows) < 40:
        raise ValueError(f"Need at least 40 patterns, got {len(rows)}")

    seen_names: set[str] = set()
    for row in rows:
        name = row["name"]
        if name in seen_names:
            raise ValueError(f"Duplicate pattern name: {name}")
        seen_names.add(name)

        if row["relationship"] not in ALLOWED_RELATIONSHIPS:
            raise ValueError(f"Invalid relationship in {name}: {row['relationship']}")
        if row["section_type"] not in ALLOWED_SECTION_TYPES:
            raise ValueError(f"Invalid section_type in {name}: {row['section_type']}")
        if row["tension_level"] not in ALLOWED_TENSION:
            raise ValueError(f"Invalid tension_level in {name}: {row['tension_level']}")


def ensure_coverage(rows: list[dict[str, str]]) -> None:
    def has_pair(melody: str, accomp_contains: str) -> bool:
        return any(
            row["melody_instrument"] == melody and accomp_contains in row["accomp_instrument"]
            for row in rows
        )

    def has_name_contains(token: str, section: str | None = None) -> bool:
        return any(
            token in row["name"] and (section is None or row["section_type"] == section)
            for row in rows
        )

    checks = [
        (has_pair("vocal", "piano"), "Missing Vocal + Piano coverage"),
        (has_pair("vocal", "guitar"), "Missing Vocal + Guitar coverage"),
        (has_pair("vocal", "strings"), "Missing Vocal + Strings coverage"),
        (has_pair("vocal", "synth_pad"), "Missing Vocal + Synth Pad coverage"),
        (has_pair("vocal", "bass"), "Missing Melody + Bass coverage"),
        (has_pair("vocal", "drum"), "Missing Melody + Drums coverage"),
        (has_pair("electric_guitar_lead", "electric_guitar_rhythm"), "Missing Lead + Rhythm Guitar coverage"),
        (has_pair("piano", "strings"), "Missing Piano + Strings coverage"),
        (has_name_contains("jazz_horn_with_piano_comping"), "Missing jazz horn + piano comping coverage"),
        (has_name_contains("edm_lead_synth_with_arp"), "Missing EDM lead synth + arp coverage"),
        (has_name_contains("arpeggio", "verse"), "Missing verse arpeggio pattern"),
        (has_name_contains("arpeggio", "chorus"), "Missing chorus arpeggio pattern"),
        (has_name_contains("block_chords", "verse"), "Missing verse block chord pattern"),
        (has_name_contains("block_chords", "chorus"), "Missing chorus block chord pattern"),
        (has_name_contains("broken_chords", "verse"), "Missing verse broken chord pattern"),
        (has_name_contains("broken_chords", "chorus"), "Missing chorus broken chord pattern"),
    ]
    for passed, message in checks:
        if not passed:
            raise ValueError(message)


def build_rows(patterns: list[dict[str, str]], refs: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for pattern in patterns:
        source_url = pick_reference_url(pattern, refs)
        source = f"{SOURCE_PREFIX}:enriched|{source_url}" if source_url else f"{SOURCE_PREFIX}:manual"
        rows.append({**pattern, "source": source})
    return rows


def insert_rows(rows: list[dict[str, str]]) -> tuple[int, int]:
    init_db(DB_FILE)
    conn = sqlite3.connect(str(DB_FILE))
    c = conn.cursor()

    c.execute("DELETE FROM melody_accompaniment WHERE source LIKE ?", (f"{SOURCE_PREFIX}:%",))
    c.executemany(
        """
        INSERT INTO melody_accompaniment (
            name,
            style,
            section_type,
            melody_instrument,
            accomp_instrument,
            relationship,
            rhythm_relation,
            register_relation,
            dynamic_relation,
            mood,
            tension_level,
            description,
            example_song,
            source
        )
        VALUES (
            :name,
            :style,
            :section_type,
            :melody_instrument,
            :accomp_instrument,
            :relationship,
            :rhythm_relation,
            :register_relation,
            :dynamic_relation,
            :mood,
            :tension_level,
            :description,
            :example_song,
            :source
        )
        """,
        rows,
    )

    mine = c.execute(
        "SELECT COUNT(*) FROM melody_accompaniment WHERE source LIKE ?",
        (f"{SOURCE_PREFIX}:%",),
    ).fetchone()[0]
    total = c.execute("SELECT COUNT(*) FROM melody_accompaniment").fetchone()[0]
    conn.commit()
    conn.close()
    return int(mine), int(total)


def main() -> None:
    refs = load_reference_results(ENRICHED_JSON_PATH)
    validate_patterns(BASE_PATTERNS)
    ensure_coverage(BASE_PATTERNS)
    rows = build_rows(BASE_PATTERNS, refs)
    mine, total = insert_rows(rows)
    print(f"Inserted melody_accompaniment rows: {len(rows)}")
    print(f"{SOURCE_PREFIX} rows in table: {mine}")
    print(f"Total rows in melody_accompaniment: {total}")


if __name__ == "__main__":
    main()
