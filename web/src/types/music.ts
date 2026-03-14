export interface NoteEvent {
  pitch: number;      // MIDI note 0-127
  start: number;      // time in seconds
  duration: number;   // duration in seconds
  velocity: number;   // 0-127
}

export interface MelodyData {
  notes: NoteEvent[];
  readonly tempoBpm: number;
  readonly beatsPerBar: number;
  readonly beatUnit: number;
  readonly key?: KeyEstimate;
}

export interface KeyEstimate {
  tonicPc: number;
  tonicName: string;
  mode: 'major' | 'minor' | 'dorian' | 'mixolydian';
  score: number;
}

export interface Chord {
  rootPc: number;
  rootName: string;
  quality: string;
  symbol: string;
  roman: string;
  tones: number[];
}

export interface HarmonyCandidate {
  name: string;
  mode: string;
  bars: Chord[];
  score: number;
  chordToneCoverage: number;
  strongBeatCoverage: number;
}

export interface ArrangementTrack {
  name: string;
  instrument: string;
  channel: number;
  program: number;
  notes: NoteEvent[];
}

export interface Arrangement {
  tracks: ArrangementTrack[];
  readonly tempoBpm: number;
  bars: number;
  style: 'pop' | 'modal' | 'jazz';
  complexity: 'basic' | 'rich';
}
