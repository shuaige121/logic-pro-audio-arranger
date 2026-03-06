import { useI18n } from '../i18n.ts';
import './TransportControls.css';

interface TransportControlsProps {
  isPlaying: boolean;
  tempo: number;
  style: 'pop' | 'modal' | 'jazz';
  complexity: 'basic' | 'rich';
  bars: number;
  currentBeat: number;
  beatsPerBar: number;
  onPlay: () => void;
  onStop: () => void;
  onTempoChange: (tempo: number) => void;
  onStyleChange: (style: 'pop' | 'modal' | 'jazz') => void;
  onComplexityChange: (complexity: 'basic' | 'rich') => void;
  onBarsChange: (bars: number) => void;
  onGenerate: () => void;
  isGenerating: boolean;
}

function formatPosition(currentBeat: number, beatsPerBar: number): string {
  const bar = Math.floor(currentBeat / beatsPerBar) + 1;
  const beat = Math.floor(currentBeat % beatsPerBar) + 1;
  return `${String(bar).padStart(3, '0')}:${String(beat).padStart(2, '0')}`;
}

export default function TransportControls({
  isPlaying,
  tempo,
  style,
  complexity,
  bars,
  currentBeat,
  beatsPerBar,
  onPlay,
  onStop,
  onTempoChange,
  onStyleChange,
  onComplexityChange,
  onBarsChange,
  onGenerate,
  isGenerating,
}: TransportControlsProps) {
  const { t } = useI18n();

  return (
    <div className="transport-bar">
      <div className="transport-bar__title">{t('arrange_title')}</div>

      <div className="transport-bar__buttons">
        <button className="btn btn--icon transport-bar__btn" title={t('transport.rewind')} onClick={onStop}>
          {'\u23EE'}
        </button>
        <button
          className={`btn btn--icon transport-bar__btn ${isPlaying ? 'transport-bar__btn--pause' : 'transport-bar__btn--play'}`}
          title={isPlaying ? t('transport.pause') : t('transport.play')}
          onClick={onPlay}
        >
          {isPlaying ? '\u23F8' : '\u25B6'}
        </button>
        <button className="btn btn--icon transport-bar__btn" title={t('transport.stop')} onClick={onStop}>
          {'\u23F9'}
        </button>
      </div>

      <div className="transport-bar__position">
        <span className="transport-bar__position-value">{formatPosition(currentBeat, beatsPerBar)}</span>
      </div>

      <div className="transport-bar__params">
        <div className="param-group">
          <span className="control-label">{t('analyze_bpm')}</span>
          <input
            type="number"
            className="select-control transport-bar__tempo-input"
            value={tempo}
            min={40}
            max={240}
            onChange={(e) => {
              const value = Number(e.target.value);
              if (!Number.isNaN(value) && value >= 40 && value <= 240) onTempoChange(value);
            }}
          />
        </div>

        <div className="param-group">
          <span className="control-label">{t('transport.bars')}</span>
          <input
            type="number"
            className="select-control transport-bar__bars-input"
            value={bars}
            min={2}
            max={32}
            onChange={(e) => {
              const value = Number(e.target.value);
              if (!Number.isNaN(value) && value >= 2 && value <= 32) onBarsChange(value);
            }}
          />
        </div>

        <div className="param-group">
          <span className="control-label">{t('arrange_style')}</span>
          <select
            className="select-control"
            value={style}
            onChange={(e) => onStyleChange(e.target.value as 'pop' | 'modal' | 'jazz')}
          >
            <option value="pop">{t('transport.stylePop')}</option>
            <option value="modal">{t('transport.styleModal')}</option>
            <option value="jazz">{t('transport.styleJazz')}</option>
          </select>
        </div>

        <div className="param-group">
          <span className="control-label">{t('transport.complexity')}</span>
          <select
            className="select-control"
            value={complexity}
            onChange={(e) => onComplexityChange(e.target.value as 'basic' | 'rich')}
          >
            <option value="basic">{t('transport.complexityBasic')}</option>
            <option value="rich">{t('transport.complexityRich')}</option>
          </select>
        </div>
      </div>

      <div className="transport-bar__actions">
        <button className="btn btn--primary" onClick={onGenerate} disabled={isGenerating}>
          {isGenerating ? t('arrange_generating') : t('arrange_generate')}
        </button>
      </div>
    </div>
  );
}
