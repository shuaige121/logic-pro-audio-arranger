/**
 * Gemini AI Arranger
 *
 * Uses Gemini 2.0 Flash to generate full multi-track arrangements from a melody.
 * Falls back to the local template-based engine on failure.
 */

import type { NoteEvent, Arrangement, ArrangementTrack, KeyEstimate } from '../types/music.ts';
import { estimateKey, inferBarCount, generateHarmony, buildArrangement } from './index.ts';

type CreativityLevel = 'conservative' | 'balanced' | 'creative';

interface ImmutableProjectParams {
  readonly tempoBpm: number;
  readonly beatsPerBar: number;
  readonly key: KeyEstimate;
}

function createImmutableProjectParams(
  tempoBpm: number,
  beatsPerBar: number,
  key: KeyEstimate,
): ImmutableProjectParams {
  return { tempoBpm, beatsPerBar, key: { ...key } };
}

function enforceImmutableArrangement(
  arrangement: Arrangement,
  params: ImmutableProjectParams,
): Arrangement {
  return { ...arrangement, tempoBpm: params.tempoBpm };
}

const GEMINI_API_KEY = import.meta.env.VITE_GEMINI_API_KEY || '';
const GEMINI_MODEL = 'gemini-2.0-flash';
const GEMINI_ENDPOINT = `https://generativelanguage.googleapis.com/v1beta/models/${GEMINI_MODEL}:generateContent`;

// ---------------------------------------------------------------------------
// JSON Schema for structured output
// ---------------------------------------------------------------------------

const ARRANGEMENT_SCHEMA = {
  type: 'object',
  properties: {
    tracks: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          name: { type: 'string' },
          instrument: { type: 'string' },
          channel: { type: 'integer' },
          program: { type: 'integer' },
          notes: {
            type: 'array',
            items: {
              type: 'object',
              properties: {
                pitch: { type: 'integer' },
                start: { type: 'number' },
                duration: { type: 'number' },
                velocity: { type: 'integer' },
              },
              required: ['pitch', 'start', 'duration', 'velocity'],
            },
          },
        },
        required: ['name', 'instrument', 'channel', 'program', 'notes'],
      },
    },
  },
  required: ['tracks'],
};

// ---------------------------------------------------------------------------
// Prompt builder
// ---------------------------------------------------------------------------

function buildPrompt(
  melody: NoteEvent[],
  key: KeyEstimate,
  style: string,
  tempoBpm: number,
  bars: number,
  creativityLevel: CreativityLevel,
): string {
  const secondsPerBeat = 60 / tempoBpm;
  const totalDuration = bars * 4 * secondsPerBeat;
  const creativityGuidance = creativityLevel === 'conservative'
    ? 'Use simple, stable accompaniment with clear harmonic support and minimal rhythmic syncopation.'
    : creativityLevel === 'creative'
      ? 'Use adventurous voicings, rhythmic variation, and tasteful counter-melodies while staying musical.'
      : 'Balance clear support with occasional rhythmic and harmonic variation.';

  // Compact melody representation
  const melodyCompact = melody.slice(0, 200).map(n => ({
    p: n.pitch,
    s: Math.round(n.start * 1000) / 1000,
    d: Math.round(n.duration * 1000) / 1000,
    v: n.velocity,
  }));

  return `You are an expert music arranger. Given a melody, generate a complete multi-track arrangement.

## Input
- Key: ${key.tonicName} ${key.mode}
- Style: ${style}
- Tempo: ${tempoBpm} BPM
- Bars: ${bars} (4/4 time)
- Creativity level: ${creativityLevel}
- Total duration: ${totalDuration.toFixed(2)} seconds
- Seconds per beat: ${secondsPerBeat.toFixed(4)}

Melody notes (pitch=MIDI 0-127, s=start seconds, d=duration seconds, v=velocity):
${JSON.stringify(melodyCompact)}

## Instructions
Generate these tracks:
1. **Bass** — Root-based bass line following the implied chord progression. Use MIDI pitches 28-55 (bass range). Channel 1, program 33 (Electric Bass Finger).
2. **Harmony** — Chord pads or comping in mid range (MIDI 48-72). Channel 2, program 0 (Acoustic Grand Piano).
3. **Drums** — Rhythmic pattern appropriate for the style. Channel 9 (percussion). Use standard GM drum mapping: 36=kick, 38=snare, 42=hi-hat closed, 46=hi-hat open, 49=crash, 51=ride. Program 0.

Style guidelines:
- Pop: Straight 4/4 feel, root-fifth bass, block chords, standard rock beat
- Jazz: Walking bass, shell voicings (3rd+7th), swing ride cymbal pattern
- Modal: Pedal bass tones, open voicings, sparse percussion with groove

Creativity guidance:
- ${creativityGuidance}

## Rules
- DO NOT change tempo, key, or time signature. These are immutable: tempo=${tempoBpm} BPM, key=${key.tonicName} ${key.mode}.
- All note start times must be >= 0 and < ${totalDuration.toFixed(2)}
- All note durations must be > 0
- Velocity range: 40-120
- Bass pitches: 28-55
- Harmony pitches: 48-72
- Drum pitches: use only standard GM percussion (35-59)
- Generate notes that musically complement the given melody
- Create rhythmically interesting patterns, not just sustained notes
- Ensure the arrangement grooves and feels alive`;
}

