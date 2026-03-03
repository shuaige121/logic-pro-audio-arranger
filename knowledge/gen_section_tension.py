#!/usr/bin/env python3
"""Generate section arrangement patterns and tension-curve templates."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

try:
    from knowledge.init_db import DB_PATH, init_db
except ModuleNotFoundError:
    from init_db import DB_PATH, init_db  # type: ignore

SECTION_REF_PATH = Path(__file__).parent / "extracted" / "section_patterns_enriched.json"
TENSION_REF_PATH = Path(__file__).parent / "extracted" / "tension_energy_enriched.json"

ALLOWED_SECTION_TYPES = {
    "intro",
    "verse",
    "pre_chorus",
    "chorus",
    "bridge",
    "outro",
    "drop",
    "buildup",
    "breakdown",
    "solo",
    "interlude",
}
ALLOWED_STYLES = {"pop", "rock", "jazz", "rnb", "edm", "classical", "folk", "latin", "blues", "country", "general"}
ALLOWED_TEXTURE = {"thin", "medium", "thick", "very_thick"}
REQUIRED_CURVE_NAMES = {
    "classic_pop_arc",
    "rock_power_build",
    "ballad_emotional_arc",
    "edm_drop_cycle",
    "jazz_head_solo_head",
    "classical_sonata",
    "folk_storytelling",
    "rnb_groove_build",
    "blues_12bar_cycle",
    "latin_dance_energy",
    "country_verse_chorus",
    "anthem_epic_build",
    "minimal_ambient",
    "progressive_long_build",
    "hip_hop_verse_hook",
}

REQUIRED_SECTION_STYLE = {
    "intro": {"pop", "rock", "jazz", "edm", "classical", "folk"},
    "verse": {"pop", "rock", "jazz", "rnb", "edm", "folk", "country"},
    "pre_chorus": {"pop", "rock", "edm"},
    "chorus": {"pop", "rock", "rnb", "edm", "country"},
    "bridge": {"pop", "rock", "jazz", "rnb"},
    "outro": {"pop", "rock", "jazz", "edm"},
    "drop": {"edm"},
    "buildup": {"edm"},
    "breakdown": {"edm", "rock"},
    "solo": {"rock", "jazz", "blues"},
}


def normalize_space(text: str) -> str:
    return " ".join(str(text).split()).strip()


def load_reference_items(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, list):
        return []

    items: list[dict[str, str]] = []
    for entry in payload:
        if not isinstance(entry, dict):
            continue
        url = normalize_space(entry.get("url", ""))
        title = normalize_space(entry.get("title", ""))
        query = normalize_space(entry.get("query", ""))
        if url or title or query:
            items.append({"url": url, "title": title, "query": query})
    return items


def source_for(kind: str, refs: list[dict[str, str]], index: int) -> str:
    base = "generated:knowledge/gen_section_tension.py"
    if not refs:
        return f"{base}|{kind}|fallback"
    ref = refs[index % len(refs)]
    query = ref.get("query", "")
    url = ref.get("url", "")
    if query and url:
        return f"{base}|{kind}|q={query}|{url}"
    if url:
        return f"{base}|{kind}|{url}"
    if query:
        return f"{base}|{kind}|q={query}"
    return f"{base}|{kind}|fallback"


def sp(
    section_type: str,
    style: str,
    active_instruments: list[str],
    texture_density: str,
    energy_level: int,
    melody_treatment: str,
    harmony_treatment: str,
    rhythm_treatment: str,
    bass_treatment: str,
    transition_in: str,
    transition_out: str,
    mood_function: str,
    description: str,
) -> dict[str, Any]:
    return {
        "section_type": section_type,
        "style": style,
        "active_instruments": active_instruments,
        "texture_density": texture_density,
        "energy_level": str(energy_level),
        "melody_treatment": melody_treatment,
        "harmony_treatment": harmony_treatment,
        "rhythm_treatment": rhythm_treatment,
        "bass_treatment": bass_treatment,
        "transition_in": transition_in,
        "transition_out": transition_out,
        "mood_function": mood_function,
        "description": description,
        "source": "",
    }


def tc(
    name: str,
    style: str,
    structure: str,
    curve_data: dict[str, int],
    description: str,
    example_song: str,
) -> dict[str, Any]:
    return {
        "name": name,
        "style": style,
        "structure": structure,
        "curve_data": curve_data,
        "description": description,
        "example_song": example_song,
        "source": "",
    }


def build_section_patterns() -> list[dict[str, Any]]:
    patterns = [
        # intro
        sp(
            "intro",
            "pop",
            ["vocal", "piano", "synth_pad", "sub_bass", "drums"],
            "thin",
            3,
            "hook motif appears in short two-bar fragments",
            "simple I-V-vi-IV voicing with suspended color",
            "straight eighth pulse with light percussion loop",
            "long root notes with sidechain breathing",
            "fade-in pad and reversed cymbal swell",
            "snare pickup and riser into verse",
            "establish radio-friendly identity quickly",
            "Pop intro presents a recognizable melodic cell while keeping space for the vocal entry.",
        ),
        sp(
            "intro",
            "rock",
            ["electric_guitar", "bass", "drums", "organ"],
            "medium",
            4,
            "guitar riff states thematic contour without full melody",
            "power-chord pedal over tonic and flat-VII",
            "kick on downbeats with open-hat lift",
            "picked eighth-note pedal tone",
            "count-in with stick clicks and amp swell",
            "drum fill into full-band verse",
            "set attitude and groove confidence",
            "Rock intro uses riff-first writing so the song identity is clear before vocals enter.",
        ),
        sp(
            "intro",
            "jazz",
            ["piano", "upright_bass", "brush_drums", "tenor_sax"],
            "thin",
            3,
            "head motif hinted with rubato pickup",
            "extended tonic and ii-V turnaround",
            "light swing comping with brushes",
            "walking fragments then held pedal",
            "solo piano pickup and room ambience",
            "tempo settles with brush pickup",
            "introduce harmonic color and tone",
            "Jazz intro acts like a miniature preface, using rubato then settling into pulse for the head.",
        ),
        sp(
            "intro",
            "edm",
            ["synth_pad", "pluck", "fx_riser", "kick", "sub_bass"],
            "medium",
            4,
            "lead motif filtered and rhythmically simplified",
            "two-chord loop with low-pass automation",
            "four-on-floor ghost kick and uplifter noise",
            "sub enters late to reserve impact",
            "ambient downlifter tail from previous section",
            "snare roll and cutoff automation into verse/buildup",
            "set tonal center and dance context",
            "EDM intro focuses on frequency staging: filtered highs first, low-end introduced only near transition.",
        ),
        sp(
            "intro",
            "classical",
            ["strings", "woodwinds", "horn", "timpani", "harp"],
            "medium",
            3,
            "primary theme appears in unison then opens to counterline",
            "functional tonic preparation with dominant hint",
            "free tempo opening moving to clear meter",
            "celli and basses double tonic in octaves",
            "orchestral swell from silence",
            "cadential gesture into first statement",
            "frame narrative and thematic material",
            "Classical intro outlines thematic DNA and orchestral color before full formal exposition.",
        ),
        sp(
            "intro",
            "folk",
            ["acoustic_guitar", "mandolin", "upright_bass", "shaker"],
            "thin",
            2,
            "melody implied by guitar top notes",
            "open-position triads with drone fifths",
            "gentle strum pattern and sparse shaker",
            "bass enters after first phrase",
            "counted breath and pick noise kept audible",
            "strum accent into verse lyric",
            "create intimacy and storytelling focus",
            "Folk intro keeps arrangement honest and close, prioritizing lyric readiness over spectacle.",
        ),
        sp(
            "intro",
            "latin",
            ["nylon_guitar", "piano", "congas", "bass", "flute"],
            "medium",
            4,
            "flute answers a short rhythmic guitar idea",
            "minor tonic with secondary dominant turnaround",
            "clave-informed groove starts quietly",
            "anticipated bass pickups before barline",
            "percussion-only pickup with shaker",
            "fill from timbales into verse",
            "prepare danceable momentum",
            "Latin intro introduces groove vocabulary first so later vocal entries feel naturally embedded.",
        ),
        sp(
            "intro",
            "blues",
            ["electric_piano", "electric_guitar", "bass", "brush_drums", "harmonica"],
            "thin",
            3,
            "call-and-response licks foreshadow vocal phrasing",
            "I7-IV7 vamp with turnaround pickup",
            "laid-back shuffle with light snare ghosts",
            "root-fifth walk-ups at phrase ends",
            "guitar pickup slide and amp hum",
            "short drum fill to verse",
            "set earthy character and groove",
            "Blues intro works as a mood-setting vamp that leaves enough space for expressive vocal entrance.",
        ),
        # verse
        sp(
            "verse",
            "pop",
            ["vocal", "piano", "bass", "drums", "pad"],
            "medium",
            5,
            "lead vocal carries full lyric with restrained range",
            "diatonic loop with occasional add9 coloration",
            "tight backbeat and muted syncopation",
            "root and passing fifth approach notes",
            "strip-down from intro with kick entrance",
            "pre-chorus lift through rising snare pattern",
            "deliver story while preserving headroom",
            "Pop verse balances clarity and forward motion, keeping hooks subtle before chorus payoff.",
        ),
        sp(
            "verse",
            "rock",
            ["vocal", "electric_guitar", "bass", "drums"],
            "medium",
            6,
            "vocal melody follows riff contour in narrow tessitura",
            "riff-based harmony around tonic and subdominant",
            "driving eighth-note hats with backbeat emphasis",
            "locked with kick using octave jumps",
            "drop cymbals after intro for verse focus",
            "snare fill and rhythm guitar open chords to pre-chorus",
            "advance narrative with gritty momentum",
            "Rock verse keeps the band compact and punchy so the chorus can open wider.",
        ),
        sp(
            "verse",
            "jazz",
            ["vocal", "piano", "upright_bass", "drums", "guitar"],
            "medium",
            5,
            "melody ornamented with pickups and delayed resolutions",
            "ii-V-I chains with chromatic approach chords",
            "swing ride pulse with conversational comping",
            "walking bass outlines guide tones",
            "drums switch from brushes to sticks",
            "turnaround tag leads to pre-chorus/bridge",
            "deepen harmonic narrative",
            "Jazz verse uses harmonic movement to carry tension while leaving rhythmic freedom to the vocalist.",
        ),
        sp(
            "verse",
            "rnb",
            ["vocal", "electric_piano", "sub_bass", "drum_machine", "guitar"],
            "medium",
            5,
            "melismas placed at line endings only",
            "lush seventh chords with suspended reharmonization",
            "lazy pocket with swung sixteenth hats",
            "syncopated sub pattern with octave glides",
            "filtered intro drops into dry vocal",
            "riser and harmony stack into pre-chorus",
            "intimate storytelling and groove lock",
            "R&B verse emphasizes pocket and vocal nuance, letting harmony color emotional subtext.",
        ),
        sp(
            "verse",
            "edm",
            ["vocal", "pluck", "pad", "kick", "percussion", "bass"],
            "medium",
            5,
            "topline simplified to short rhythmic motifs",
            "two- or four-chord loop with gradual filter opening",
            "four-on-floor plus offbeat percussion",
            "sub kept restrained to preserve drop impact",
            "drums narrow to kick and clap",
            "snare roll and uplifter to buildup",
            "maintain dance continuity while setting up lift",
            "EDM verse keeps energy stable but controlled, reserving spectral width for later sections.",
        ),
        sp(
            "verse",
            "folk",
            ["vocal", "acoustic_guitar", "upright_bass", "fiddle", "percussion"],
            "thin",
            4,
            "speech-like melody with repeated anchor tones",
            "I-IV-V movement with modal inflections",
            "strum-driven pulse and occasional hand percussion",
            "simple roots with brief walk-up links",
            "intro instruments thin out for lyric focus",
            "added harmony vocal into chorus",
            "carry narrative detail",
            "Folk verse prioritizes diction and narrative pacing, with arrangement reacting to lyric cadence.",
        ),
        sp(
            "verse",
            "country",
            ["vocal", "acoustic_guitar", "electric_guitar", "bass", "drums", "pedal_steel"],
            "medium",
            5,
            "melody centers on chord tones and conversational rhythm",
            "I-V-vi-IV or I-IV-V with passing diminished links",
            "train-beat groove with light snare ghost notes",
            "two-beat roots and fifth approaches",
            "guitar lick pickup from intro",
            "snare fill and steel swell into chorus",
            "paint concrete lyrical scenes",
            "Country verse leans on hooky but singable shapes and clear harmonic grounding.",
        ),
        sp(
            "verse",
            "latin",
            ["vocal", "piano", "bass", "congas", "timbales", "guitar"],
            "medium",
            6,
            "melody uses syncopated anticipations against clave",
            "minor progression with dominant substitutions",
            "clave-locked percussion and montuno fragments",
            "tumbao pattern with chromatic approach",
            "percussion pattern opens up after intro",
            "timbales roll to pre-chorus",
            "build rhythmic excitement without over-dense texture",
            "Latin verse is rhythm-forward, with harmony and melody weaving around percussion architecture.",
        ),
        sp(
            "verse",
            "blues",
            ["vocal", "electric_guitar", "bass", "drums", "organ"],
            "medium",
            5,
            "call-and-response between vocal and guitar fills",
            "12-bar blues framework with dominant extensions",
            "shuffle groove and occasional stop-time accents",
            "walking bass in bars 9-12 turnaround",
            "riff intro drops to leave vocal room",
            "turnaround lick or drum break into chorus",
            "communicate tension and release in each stanza",
            "Blues verse uses phrase-end fills as structural punctuation, reinforcing emotional cadence.",
        ),
        # pre_chorus
        sp(
            "pre_chorus",
            "pop",
            ["vocal", "piano", "synth_pad", "bass", "drums"],
            "medium",
            6,
            "melody rises stepwise toward chorus peak note",
            "chords shift to vi-IV-I-V with increased harmonic rhythm",
            "kick pattern densifies and claps layer in",
            "ascending bass line over two bars",
            "subtle automation opens high frequencies",
            "drum fill and crash to chorus",
            "increase anticipation",
            "Pop pre-chorus narrows lyric density while expanding melodic lift to prime the chorus hit.",
        ),
        sp(
            "pre_chorus",
            "rock",
            ["vocal", "distorted_guitar", "bass", "drums", "synth_pad"],
            "thick",
            7,
            "melody pushes upward with longer sustained tones",
            "harmonic climb via secondary dominant motion",
            "toms and open hats build urgency",
            "eighth-note pedal then octave jump",
            "guitars open from palm-mute to full strum",
            "fill with cymbal choke before chorus",
            "drive momentum into release",
            "Rock pre-chorus uses density and register expansion to create a springboard into chorus.",
        ),
        sp(
            "pre_chorus",
            "edm",
            ["vocal", "arpeggiator", "snare_roll", "fx_riser", "bass"],
            "thick",
            7,
            "topline simplified to repeated hook fragment",
            "sustained chord stack with rising filter cutoff",
            "snare roll accelerates and noise sweep ascends",
            "sub pulses on quarter notes before mute",
            "drop percussion stripped then rebuilt",
            "hard stop or vocal chop into drop",
            "maximize suspense before drop",
            "EDM pre-chorus behaves as a controlled pressure chamber where rhythmic density rises before release.",
        ),
        sp(
            "pre_chorus",
            "rnb",
            ["vocal", "electric_piano", "synth_pad", "sub_bass", "drum_machine"],
            "medium",
            6,
            "stacked harmonies answer lead phrases",
            "extended chords with delayed tonic resolution",
            "snare accents increase and hats open slightly",
            "gliding sub connects chord roots",
            "verse groove thins to spotlight vocal stacks",
            "vocal run and cymbal swell into chorus",
            "heighten emotional pull",
            "R&B pre-chorus adds harmonic shimmer and vocal layering rather than brute force density.",
        ),
        sp(
            "pre_chorus",
            "country",
            ["vocal", "acoustic_guitar", "electric_guitar", "bass", "drums", "pedal_steel"],
            "medium",
            6,
            "melody climbs with longer held syllables",
            "IV-V-vi progression to delay tonic",
            "snare lift with tambourine reinforcement",
            "ascending fifth pattern toward chorus downbeat",
            "acoustic strum intensifies and steel swells",
            "band break then full chorus entry",
            "set up lyrical punchline",
            "Country pre-chorus shifts harmonic gravity away from tonic to frame a bigger chorus entrance.",
        ),
        # chorus
        sp(
            "chorus",
            "pop",
            ["lead_vocal", "backing_vocals", "synth", "piano", "bass", "drums"],
            "thick",
            8,
            "main hook in high tessitura with doubled octave support",
            "stable diatonic progression with bright extensions",
            "full backbeat and syncopated percussion",
            "root-octave movement with occasional passing tones",
            "pre-chorus cymbal swell and fill",
            "drop to verse via de-layering and pickup",
            "deliver peak memorability",
            "Pop chorus maximizes hook clarity, vocal layering, and frequency width for commercial impact.",
        ),
        sp(
            "chorus",
            "rock",
            ["lead_vocal", "guitar_wall", "bass", "drums", "backing_vocals"],
            "very_thick",
            9,
            "anthemic line doubled by guitars",
            "power-chord progression with dominant lift",
            "crash-driven groove and driving snare",
            "bass follows riff with octave punches",
            "pre-chorus tom build",
            "short tag riff or half-time break",
            "release accumulated drive",
            "Rock chorus increases saturation, width, and vocal unison to feel physically larger than verse.",
        ),
        sp(
            "chorus",
            "rnb",
            ["lead_vocal", "harmony_stack", "electric_piano", "synth_bass", "drum_machine"],
            "thick",
            8,
            "lead melody answered by stacked ad-libs",
            "lush chords with altered dominants resolving late",
            "deep pocket with syncopated claps",
            "sub-bass groove locks with kick pattern",
            "pre-chorus vocal run lands on chorus hook",
            "breakdown or verse return via filtered drums",
            "provide emotional release with groove continuity",
            "R&B chorus builds width through harmonies and sub movement while keeping rhythmic feel smooth.",
        ),
        sp(
            "chorus",
            "edm",
            ["lead_synth", "vocal_chop", "supersaw", "sub_bass", "kick", "clap"],
            "very_thick",
            9,
            "hook converted to lead synth or vocal chop motif",
            "looped progression with bright stacked voicings",
            "full four-on-floor plus offbeat layers",
            "sidechained sub and reese support",
            "pre-drop mute and impact hit",
            "breakdown via kick removal and filtered tail",
            "maximize dancefloor release",
            "EDM chorus/drop section is the principal payoff: full-spectrum arrangement and simple hook repetition.",
        ),
        sp(
            "chorus",
            "country",
            ["lead_vocal", "backing_vocals", "acoustic_guitar", "electric_guitar", "bass", "drums"],
            "thick",
            8,
            "hook lyric repeated with harmony thirds",
            "I-IV-V with suspended embellishments",
            "open hi-hat backbeat and tambourine",
            "steady roots with turnaround run-ups",
            "pre-chorus snare build",
            "instrumental tag back to verse",
            "deliver sing-along payoff",
            "Country chorus foregrounds lyric hook repetition and full-band resonance for audience participation.",
        ),
        sp(
            "chorus",
            "latin",
            ["lead_vocal", "choir", "piano", "bass", "congas", "horn_section"],
            "thick",
            8,
            "hook phrase alternates with horn responses",
            "cyclic minor progression with dominant pushes",
            "full clave groove with additional percussion",
            "tumbao line reinforced by bass guitar",
            "timbales build from pre-chorus",
            "percussion break into verse",
            "trigger dance-floor euphoria",
            "Latin chorus peaks by combining vocal chant energy with horn-and-percussion punches.",
        ),
        sp(
            "chorus",
            "blues",
            ["lead_vocal", "backing_vocals", "electric_guitar", "organ", "bass", "drums"],
            "thick",
            7,
            "short repeated refrain with shouted responses",
            "dominant-heavy progression with turnaround extension",
            "shuffle intensified with snare accents",
            "walking line thickened with octave doubles",
            "verse turnaround snaps into downbeat",
            "guitar fill into next verse/solo",
            "provide cathartic refrain",
            "Blues chorus tightens phrase length and increases ensemble response for communal release.",
        ),
        # bridge
        sp(
            "bridge",
            "pop",
            ["lead_vocal", "piano", "strings", "bass", "drums"],
            "medium",
            6,
            "new melodic contour avoids chorus hook interval",
            "modal mixture or relative-minor detour",
            "rhythm simplifies to half-time feel",
            "sustained pedal under changing chords",
            "chorus tail drops to sparse texture",
            "riser and drum fill back to final chorus",
            "add contrast and renew final chorus impact",
            "Pop bridge introduces fresh harmonic perspective before returning to the main hook.",
        ),
        sp(
            "bridge",
            "rock",
            ["vocal", "guitar", "bass", "drums", "synth"],
            "thick",
            7,
            "melody shifts to lower register for weight",
            "chromatic chord movement for tension",
            "half-time snare with tom punctuations",
            "pedal bass under moving upper chords",
            "chorus ends with sustained guitar feedback",
            "snare fill and crash into last chorus",
            "break repetition and create lift",
            "Rock bridge often darkens color and alters meter feel to make the final chorus hit harder.",
        ),
        sp(
            "bridge",
            "jazz",
            ["sax", "piano", "upright_bass", "drums", "guitar"],
            "medium",
            6,
            "bridge melody uses sequence and altered tensions",
            "cycle-of-fifths bridge progression with substitutions",
            "swing continues with denser comp accents",
            "walking bass emphasizes guide-tone resolutions",
            "head ends with pickup into bridge",
            "turnaround into head reprise",
            "expand harmonic journey",
            "Jazz bridge re-harmonizes familiar material and refreshes directional pull before returning home.",
        ),
        sp(
            "bridge",
            "rnb",
            ["lead_vocal", "harmony_stack", "electric_piano", "synth_pad", "sub_bass"],
            "medium",
            6,
            "melody becomes more legato and vulnerable",
            "borrowed chords and extended dominants",
            "drums reduced to rim and sparse kick",
            "sub holds long tones with occasional glide",
            "chorus layers strip down abruptly",
            "vocal ad-lib run into final chorus",
            "deliver emotional perspective shift",
            "R&B bridge thins rhythm and enriches harmony to spotlight lyric intimacy before final peak.",
        ),
        sp(
            "bridge",
            "edm",
            ["vocal", "pad", "arp", "fx", "kick", "bass"],
            "medium",
            7,
            "hook fragmented into atmospheric chops",
            "minor reharmonization of drop chords",
            "groove alternates between half-time and full-time",
            "sub returns gradually via filter automation",
            "breakdown ambience into moving arp",
            "snare build into final drop",
            "reset ear then relaunch energy",
            "EDM bridge is a contrast engine that recontextualizes the hook before final release.",
        ),
        sp(
            "bridge",
            "country",
            ["lead_vocal", "acoustic_guitar", "piano", "pedal_steel", "bass", "drums"],
            "medium",
            6,
            "melody pivots to reflective, sustained phrases",
            "relative minor shift then dominant return",
            "groove simplifies with brushes",
            "bass stays supportive on roots",
            "chorus tag decays to guitar and vocal",
            "drum fill and harmony swell to final chorus",
            "offer lyrical new angle",
            "Country bridge uses harmonic detour and narrative twist to refresh repeated hook sections.",
        ),
        # outro
        sp(
            "outro",
            "pop",
            ["lead_vocal", "backing_vocals", "piano", "synth_pad", "drums", "bass"],
            "medium",
            4,
            "hook repeated with ad-lib variation",
            "tonic prolongation with plagal color",
            "groove simplifies and removes high percussion",
            "root pedal fading with sidechain reduced",
            "last chorus extends with tag repeats",
            "fade-out or final stinger chord",
            "provide closure while retaining hook memory",
            "Pop outro usually recycles chorus identity and gradually strips layers for smooth release.",
        ),
        sp(
            "outro",
            "rock",
            ["guitar", "bass", "drums", "vocal", "organ"],
            "thick",
            5,
            "final refrain gives way to instrumental riff",
            "riff vamp on tonic and subdominant",
            "drums keep full pulse then break for final hit",
            "bass follows riff with final descending run",
            "last chorus extends with crowd-style shouts",
            "hard stop, unison hit, or feedback decay",
            "end with physical impact",
            "Rock outro commonly alternates vamp repetition and decisive final hit to leave a strong afterimage.",
        ),
        sp(
            "outro",
            "jazz",
            ["piano", "upright_bass", "drums", "horns"],
            "thin",
            3,
            "head fragment restated softly",
            "ii-V turnarounds resolved with tag ending",
            "ride and brushes taper dynamics",
            "walking bass slows to two-feel",
            "last head chorus cues tag",
            "held tonic extension and ensemble cutoff",
            "signal elegant resolution",
            "Jazz outro often uses tag repetitions and dynamic tapering to land a tasteful cadence.",
        ),
        sp(
            "outro",
            "edm",
            ["pad", "pluck", "fx_downlifter", "kick", "sub_bass"],
            "thin",
            3,
            "hook motif reduced to filtered echo",
            "static tonic vamp with high-cut automation",
            "kick removed progressively every 4 bars",
            "sub filtered and faded to mono",
            "drop tail collapses to ambience",
            "noise sweep down and reverb tail",
            "cool down dancefloor energy",
            "EDM outro clears low-end and rhythmic density to transition naturally out of peak sections.",
        ),
        sp(
            "outro",
            "classical",
            ["strings", "woodwinds", "brass", "timpani", "harp"],
            "medium",
            4,
            "main theme appears in augmentation",
            "cadential progression with tonic pedal",
            "ritardando and cadential rhythmic broadening",
            "double bass sustains tonic foundation",
            "recapitulated material moves to coda",
            "perfect authentic cadence and final fermata",
            "formal closure and thematic summation",
            "Classical outro/coda consolidates thematic material and confirms tonal resolution decisively.",
        ),
        sp(
            "outro",
            "folk",
            ["acoustic_guitar", "fiddle", "vocal", "upright_bass"],
            "thin",
            2,
            "last line delivered almost a cappella",
            "return to opening chords in simpler voicing",
            "strumming decrescendos with rubato ending",
            "bass drops out before final chord",
            "chorus repeats then strips to core duo",
            "natural room decay on final strum",
            "create intimate farewell",
            "Folk outro often mirrors intro simplicity, closing the narrative with human-scale texture.",
        ),
        # drop
        sp(
            "drop",
            "edm",
            ["supersaw", "sub_bass", "kick", "clap", "fx", "vocal_chop"],
            "very_thick",
            10,
            "house-style hook in short rhythmic loops",
            "bright triad stack over looped progression",
            "steady four-on-floor with groove percussion",
            "sidechained sub anchors each downbeat",
            "buildup ends with silence and impact hit",
            "DJ-friendly 8-bar phrase ending into break",
            "deliver maximal kinetic release",
            "House-oriented drop emphasizes groove continuity and broad harmonic clarity.",
        ),
        sp(
            "drop",
            "edm",
            ["wobble_bass", "growl_lead", "kick", "snare", "fx", "vocal_chop"],
            "very_thick",
            10,
            "dubstep motif built from call-and-response bass design",
            "minimal harmony; tension from timbral modulation",
            "half-time snare with syncopated bass rhythm",
            "aggressive modulated bass dominates low-mid band",
            "hard cutoff and pre-drop vocal",
            "fill into second drop variation",
            "create shock-and-release contrast",
            "Dubstep drop prioritizes timbral aggression and rhythmic surprise over harmonic movement.",
        ),
        sp(
            "drop",
            "edm",
            ["trance_lead", "arp", "kick", "sub_bass", "pad", "fx"],
            "very_thick",
            9,
            "trance lead states long hook over driving pulse",
            "minor progression with extended dominant lift",
            "full 4/4 kick with gated sidechain pads",
            "rolling offbeat bass pattern",
            "snare crescendo and white-noise rise",
            "breakdown return with filtered lead",
            "sustain euphoric drive",
            "Trance drop favors continuous forward motion and long-form melodic euphoria.",
        ),
        # buildup
        sp(
            "buildup",
            "edm",
            ["snare_roll", "fx_riser", "vocal_chop", "arp", "sub_bass"],
            "thick",
            8,
            "house hook chopped into shorter rhythmic cells",
            "chord loop stays static while filter opens",
            "snare density rises every 4 bars",
            "sub thins out right before drop",
            "verse or break strips drums first",
            "bar-8 silence then drop",
            "raise anticipation through repetition and acceleration",
            "House buildup escalates by adding subdivisions and widening frequency content without harmonic change.",
        ),
        sp(
            "buildup",
            "edm",
            ["snare_roll", "noise", "vocal_fx", "synth_stab", "sub_bass"],
            "very_thick",
            9,
            "dubstep phrase chopped with pitch risers",
            "single-chord pedal keeps harmonic tension unresolved",
            "triplet snare bursts and stutter edits",
            "sub mutes one bar before drop",
            "breakdown reintroduces rhythmic edits",
            "impact hit into drop groove",
            "compress time perception before impact",
            "Dubstep buildup relies on rhythmic fragmentation and hard mutes to maximize impact contrast.",
        ),
        sp(
            "buildup",
            "edm",
            ["arp", "pad", "snare_roll", "fx_riser", "kick"],
            "thick",
            8,
            "trance motif ascends in sequential transposition",
            "harmonic rhythm doubles near final bars",
            "snare roll plus open-hat ramps",
            "offbeat bass continues until final cutoff",
            "breakdown pad grows brighter",
            "uplifter peak and drop hit",
            "create long-form lift and expectation",
            "Trance buildup is gradual and melodic, often spanning 16-32 bars before release.",
        ),
        # breakdown
        sp(
            "breakdown",
            "edm",
            ["pad", "piano", "vocal", "fx", "sub_bass"],
            "thin",
            4,
            "hook restated in sparse piano voicing",
            "chord progression simplified with suspended delays",
            "kick removed; only ambient pulse remains",
            "sub follows long whole-note roots",
            "drop ends with filtered tail",
            "snare roll or arp ramp to buildup",
            "provide emotional reset between peaks",
            "EDM breakdown reduces rhythmic pressure and reframes melodic material before the next build.",
        ),
        sp(
            "breakdown",
            "rock",
            ["vocal", "clean_guitar", "bass", "drums"],
            "thin",
            5,
            "vocal line becomes more exposed and lower",
            "minor detour with suspended chords",
            "half-time groove with tom accents",
            "bass holds pedal note to build tension",
            "chorus drops to stripped band texture",
            "snare fill into solo or chorus",
            "contrast intensity and spotlight lyric",
            "Rock breakdown shifts to sparse half-time to reset dynamics before returning to full power.",
        ),
        sp(
            "breakdown",
            "pop",
            ["vocal", "piano", "pad", "sub_bass", "snap"],
            "thin",
            4,
            "chorus hook reharmonized softly",
            "diatonic progression with added suspended tones",
            "beat reduced to snaps and soft kick",
            "minimal sub pulses every other bar",
            "chorus ring-out into silence",
            "lift back through pre-chorus-style build",
            "emotional breath before final refrain",
            "Pop breakdown offers intimacy and lyrical focus to make final chorus feel larger.",
        ),
        sp(
            "breakdown",
            "jazz",
            ["piano", "bass", "drums", "flugelhorn"],
            "thin",
            3,
            "improvised paraphrase of main theme",
            "pedal-point reharmonization with quartal colors",
            "rubato phrasing then soft pulse return",
            "bass sustains drones and sparse approach notes",
            "full ensemble thins to trio texture",
            "pickup fill back to head",
            "create reflective contrast",
            "Jazz breakdown/interlude moment suspends strict form and tempo to refresh listener attention.",
        ),
        # solo
        sp(
            "solo",
            "rock",
            ["lead_guitar", "rhythm_guitar", "bass", "drums", "keys"],
            "thick",
            8,
            "lead instrument develops motif with bends and sequences",
            "looped chorus harmony or modal vamp",
            "steady rock groove with occasional stops",
            "bass mirrors accent hits then returns to roots",
            "chorus tail opens lane for solo",
            "drum fill back to vocal hook",
            "showcase virtuosity and sustain excitement",
            "Rock solo sections usually retain groove intensity while opening midrange space for lead guitar.",
        ),
        sp(
            "solo",
            "jazz",
            ["tenor_sax", "piano", "upright_bass", "drums", "guitar"],
            "medium",
            7,
            "improvised lines target guide tones and motif development",
            "standard form with reharmonized passing dominants",
            "swing comping with interactive hits",
            "walking bass reinforces form landmarks",
            "head closes and soloist enters via pickup",
            "trading fours or drum break to head out",
            "expand improvisational narrative",
            "Jazz solo section is the core developmental space where tension rises through harmonic navigation.",
        ),
        sp(
            "solo",
            "blues",
            ["lead_guitar", "rhythm_guitar", "bass", "drums", "organ"],
            "thick",
            7,
            "blues-scale motifs with call-and-response phrasing",
            "12-bar dominant cycle with turnarounds",
            "shuffle persists with stronger fills",
            "walking bass locks turnaround cues",
            "vocal chorus ends on held chord",
            "pickup lick into final vocal chorus",
            "intensify expressive tension",
            "Blues solo extends emotional vocabulary through articulation nuance rather than dense reharmony.",
        ),
        sp(
            "solo",
            "country",
            ["pedal_steel", "telecaster", "acoustic_guitar", "bass", "drums"],
            "medium",
            7,
            "steel and guitar trade short melodic phrases",
            "verse/chorus harmony with added passing chords",
            "steady train beat and brush snare support",
            "bass outlines roots with melodic walk-ups",
            "chorus tag creates opening for instrumental break",
            "fiddle pickup back to chorus",
            "add color while keeping song singable",
            "Country solo sections stay melodic and lyric-friendly, emphasizing phrase clarity over complexity.",
        ),
        sp(
            "solo",
            "latin",
            ["trumpet", "piano", "bass", "congas", "timbales", "guitar"],
            "thick",
            8,
            "horn improvisation uses rhythmic cells over clave",
            "montuno vamp with dominant turnaround",
            "percussion remains dense and dance-forward",
            "tumbao bass supports syncopated horn accents",
            "chorus chant drops to percussion break",
            "brass hit cues return to vocal",
            "elevate excitement without losing groove",
            "Latin solo passages are rhythm-centric and depend on tight dialogue with percussion patterns.",
        ),
        # interlude
        sp(
            "interlude",
            "general",
            ["piano", "strings", "pad", "fx"],
            "thin",
            3,
            "theme transformed into short instrumental motif",
            "non-functional planing for color shift",
            "free pulse or sparse ostinato",
            "minimal pedal bass",
            "vocal section resolves to held chord",
            "pickup fill into next verse/chorus",
            "create breathing room and scene change",
            "General interlude acts as narrative punctuation, often recontextualizing motifs without heavy beat pressure.",
        ),
        sp(
            "interlude",
            "pop",
            ["synth", "vocal_chop", "piano", "bass", "drums"],
            "medium",
            5,
            "hook appears as instrumental vocal-chop phrase",
            "chorus chords reharmonized with suspended voicings",
            "beat reduced to groove essentials",
            "bass simplifies to roots",
            "chorus decays into filtered interlude",
            "snare pickup to verse/bridge",
            "refresh hook without lyric overload",
            "Pop interlude is a hook-maintenance device that preserves familiarity while resting the vocal lead.",
        ),
        sp(
            "interlude",
            "jazz",
            ["piano", "upright_bass", "drums", "clarinet"],
            "thin",
            4,
            "instrumental paraphrase bridges form sections",
            "substitute dominant chain to pivot key center",
            "brush groove with subtle metric displacement",
            "walking-to-two-feel transition",
            "solo cadence leads into interlude",
            "pickup into head or new chorus",
            "smooth formal pivot",
            "Jazz interlude provides harmonic redirection and resets phrase architecture before restatement.",
        ),
        sp(
            "interlude",
            "classical",
            ["strings", "woodwinds", "harp", "horn"],
            "medium",
            4,
            "motivic fragments exchanged between sections",
            "sequential modulation through related keys",
            "ostinato under lyrical counterlines",
            "celli maintain harmonic anchor",
            "cadence from prior theme",
            "dominant preparation into next movement/section",
            "bridge large-form architecture",
            "Classical interlude connects thematic blocks through modulation and orchestrational dialogue.",
        ),
        sp(
            "interlude",
            "edm",
            ["pad", "arp", "fx", "vocal_chop", "sub_bass"],
            "thin",
            4,
            "hook granularized into atmospheric fragments",
            "single-chord bed with delayed resolution",
            "rhythm mostly removed except pulse ghost",
            "sub enters only at phrase boundaries",
            "drop tail filters into ambience",
            "riser into buildup or verse",
            "reset listener focus between drops",
            "EDM interlude functions as a low-energy connector, preserving motif identity while reducing impact fatigue.",
        ),
        sp(
            "interlude",
            "folk",
            ["acoustic_guitar", "fiddle", "mandolin", "upright_bass"],
            "thin",
            3,
            "instrumental echo of vocal melody",
            "modal drone with tonic-subdominant movement",
            "light strumming and bowed sustain",
            "bass outlines simple roots",
            "verse ends with open-string ring",
            "pick-up strum into next verse",
            "maintain narrative flow without lyrics",
            "Folk interlude gives the story a reflective pause while keeping acoustic continuity intact.",
        ),
        sp(
            "interlude",
            "rnb",
            ["electric_piano", "synth_pad", "sub_bass", "drum_machine", "vocalise"],
            "thin",
            4,
            "wordless vocalise carries motif variation",
            "extended chords with chromatic inner motion",
            "beat drops to rim and soft kick",
            "sub sustains long notes",
            "chorus ad-lib tail melts into keys",
            "snare lift to final chorus",
            "create sensual space before climax",
            "R&B interlude is often a texture-and-harmony showcase that resets emotional tone for the final section.",
        ),
    ]
    return patterns


def build_tension_curves() -> list[dict[str, Any]]:
    return [
        tc(
            "classic_pop_arc",
            "pop",
            "intro-verse-chorus-verse-chorus-bridge-chorus-outro",
            {"intro": 3, "verse1": 4, "chorus1": 7, "verse2": 5, "chorus2": 8, "bridge": 6, "chorus3": 9, "outro": 4},
            "Mainstream pop arc with repeated chorus lifts and a contrast bridge before the final peak.",
            "Katy Perry - Firework",
        ),
        tc(
            "rock_power_build",
            "rock",
            "intro-verse-pre_chorus-chorus-verse-pre_chorus-chorus-solo-chorus-outro",
            {"intro": 4, "verse1": 5, "pre_chorus1": 7, "chorus1": 8, "verse2": 6, "pre_chorus2": 8, "chorus2": 9, "solo": 8, "chorus3": 10, "outro": 5},
            "Rock layout with aggressive step-ups into each chorus and a high-energy solo plateau.",
            "Bon Jovi - Livin' on a Prayer",
        ),
        tc(
            "ballad_emotional_arc",
            "pop",
            "intro-verse-verse-pre_chorus-chorus-verse-pre_chorus-chorus-outro",
            {"intro": 2, "verse1": 3, "verse2": 4, "pre_chorus1": 5, "chorus1": 7, "verse3": 5, "pre_chorus2": 6, "chorus2": 8, "outro": 3},
            "Ballad curve rises gradually from intimacy to emotional release, then resolves softly.",
            "Adele - Someone Like You",
        ),
        tc(
            "edm_drop_cycle",
            "edm",
            "intro-buildup-drop-breakdown-buildup-drop-outro",
            {"intro": 3, "buildup1": 8, "drop1": 10, "breakdown": 4, "buildup2": 9, "drop2": 10, "outro": 3},
            "Two-cycle EDM architecture alternating high-tension builds and maximal drop release.",
            "Martin Garrix - Animals",
        ),
        tc(
            "jazz_head_solo_head",
            "jazz",
            "intro-head-solo1-solo2-trading-head-outro",
            {"intro": 3, "head_in": 5, "solo1": 7, "solo2": 8, "trading": 9, "head_out": 6, "outro": 4},
            "Traditional jazz form where improvisational tension peaks during solos and trading.",
            "Miles Davis - So What",
        ),
        tc(
            "classical_sonata",
            "classical",
            "introduction-exposition-development-recapitulation-coda",
            {"introduction": 3, "exposition": 6, "development": 9, "recapitulation": 7, "coda": 5},
            "Sonata-like macro curve with highest tension in development and controlled release afterward.",
            "Beethoven - Symphony No. 5 (Movement 1)",
        ),
        tc(
            "folk_storytelling",
            "folk",
            "intro-verse-verse-chorus-verse-chorus-bridge-chorus-outro",
            {"intro": 2, "verse1": 3, "verse2": 4, "chorus1": 6, "verse3": 5, "chorus2": 7, "bridge": 6, "chorus3": 8, "outro": 3},
            "Narrative folk arc where each verse adds weight and choruses escalate community sing-along energy.",
            "Mumford & Sons - I Will Wait",
        ),
        tc(
            "rnb_groove_build",
            "rnb",
            "intro-verse-pre_chorus-chorus-verse-pre_chorus-chorus-bridge-chorus-outro",
            {"intro": 3, "verse1": 4, "pre_chorus1": 6, "chorus1": 7, "verse2": 5, "pre_chorus2": 7, "chorus2": 8, "bridge": 6, "chorus3": 9, "outro": 4},
            "R&B tension profile keeps groove continuity while layering harmonic and vocal intensity.",
            "Beyonce - Halo",
        ),
        tc(
            "blues_12bar_cycle",
            "blues",
            "intro-chorus1-chorus2-solo-chorus3-turnaround-outro",
            {"intro": 3, "chorus1": 5, "chorus2": 6, "solo": 8, "chorus3": 7, "turnaround": 6, "outro": 4},
            "Blues cycle builds within repeated 12-bar forms, peaking in instrumental solo choruses.",
            "B.B. King - The Thrill Is Gone",
        ),
        tc(
            "latin_dance_energy",
            "latin",
            "intro-verse-pre_chorus-chorus-montuno-chorus-break-chorus-outro",
            {"intro": 4, "verse": 5, "pre_chorus": 6, "chorus1": 8, "montuno": 9, "chorus2": 9, "break": 6, "chorus3": 10, "outro": 5},
            "Latin dance arc sustains high groove energy with montuno-driven late-section lift.",
            "Marc Anthony - Vivir Mi Vida",
        ),
        tc(
            "country_verse_chorus",
            "country",
            "intro-verse-chorus-verse-chorus-bridge-chorus-outro",
            {"intro": 3, "verse1": 4, "chorus1": 7, "verse2": 5, "chorus2": 8, "bridge": 6, "chorus3": 9, "outro": 4},
            "Country arc with lyrical verses and increasingly anthemic choruses.",
            "Luke Combs - Beautiful Crazy",
        ),
        tc(
            "anthem_epic_build",
            "rock",
            "intro-verse-pre_chorus-chorus-breakdown-buildup-chorus-outro",
            {"intro": 3, "verse": 5, "pre_chorus": 7, "chorus1": 9, "breakdown": 4, "buildup": 8, "chorus2": 10, "outro": 6},
            "Anthemic curve with dramatic mid-song reset and oversized final chorus return.",
            "Imagine Dragons - Believer",
        ),
        tc(
            "minimal_ambient",
            "general",
            "intro-texture_a-texture_b-climax-decay-outro",
            {"intro": 2, "texture_a": 3, "texture_b": 4, "climax": 6, "decay": 3, "outro": 2},
            "Low-contrast ambient shape with subtle crest rather than sharp peaks.",
            "Brian Eno - An Ending (Ascent)",
        ),
        tc(
            "progressive_long_build",
            "edm",
            "intro-verse-buildup1-drop1-breakdown-buildup2-drop2-extended_outro",
            {"intro": 2, "verse": 4, "buildup1": 7, "drop1": 8, "breakdown": 5, "buildup2": 9, "drop2": 10, "extended_outro": 4},
            "Progressive template favors long transitions and a larger second drop payoff.",
            "Eric Prydz - Opus",
        ),
        tc(
            "hip_hop_verse_hook",
            "hip_hop",
            "intro-verse-hook-verse-hook-bridge-hook-outro",
            {"intro": 3, "verse1": 5, "hook1": 7, "verse2": 6, "hook2": 8, "bridge": 6, "hook3": 9, "outro": 4},
            "Hip-hop arrangement arc where verses carry narrative tension and hooks deliver repeated release.",
            "Drake - God's Plan",
        ),
    ]


def validate_section_patterns(records: list[dict[str, Any]]) -> None:
    if len(records) < 50:
        raise ValueError(f"section_patterns requires at least 50 records, got {len(records)}")

    style_map: dict[str, set[str]] = {}
    for i, rec in enumerate(records):
        section_type = rec["section_type"]
        style = rec["style"]
        if section_type not in ALLOWED_SECTION_TYPES:
            raise ValueError(f"Invalid section_type at #{i}: {section_type}")
        if style not in ALLOWED_STYLES:
            raise ValueError(f"Invalid style at #{i}: {style}")
        if rec["texture_density"] not in ALLOWED_TEXTURE:
            raise ValueError(f"Invalid texture_density at #{i}: {rec['texture_density']}")
        level = rec["energy_level"]
        if level not in {str(v) for v in range(1, 11)}:
            raise ValueError(f"energy_level must be string 1-10 at #{i}: {level}")
        if not isinstance(rec["active_instruments"], list) or not rec["active_instruments"]:
            raise ValueError(f"active_instruments must be non-empty list at #{i}")

        style_map.setdefault(section_type, set()).add(style)

    for section_type, required_styles in REQUIRED_SECTION_STYLE.items():
        actual = style_map.get(section_type, set())
        if not required_styles.issubset(actual):
            missing = sorted(required_styles - actual)
            raise ValueError(f"Missing required styles for {section_type}: {missing}")


def validate_tension_curves(records: list[dict[str, Any]]) -> None:
    if len(records) < 15:
        raise ValueError(f"tension_curves requires at least 15 records, got {len(records)}")

    names = {rec["name"] for rec in records}
    missing_names = sorted(REQUIRED_CURVE_NAMES - names)
    if missing_names:
        raise ValueError(f"Missing required tension curve names: {missing_names}")

    for i, rec in enumerate(records):
        if not rec["name"] or not rec["structure"]:
            raise ValueError(f"Invalid tension curve record #{i}: missing name/structure")
        curve_data = rec["curve_data"]
        if not isinstance(curve_data, dict) or not curve_data:
            raise ValueError(f"curve_data must be non-empty object at #{i}")
        for key, value in curve_data.items():
            if not isinstance(key, str) or not key:
                raise ValueError(f"curve_data key must be non-empty string at #{i}")
            if not isinstance(value, int) or value < 1 or value > 10:
                raise ValueError(f"curve_data value must be int 1-10 at #{i}: {key}={value}")


def assign_sources(records: list[dict[str, Any]], refs: list[dict[str, str]], kind: str) -> None:
    for idx, record in enumerate(records):
        record["source"] = source_for(kind, refs, idx)


def write_section_patterns(conn: sqlite3.Connection, records: list[dict[str, Any]]) -> None:
    conn.execute("DELETE FROM section_patterns")
    conn.executemany(
        """
        INSERT INTO section_patterns (
            section_type, style, active_instruments, texture_density, energy_level,
            melody_treatment, harmony_treatment, rhythm_treatment, bass_treatment,
            transition_in, transition_out, mood_function, description, source
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                rec["section_type"],
                rec["style"],
                json.dumps(rec["active_instruments"], ensure_ascii=False, separators=(",", ":")),
                rec["texture_density"],
                rec["energy_level"],
                rec["melody_treatment"],
                rec["harmony_treatment"],
                rec["rhythm_treatment"],
                rec["bass_treatment"],
                rec["transition_in"],
                rec["transition_out"],
                rec["mood_function"],
                rec["description"],
                rec["source"],
            )
            for rec in records
        ],
    )


