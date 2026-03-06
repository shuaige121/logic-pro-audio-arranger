import { useI18n } from '../i18n.ts';
import type { ArrangementTrack } from '../types/music.ts';
import './TrackList.css';

const TRACK_COLORS: Record<string, string> = {
  melody: 'var(--track-melody)',
  lead: 'var(--track-melody)',
  bass: 'var(--track-bass)',
  harmony: 'var(--track-chords)',
  chord: 'var(--track-chords)',
  pad: 'var(--track-pad)',
  arp: 'var(--track-pad)',
  drum: 'var(--track-drums)',
  percus: 'var(--track-drums)',
};

function getTrackColor(name: string): string {
  const lower = name.toLowerCase();
  for (const [key, color] of Object.entries(TRACK_COLORS)) {
    if (lower.includes(key)) return color;
  }
  return 'var(--track-melody)';
}

export interface TrackState {
  muted: boolean;
  soloed: boolean;
  volume: number; // 0-1
}

interface TrackListProps {
  tracks: ArrangementTrack[];
  trackStates: Record<string, TrackState>;
  selectedTrack: string | null;
  onTrackSelect: (name: string) => void;
  onMuteToggle: (name: string) => void;
  onSoloToggle: (name: string) => void;
  onVolumeChange: (name: string, volume: number) => void;
}

export default function TrackList({
  tracks,
  trackStates,
  selectedTrack,
  onTrackSelect,
  onMuteToggle,
  onSoloToggle,
  onVolumeChange,
}: TrackListProps) {
  const { t } = useI18n();

  if (tracks.length === 0) {
    return (
      <div className="track-list">
        <div className="track-list__empty">{t('trackList.empty')}</div>
      </div>
    );
  }

  return (
    <div className="track-list">
      <div className="track-list__header">{t('trackList.title')}</div>
      {tracks.map((track) => {
        const color = getTrackColor(track.name);
        const state = trackStates[track.name] || { muted: false, soloed: false, volume: 0.8 };
        const isSelected = selectedTrack === track.name;

        return (
          <div
            key={track.name}
            className={`track-list__item ${isSelected ? 'track-list__item--selected' : ''}`}
            onClick={() => onTrackSelect(track.name)}
          >
            <div className="track-list__color-bar" style={{ backgroundColor: color }} />
            <div className="track-list__info">
              <span className="track-list__name">{track.name}</span>
              <span className="track-list__instrument">{track.instrument}</span>
            </div>
            <div className="track-list__controls">
              <button
                className={`track-list__btn track-list__btn--mute ${state.muted ? 'track-list__btn--active' : ''}`}
                onClick={(e) => { e.stopPropagation(); onMuteToggle(track.name); }}
                title={t('edit_mute')}
              >
                M
              </button>
              <button
                className={`track-list__btn track-list__btn--solo ${state.soloed ? 'track-list__btn--active' : ''}`}
                onClick={(e) => { e.stopPropagation(); onSoloToggle(track.name); }}
                title={t('edit_solo')}
              >
                S
              </button>
              <input
                type="range"
                className="track-list__volume"
                min={0}
                max={1}
                step={0.01}
                value={state.volume}
                onClick={(e) => e.stopPropagation()}
                onChange={(e) => onVolumeChange(track.name, parseFloat(e.target.value))}
                title={`${t('edit_volume')}: ${Math.round(state.volume * 100)}%`}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
