import { useMemo, useState } from 'react';
import type { CSSProperties, WheelEvent } from 'react';
import type { Arrangement, ArrangementTrack } from '../types/music.ts';
import { useI18n } from '../i18n.ts';
import './ArrangementView.css';

interface ArrangementViewProps {
  arrangement: Arrangement | null;
  currentBeat: number;
  beatsPerBar?: number;
  sections?: Array<{ name: string; startBar: number; endBar: number; color?: string }>;
}

interface SectionMarker {
  name: string;
  startBar: number;
  endBar: number;
  color?: string;
}

interface NoteBlock {
  left: number;
  width: number;
  top: number;
  height: number;
  tooltip: string;
}

interface TrackLaneData {
  track: ArrangementTrack;
  color: string;
  notes: NoteBlock[];
  subtitle: string;
}

const TRACK_HEIGHT = 64;
const TRACK_PADDING_Y = 6;
const TRACK_META_WIDTH = 200;

const DEFAULT_BEAT_WIDTH = 30;
const MIN_BEAT_WIDTH = 14;
const MAX_BEAT_WIDTH = 96;

/* Logic Pro region colors: green=instrument, blue=audio, yellow=drums, purple=midi */
const BRAND_COLORS = ['#5ec455', '#4a90d9', '#f5c542', '#c080e0'];
const SECTION_FALLBACK_COLORS = [
  'rgba(94, 196, 85, 0.24)',
  'rgba(74, 144, 217, 0.22)',
  'rgba(245, 197, 66, 0.20)',
  'rgba(192, 128, 224, 0.22)',
];
const NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

function midiToNoteName(pitch: number): string {
  const roundedPitch = Math.round(pitch);
  const safePitch = ((roundedPitch % 12) + 12) % 12;
  const octave = Math.floor(roundedPitch / 12) - 1;
  return `${NOTE_NAMES[safePitch]}${octave}`;
}

function buildDefaultSections(totalBars: number): SectionMarker[] {
  if (totalBars <= 0) return [];
  const labels = ['Intro', 'Verse', 'Chorus', 'Bridge', 'Chorus', 'Outro'];
  const targetCount = Math.min(labels.length, Math.max(1, Math.round(totalBars / 2)));
  const generated: SectionMarker[] = [];
  let startBar = 1;

  for (let i = 0; i < targetCount && startBar <= totalBars; i += 1) {
    const remainingBars = totalBars - startBar + 1;
    const sectionsLeft = targetCount - i;
    const length = sectionsLeft === 1 ? remainingBars : Math.max(1, Math.round(remainingBars / sectionsLeft));
    const endBar = startBar + length - 1;
    generated.push({
      name: labels[i] ?? `Section ${i + 1}`,
      startBar,
      endBar,
      color: SECTION_FALLBACK_COLORS[i % SECTION_FALLBACK_COLORS.length],
    });
    startBar = endBar + 1;
  }

  return generated;
}

function normalizeSections(input: SectionMarker[] | undefined, totalBars: number): SectionMarker[] {
  const source = input && input.length > 0 ? input : buildDefaultSections(totalBars);
  return source
    .map((section, index) => {
      const startBar = clamp(Math.floor(section.startBar || 1), 1, totalBars);
      const endBar = clamp(Math.floor(section.endBar || startBar), startBar, totalBars);
      return {
        ...section,
        startBar,
        endBar,
        color: section.color ?? SECTION_FALLBACK_COLORS[index % SECTION_FALLBACK_COLORS.length],
      };
    })
    .sort((a, b) => a.startBar - b.startBar);
}

