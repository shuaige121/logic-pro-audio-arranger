#!/usr/bin/env python3
"""Run massive Brave searches for music knowledge. Coordinator runs this (has internet)."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from brave_search import batch_search

QUERIES = {
    "mood_music": [
        "music emotion mood tempo key mode mapping",
        "sad music characteristics tempo key instruments",
        "happy music theory elements major minor tempo",
        "epic cinematic music arrangement techniques",
        "romantic music arrangement characteristics",
        "tense suspenseful music harmony dissonance",
        "calm peaceful music arrangement elements",
        "angry aggressive music production techniques",
        "melancholy nostalgic music chord progressions",
        "triumphant victorious music arrangement",
        "mysterious dark music scales modes",
        "playful lighthearted music arrangement",
        "dreamy ethereal music production techniques",
        "energetic upbeat music rhythm tempo",
        "emotional ballad arrangement techniques instruments",
    ],
    "melody_accompaniment": [
        "melody accompaniment relationship music arrangement",
        "how piano accompanies vocal melody patterns",
        "guitar strumming patterns behind melody",
        "string arrangement behind lead melody techniques",
        "bass line melody interaction music theory",
        "countermelody writing techniques examples",
        "rhythm section supporting melody arrangement",
        "call and response melody arrangement examples",
        "melody doubling orchestration techniques",
        "accompaniment patterns different music styles",
        "how to arrange instruments around a melody",
        "comping patterns jazz behind melody",
        "synth pad melody support arrangement",
        "drum groove melody interaction rhythm",
        "melody harmony texture relationship arrangement",
    ],
    "section_patterns": [
        "song intro arrangement instruments patterns",
        "verse arrangement techniques instruments density",
        "chorus arrangement build energy instruments",
        "bridge arrangement contrast techniques",
        "pre-chorus build up arrangement techniques",
        "outro ending arrangement techniques music",
        "drop build arrangement EDM techniques",
        "song section transitions arrangement",
        "verse to chorus transition arrangement techniques",
        "arrangement density energy each section song",
        "how to build energy in music arrangement",
        "instrument layering verse chorus differences",
        "arrangement blueprint pop song sections",
        "song structure arrangement guide instruments per section",
        "dynamic contrast between song sections arrangement",
    ],
    "song_analysis": [
        "song arrangement analysis breakdown popular songs",
        "Adele Someone Like You arrangement analysis",
        "Billie Jean Michael Jackson arrangement breakdown",
        "Bohemian Rhapsody arrangement analysis instruments",
        "Hotel California arrangement analysis chords instruments",
        "Let It Be Beatles arrangement analysis",
        "Shape of You Ed Sheeran production breakdown",
        "Blinding Lights Weeknd arrangement analysis",
        "Despacito arrangement production analysis",
        "Yesterday Beatles arrangement analysis simple",
        "Hallelujah Leonard Cohen arrangement analysis",
        "Imagine John Lennon arrangement analysis",
        "No Woman No Cry Bob Marley arrangement",
        "Take Five Dave Brubeck arrangement analysis",
        "Superstition Stevie Wonder arrangement analysis",
        "Clair de Lune Debussy arrangement analysis",
        "Fur Elise Beethoven arrangement analysis",
        "Moonlight Sonata arrangement analysis",
        "Canon in D Pachelbel arrangement analysis",
        "All of Me John Legend arrangement analysis",
    ],
    "tension_energy": [
        "tension release music arrangement curve",
        "energy arc song structure arrangement",
        "dynamic curve pop song arrangement",
        "building tension music production techniques",
        "climax placement song arrangement",
        "arrangement energy levels verse chorus bridge",
        "emotional arc music composition",
        "tension resolution chord progression arrangement",
        "instrumental buildup techniques arrangement",
        "how producers create tension release in songs",
    ],
    "real_midi_projects": [
        "free MIDI files download popular songs",
        "MIDI file database arrangement analysis",
        "freemidi.org popular songs MIDI",
        "bitmidi.com MIDI files",
        "github MIDI music dataset arrangement",
        "MIDI arrangement multi-track examples",
        "MIDI file song structure analysis tools",
        "open source MIDI arrangements analysis",
        "MIDI chord progression dataset",
        "analyze MIDI file arrangement python",
    ],
}

def main():
    out_dir = Path(__file__).parent / "search_results"
    out_dir.mkdir(exist_ok=True)

    total = sum(len(v) for v in QUERIES.values())
    print(f"Running {total} queries across {len(QUERIES)} categories...", file=sys.stderr)

    for category, queries in QUERIES.items():
        print(f"\n--- {category} ({len(queries)} queries) ---", file=sys.stderr)
        results = batch_search(queries, count=20, delay=0.05)
        out_file = out_dir / f"{category}.json"
        out_file.write_text(json.dumps(results, ensure_ascii=False, indent=2))
        print(f"  Got {len(results)} results -> {out_file}", file=sys.stderr)

    print(f"\nDone! Results saved to {out_dir}/", file=sys.stderr)


if __name__ == "__main__":
    main()
