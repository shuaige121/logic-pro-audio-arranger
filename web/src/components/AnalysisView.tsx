import { useI18n } from '../i18n.ts';
import './AnalysisView.css';

export type TimeSignature = '3/4' | '4/4' | '6/8';

export interface AnalysisFormState {
  key: string;
  mode: 'major' | 'minor' | 'dorian' | 'mixolydian';
  bpm: number;
  timeSignature: TimeSignature;
  bars: number;
  notes: number;
  phrases: number;
}

interface AnalysisViewProps {
  value: AnalysisFormState;
  onChange: (next: AnalysisFormState) => void;
  onConfirm: () => void;
}

const KEY_OPTIONS = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
const MODE_OPTIONS: Array<AnalysisFormState['mode']> = ['major', 'minor', 'dorian', 'mixolydian'];
const TIME_SIGNATURE_OPTIONS: TimeSignature[] = ['3/4', '4/4', '6/8'];

function modeLabel(mode: AnalysisFormState['mode']): string {
  switch (mode) {
    case 'major':
      return 'major';
    case 'minor':
      return 'minor';
    case 'dorian':
      return 'dorian';
    case 'mixolydian':
      return 'mixolydian';
    default:
      return mode;
  }
}

export default function AnalysisView({ value, onChange, onConfirm }: AnalysisViewProps) {
  const { t } = useI18n();

  return (
    <section className="analysis-view">
      <header className="analysis-view__header">
        <h2 className="analysis-view__title">{t('analyze_title')}</h2>
        <p className="analysis-view__subtitle">{t('analyze_correct')}</p>
      </header>

      <div className="analysis-view__stats">
        <div className="analysis-view__stat-card">
          <span>{t('analyze_bars')}</span>
          <strong>{value.bars}</strong>
        </div>
        <div className="analysis-view__stat-card">
          <span>{t('analyze_notes')}</span>
          <strong>{value.notes}</strong>
        </div>
        <div className="analysis-view__stat-card">
          <span>{t('analyze_phrases')}</span>
          <strong>{value.phrases}</strong>
        </div>
      </div>

      <div className="analysis-view__controls">
        <label className="analysis-view__field">
          <span>{t('analyze_key')}</span>
          <div className="analysis-view__key-row">
            <select
              className="select-control"
              value={value.key}
              onChange={(event) => onChange({ ...value, key: event.target.value })}
            >
              {KEY_OPTIONS.map((keyName) => (
                <option key={keyName} value={keyName}>
                  {keyName}
                </option>
              ))}
            </select>
            <select
              className="select-control"
              value={value.mode}
              onChange={(event) => onChange({ ...value, mode: event.target.value as AnalysisFormState['mode'] })}
            >
              {MODE_OPTIONS.map((mode) => (
                <option key={mode} value={mode}>
                  {modeLabel(mode)}
                </option>
              ))}
            </select>
          </div>
        </label>

        <label className="analysis-view__field">
          <span>{t('analyze_bpm')}</span>
          <div className="analysis-view__slider-row">
            <input
              type="range"
              min={40}
              max={240}
              value={value.bpm}
              onChange={(event) => onChange({ ...value, bpm: Number(event.target.value) })}
            />
            <strong>{value.bpm}</strong>
          </div>
        </label>

        <label className="analysis-view__field">
          <span>{t('analyze_time_sig')}</span>
          <select
            className="select-control"
            value={value.timeSignature}
            onChange={(event) => onChange({ ...value, timeSignature: event.target.value as TimeSignature })}
          >
            {TIME_SIGNATURE_OPTIONS.map((signature) => (
              <option key={signature} value={signature}>
                {signature}
              </option>
            ))}
          </select>
        </label>
      </div>

      <button className="btn btn--primary analysis-view__confirm" onClick={onConfirm}>
        {t('nav_next')}
      </button>
    </section>
  );
}
