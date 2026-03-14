// @vitest-environment node
import { describe, expect, it } from 'vitest';

import type { Arrangement, KeyEstimate, MelodyData, NoteEvent } from '../../types/music.ts';

const sampleNote: NoteEvent = { pitch: 60, start: 0, duration: 0.5, velocity: 80 };
const sampleKey: KeyEstimate = { tonicPc: 0, tonicName: 'C', mode: 'major', score: 1 };

describe('immutability contracts', () => {
  it('prevents MelodyData readonly fields from being reassigned at the type level', () => {
    const melody: MelodyData = {
      notes: [sampleNote],
      tempoBpm: 120,
      beatsPerBar: 4,
      beatUnit: 4,
      key: sampleKey,
    };

    if (false) {
      // @ts-expect-error tempoBpm is readonly
      melody.tempoBpm = 90;
      // @ts-expect-error beatsPerBar is readonly
      melody.beatsPerBar = 3;
      // @ts-expect-error beatUnit is readonly
      melody.beatUnit = 8;
      // @ts-expect-error key is readonly
      melody.key = { ...sampleKey, tonicName: 'G', tonicPc: 7 };
    }

    expect(melody.tempoBpm).toBe(120);
    expect(melody.beatsPerBar).toBe(4);
    expect(melody.beatUnit).toBe(4);
    expect(melody.key).toEqual(sampleKey);
  });

  it('prevents Arrangement.tempoBpm from being reassigned at the type level', () => {
    const arrangement: Arrangement = {
      tracks: [],
      tempoBpm: 128,
      bars: 8,
      style: 'pop',
      complexity: 'basic',
    };

    if (false) {
      // @ts-expect-error tempoBpm is readonly
      arrangement.tempoBpm = 100;
    }

    expect(arrangement.tempoBpm).toBe(128);
  });
});