export default function ArrangementView({
  arrangement,
  currentBeat,
  beatsPerBar = 4,
  sections,
}: ArrangementViewProps) {
  const { t } = useI18n();
  const [beatWidth, setBeatWidth] = useState(DEFAULT_BEAT_WIDTH);

  const safeBeatsPerBar = Math.max(1, Math.floor(beatsPerBar));
  const tempoBpm = arrangement ? Math.max(1, arrangement.tempoBpm || 120) : 120;
  const secondsPerBeat = 60 / tempoBpm;

  const inferredBeats = useMemo(() => {
    if (!arrangement) return 0;
    return arrangement.tracks.reduce((maxBeat, track) => {
      const trackMaxBeat = track.notes.reduce((noteMax, note) => {
        const noteEndBeat = (note.start + note.duration) / secondsPerBeat;
        return Math.max(noteMax, noteEndBeat);
      }, 0);
      return Math.max(maxBeat, trackMaxBeat);
    }, 0);
  }, [arrangement, secondsPerBeat]);

  const totalBeats = arrangement
    ? Math.max(1, Math.ceil(Math.max(arrangement.bars * safeBeatsPerBar, inferredBeats)))
    : 0;
  const totalBars = arrangement ? Math.max(1, Math.ceil(totalBeats / safeBeatsPerBar)) : 0;
  const timelineWidth = totalBeats * beatWidth;
  const playheadLeft = clamp(currentBeat, 0, totalBeats) * beatWidth;

  const normalizedSections = useMemo(
    () => (arrangement ? normalizeSections(sections, totalBars) : []),
    [arrangement, sections, totalBars],
  );

  const trackLanes = useMemo<TrackLaneData[]>(() => {
    if (!arrangement) return [];
    return arrangement.tracks.map((track, index) => {
      const color = BRAND_COLORS[index % BRAND_COLORS.length];
      const notes = track.notes ?? [];
      const pitches = notes.map((note) => note.pitch);
      const minPitch = pitches.length > 0 ? Math.min(...pitches) - 2 : 48;
      const maxPitch = pitches.length > 0 ? Math.max(...pitches) + 2 : 72;
      const pitchRange = Math.max(12, maxPitch - minPitch);
      const noteHeight = 8;
      const noteTravel = Math.max(1, TRACK_HEIGHT - TRACK_PADDING_Y * 2 - noteHeight);

      const blocks = notes.map((note) => {
        const startBeat = note.start / secondsPerBeat;
        const durationBeats = Math.max(0.125, note.duration / secondsPerBeat);
        const normalizedPitch = (maxPitch - note.pitch) / pitchRange;
        const top = TRACK_PADDING_Y + normalizedPitch * noteTravel;

        return {
          left: startBeat * beatWidth,
          width: Math.max(4, durationBeats * beatWidth - 1),
          top: clamp(top, TRACK_PADDING_Y, TRACK_HEIGHT - TRACK_PADDING_Y - noteHeight),
          height: noteHeight,
          tooltip: `${midiToNoteName(note.pitch)} | Vel ${Math.round(note.velocity)} | ${durationBeats.toFixed(2)} beat`,
        };
      });

      const subtitle = track.instrument || `Program ${track.program}`;
      return { track, color, notes: blocks, subtitle };
    });
  }, [arrangement, beatWidth, secondsPerBeat]);

  const timelineGridStyle = useMemo<CSSProperties>(() => {
    return {
      backgroundImage: `
        linear-gradient(to right, rgba(255, 255, 255, 0.07) 1px, transparent 1px),
        linear-gradient(to right, rgba(255, 255, 255, 0.18) 1px, transparent 1px)
      `,
      backgroundSize: `${beatWidth}px 100%, ${beatWidth * safeBeatsPerBar}px 100%`,
      backgroundPosition: '0 0',
    };
  }, [beatWidth, safeBeatsPerBar]);

  const handleWheel = (event: WheelEvent<HTMLDivElement>) => {
    if (!(event.ctrlKey || event.metaKey)) return;
    event.preventDefault();
    setBeatWidth((prev) => {
      const next = prev - event.deltaY * 0.06;
      return Math.round(clamp(next, MIN_BEAT_WIDTH, MAX_BEAT_WIDTH));
    });
  };

  if (!arrangement) {
    return (
      <div className="arrangement-view">
        <div className="arrangement-view__timeline arrangement-view__timeline--empty">
          <div className="empty-state">
            <div className="empty-state__title">{t('arrangement.emptyTitle')}</div>
            <div className="empty-state__description">{t('arrangement.emptyDesc')}</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="arrangement-view">
      <div className="arrangement-view__timeline" onWheel={handleWheel}>
        <div
          className="arrangement-view__content"
          style={{ width: TRACK_META_WIDTH + timelineWidth }}
        >
          <div className="arrangement-view__row arrangement-view__row--sections">
            <div className="arrangement-view__meta-cell arrangement-view__meta-cell--section-title">
              Sections
            </div>
            <div
              className="arrangement-view__timeline-cell arrangement-view__timeline-cell--sections"
              style={{ ...timelineGridStyle, width: timelineWidth }}
            >
              {normalizedSections.map((section, index) => {
                const left = (section.startBar - 1) * safeBeatsPerBar * beatWidth;
                const width = Math.max(8, (section.endBar - section.startBar + 1) * safeBeatsPerBar * beatWidth);
                return (
                  <div
                    key={`${section.name}-${section.startBar}-${index}`}
                    className="arrangement-view__section-block"
                    style={{ left, width, backgroundColor: section.color }}
                  >
                    {section.name}
                  </div>
                );
              })}
              <div className="arrangement-view__playhead" style={{ left: playheadLeft }} />
            </div>
          </div>

          <div className="arrangement-view__row arrangement-view__row--ruler">
            <div className="arrangement-view__meta-cell arrangement-view__meta-cell--ruler-title">
              Tracks
            </div>
            <div
              className="arrangement-view__timeline-cell arrangement-view__timeline-cell--ruler"
              style={{ ...timelineGridStyle, width: timelineWidth }}
            >
              {Array.from({ length: totalBars }, (_, barIndex) => (
                <div
                  key={`bar-label-${barIndex}`}
                  className="arrangement-view__bar-label"
                  style={{ left: barIndex * safeBeatsPerBar * beatWidth + 6 }}
                >
                  {barIndex + 1}
                </div>
              ))}
              {Array.from({ length: totalBeats }, (_, beatIndex) => (
                <div
                  key={`beat-label-${beatIndex}`}
                  className="arrangement-view__beat-label"
                  style={{ left: beatIndex * beatWidth + 4 }}
                >
                  {(beatIndex % safeBeatsPerBar) + 1}
                </div>
              ))}
              <div className="arrangement-view__playhead" style={{ left: playheadLeft }} />
            </div>
          </div>

          {trackLanes.map((lane, trackIndex) => (
            <div
              className={`arrangement-view__row arrangement-view__row--track ${trackIndex % 2 === 0 ? 'arrangement-view__row--even' : 'arrangement-view__row--odd'}`}
              key={`${lane.track.name}-${trackIndex}`}
              style={{ height: TRACK_HEIGHT }}
            >
              <div className="arrangement-view__meta-cell arrangement-view__meta-cell--track">
                <span
                  className="arrangement-view__track-color"
                  style={{ backgroundColor: lane.color }}
                />
                <div className="arrangement-view__track-info">
                  <span className="arrangement-view__track-name">{lane.track.name}</span>
                  <span className="arrangement-view__track-subtitle">
                    {lane.subtitle} · {lane.track.notes.length} notes
                  </span>
                </div>
              </div>
              <div
                className="arrangement-view__timeline-cell arrangement-view__timeline-cell--track"
                style={{ ...timelineGridStyle, width: timelineWidth, height: TRACK_HEIGHT }}
              >
                {lane.notes.map((note, noteIndex) => (
                  <div
                    key={`${lane.track.name}-${noteIndex}`}
                    className="arrangement-view__note"
                    style={{
                      left: note.left,
                      width: note.width,
                      top: note.top,
                      height: note.height,
                      backgroundColor: lane.color,
                    }}
                    title={note.tooltip}
                  />
                ))}
                <div className="arrangement-view__playhead" style={{ left: playheadLeft }} />
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="arrangement-view__zoom">
        <span className="arrangement-view__zoom-label">Zoom</span>
        <input
          type="range"
          min={MIN_BEAT_WIDTH}
          max={MAX_BEAT_WIDTH}
          value={beatWidth}
          className="arrangement-view__zoom-slider"
          onChange={(event) => setBeatWidth(Number(event.target.value))}
          aria-label="Timeline zoom"
        />
        <span className="arrangement-view__zoom-value">{Math.round(beatWidth)} px/beat</span>
      </div>
    </div>
  );
}