def write_tension_curves(conn: sqlite3.Connection, records: list[dict[str, Any]]) -> None:
    conn.execute("DELETE FROM tension_curves")
    conn.executemany(
        """
        INSERT INTO tension_curves (
            name, style, structure, curve_data, description, example_song, source
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                rec["name"],
                rec["style"],
                rec["structure"],
                json.dumps(rec["curve_data"], ensure_ascii=False, separators=(",", ":")),
                rec["description"],
                rec["example_song"],
                rec["source"],
            )
            for rec in records
        ],
    )


def main() -> None:
    init_db(DB_PATH)

    section_refs = load_reference_items(SECTION_REF_PATH)
    tension_refs = load_reference_items(TENSION_REF_PATH)

    section_patterns = build_section_patterns()
    tension_curves = build_tension_curves()

    assign_sources(section_patterns, section_refs, "section_pattern")
    assign_sources(tension_curves, tension_refs, "tension_curve")

    validate_section_patterns(section_patterns)
    validate_tension_curves(tension_curves)

    conn = sqlite3.connect(str(DB_PATH))
    try:
        write_section_patterns(conn, section_patterns)
        write_tension_curves(conn, tension_curves)
        conn.commit()
    finally:
        conn.close()

    print(f"Loaded {len(section_patterns)} section_patterns records")
    print(f"Loaded {len(tension_curves)} tension_curves records")
    print(f"Section refs used: {len(section_refs)} from {SECTION_REF_PATH.name}")
    print(f"Tension refs used: {len(tension_refs)} from {TENSION_REF_PATH.name}")


if __name__ == "__main__":
    main()
