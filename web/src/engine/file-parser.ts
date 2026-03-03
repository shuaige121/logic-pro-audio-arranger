/**
 * File Parser
 *
 * Parses uploaded music files into NoteEvent arrays.
 * - MIDI files: parsed client-side using @tonejs/midi
 * - Audio/other files: sent to backend /api/digitize endpoint
 */

import { Midi } from '@tonejs/midi';
import type { NoteEvent } from '../types/music.ts';

// ---------------------------------------------------------------------------
// MIDI client-side parsing
// ---------------------------------------------------------------------------

/**
 * Parse a MIDI file (.mid/.midi) in the browser and extract notes.
 * Returns { notes, tempoBpm } or throws on error.
 */
export async function parseMidiFile(file: File): Promise<{ notes: NoteEvent[]; tempoBpm: number }> {
  const buffer = await file.arrayBuffer();
  const midi = new Midi(new Uint8Array(buffer));

  const tempoBpm = midi.header.tempos.length > 0
    ? midi.header.tempos[0].bpm
    : 120;

  const notes: NoteEvent[] = [];

  for (const track of midi.tracks) {
    for (const note of track.notes) {
      notes.push({
        pitch: note.midi,
        start: note.time,
        duration: note.duration,
        velocity: Math.round(note.velocity * 127),
      });
    }
  }

  // Sort by start time
  notes.sort((a, b) => a.start - b.start || a.pitch - b.pitch);

  return { notes, tempoBpm };
}

// ---------------------------------------------------------------------------
// Backend upload for audio files
// ---------------------------------------------------------------------------

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8765';

/**
 * Upload a file to the backend for digitization.
 * The backend handles audio analysis, pitch detection, etc.
 */
export async function uploadFileToBackend(
  file: File,
  style = 'pop',
): Promise<{ notes: NoteEvent[]; tempoBpm: number; summary?: { key: string } }> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('style', style);

  const response = await fetch(`${BACKEND_URL}/api/digitize`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: 'Server error' }));
    throw new Error(err.detail || `Upload failed (${response.status})`);
  }

  const data = await response.json();

  if (!data.ok) {
    throw new Error(data.detail || 'Digitization failed');
  }

  const notes: NoteEvent[] = (data.notes || []).map((n: { pitch: number; start: number; duration: number; velocity: number }) => ({
    pitch: n.pitch,
    start: n.start,
    duration: n.duration,
    velocity: n.velocity,
  }));

  return {
    notes,
    tempoBpm: data.tempo_bpm || 120,
    summary: data.summary,
  };
}

// ---------------------------------------------------------------------------
// Unified file handler
// ---------------------------------------------------------------------------

/** File extensions that can be parsed client-side (MIDI). */
const CLIENT_PARSEABLE = new Set(['.mid', '.midi']);

/** All supported file extensions. */
export const SUPPORTED_EXTENSIONS = [
  '.mid', '.midi',
  '.wav', '.aif', '.aiff',
  '.mp3', '.flac', '.ogg', '.aac', '.m4a', '.wma', '.opus',
  '.xml', '.musicxml', '.mxl',
  '.csv',
];

/**
 * Parse any supported music file.
 * MIDI files are parsed client-side; everything else goes to the backend.
 */
export async function parseFile(
  file: File,
  style = 'pop',
): Promise<{ notes: NoteEvent[]; tempoBpm: number; source: 'client' | 'server'; summary?: { key: string } }> {
  const ext = '.' + (file.name.split('.').pop()?.toLowerCase() || '');

  if (CLIENT_PARSEABLE.has(ext)) {
    const result = await parseMidiFile(file);
    return { ...result, source: 'client' };
  }

  // Send to backend
  const result = await uploadFileToBackend(file, style);
  return { ...result, source: 'server' };
}