// ---------------------------------------------------------------------------
// API call
// ---------------------------------------------------------------------------

async function callGemini(prompt: string): Promise<{ tracks: ArrangementTrack[] }> {
  const body = {
    contents: [{ parts: [{ text: prompt }] }],
    generationConfig: {
      responseMimeType: 'application/json',
      responseSchema: ARRANGEMENT_SCHEMA,
      temperature: 0.8,
      maxOutputTokens: 8192,
    },
  };

  const endpoint = `${GEMINI_ENDPOINT}?key=${encodeURIComponent(GEMINI_API_KEY)}`;
  const response = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Gemini API error ${response.status}: ${errorText}`);
  }

  const data = await response.json();
  const text = data?.candidates?.[0]?.content?.parts?.[0]?.text;
  if (!text) throw new Error('Empty response from Gemini');

  return JSON.parse(text);
}

// ---------------------------------------------------------------------------
// Validation & cleanup
// ---------------------------------------------------------------------------

function validateAndCleanTracks(
  tracks: ArrangementTrack[],
  totalDuration: number,
): ArrangementTrack[] {
  return tracks
    .filter(t => t.notes && t.notes.length > 0)
    .map(track => ({
      ...track,
      notes: track.notes
        .filter(n =>
          typeof n.pitch === 'number' &&
          typeof n.start === 'number' &&
          typeof n.duration === 'number' &&
          n.start >= 0 &&
          n.start < totalDuration &&
          n.duration > 0
        )
        .map(n => ({
          pitch: Math.max(0, Math.min(127, Math.round(n.pitch))),
          start: Math.max(0, n.start),
          duration: Math.min(n.duration, totalDuration - n.start),
          velocity: Math.max(1, Math.min(127, Math.round(n.velocity ?? 80))),
        })),
    }))
    .filter(t => t.notes.length > 0);
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Generate an arrangement using Gemini AI, with fallback to local engine.
 *
 * @returns The arrangement and whether AI was used.
 */
export async function generateArrangementWithAI(
  melody: NoteEvent[],
  tempoBpm: number,
  bars: number,
  style: 'pop' | 'modal' | 'jazz',
  complexity: 'basic' | 'rich',
  beatsPerBar: number,
  creativityLevel: CreativityLevel = 'balanced',
): Promise<{ arrangement: Arrangement; aiGenerated: boolean; key: KeyEstimate; harmony: import('../types/music.ts').HarmonyCandidate | null }> {
  const immutable = createImmutableProjectParams(tempoBpm, beatsPerBar, estimateKey(melody));
  const key = immutable.key;
  const barCount = Math.max(inferBarCount(melody, immutable.tempoBpm, immutable.beatsPerBar) || bars, bars);
  const secondsPerBeat = 60 / immutable.tempoBpm;
  const totalDuration = barCount * beatsPerBar * secondsPerBeat;

  // Try Gemini first when key is available.
  if (GEMINI_API_KEY) {
    try {
      const prompt = buildPrompt(melody, key, style, tempoBpm, barCount, creativityLevel);
      const result = await callGemini(prompt);

      const aiTracks = validateAndCleanTracks(result.tracks, totalDuration);
      if (aiTracks.length === 0) throw new Error('AI returned no valid tracks');

      // Always include the original melody as the first track
      const melodyTrack: ArrangementTrack = {
        name: 'Lead Melody',
        instrument: 'Synth Lead',
        channel: 0,
        program: 80,
        notes: melody,
      };

      const arrangement: Arrangement = {
        tracks: [melodyTrack, ...aiTracks],
        tempoBpm,
        bars: barCount,
        style,
        complexity,
      };

      return { arrangement: enforceImmutableArrangement(arrangement, immutable), aiGenerated: true, key: immutable.key, harmony: null };
    } catch (err) {
      console.warn('Gemini arranger failed, falling back to local engine:', err);
    }
  } else {
    console.warn('Gemini API key is missing, skipping Gemini and using local engine fallback.');
  }

  // Fallback to local engine
  const candidates = generateHarmony(melody, key, barCount, style, beatsPerBar, tempoBpm);
  const topCandidate = candidates.length > 0 ? candidates[0] : null;

  if (!topCandidate) {
    throw new Error('No harmony candidates found');
  }

  const arrangement = buildArrangement(melody, topCandidate.bars, immutable.tempoBpm, barCount, style, complexity);
  return { arrangement: enforceImmutableArrangement(arrangement, immutable), aiGenerated: false, key: immutable.key, harmony: topCandidate };
}
