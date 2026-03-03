import { useI18n } from '../i18n.ts';
import LanguageSwitcher from './LanguageSwitcher.tsx';
import './ControlBar.css';

interface ControlBarProps {
  isPlaying: boolean;
  currentBeat: number;
  beatsPerBar: number;
  tempo: number;
  bars: number;
  style: 'pop' | 'modal' | 'jazz';
  complexity: 'basic' | 'rich';
  keyName: string | null;
  modeName: string | null;
  isGenerating: boolean;
  onPlay: () => void;
  onStop: () => void;
  onTempoChange: (t: number) => void;
  onBarsChange: (b: number) => void;
  onStyleChange: (s: 'pop' | 'modal' | 'jazz') => void;
  onComplexityChange: (c: 'basic' | 'rich') => void;
  onGenerate: () => void;
  onBack: () => void;
}

function formatPosition(currentBeat: number, beatsPerBar: number): string {
  const bar = Math.floor(currentBeat / beatsPerBar) + 1;
  const beat = Math.floor(currentBeat % beatsPerBar) + 1;
  const tick = Math.round((currentBeat % 1) * 1000);
  return `${String(bar).padStart(3, '0')}:${String(beat).padStart(2, '0')}:${String(tick).padStart(3, '0')}`;
}

export default function ControlBar({
  isPlaying,
  currentBeat,
  beatsPerBar,
  tempo,
  bars,
  style,
  complexity,
  keyName,
  modeName,
  isGenerating,
  onPlay,
  onStop,
  onTempoChange,
  onBarsChange,
  onStyleChange,
  onComplexityChange,
  onGenerate,
  onBack,
}: ControlBarProps) {
  const { t } = useI18n();

  return (
    <div className="control-bar">
      {/* Transport buttons */}
      <div className="control-bar__transport">
        <button
          className="control-bar__btn"
          title={t('transport.rewind')}
          onClick={onStop}
        >
          &#x25C1;
        </button>
        <button
          className={`control-bar__btn control-bar__btn--play ${isPlaying ? 'control-bar__btn--active' : ''}`}
          title={isPlaying ? t('transport.pause') : t('transport.play')}
          onClick={onPlay}
        >
          {isPlaying ? '\u25A0' : '\u25B6'}
        </button>
        <button
          className="control-bar__btn"
          title={t('transport.stop')}
          onClick={onStop}
        >
          &#x25A0;
        </button>
      </div>

      {/* LCD Display */}
      <div className="control-bar__lcd">
        <span className="control-bar__position">
          {formatPosition(currentBeat, beatsPerBar)}
        </span>
      </div>

      {/* BPM */}
      <div className="control-bar__lcd control-bar__lcd--bpm">
        <span className="control-bar__bpm-icon">{'\u2669'}</span>
        <input
          type="number"
          className="control-bar__bpm-input"
          value={tempo}
          min={40}
          max={240}
          onChange={(e) => {
            const v = Number(e.target.value);
            if (!isNaN(v) && v >= 40 && v <= 240) onTempoChange(v);
          }}
        />
      </div>

      {/* Time sig + Key */}
      <div className="control-bar__info">
        <select
          className="control-bar__select"
          value={bars}
          onChange={(e) => {
            const v = Number(e.target.value);
            if (v >= 2 && v <= 32) onBarsChange(v);
          }}
        >
          {Array.from({ length: 31 }, (_, i) => i + 2).map((b) => (
            <option key={b} value={b}>{b} bars</option>
          ))}
        </select>
        {keyName && (
          <span className="control-bar__key">
            {keyName} {modeName}
          </span>
        )}
      </div>

      {/* Style + Complexity */}
      <div className="control-bar__params">
        <select
          className="control-bar__select"
          value={style}
          onChange={(e) => onStyleChange(e.target.value as 'pop' | 'modal' | 'jazz')}
        >
          <option value="pop">{t('transport.stylePop')}</option>
          <option value="modal">{t('transport.styleModal')}</option>
          <option value="jazz">{t('transport.styleJazz')}</option>
        </select>
        <select
          className="control-bar__select"
          value={complexity}
          onChange={(e) => onComplexityChange(e.target.value as 'basic' | 'rich')}
        >
          <option value="basic">{t('transport.complexityBasic')}</option>
          <option value="rich">{t('transport.complexityRich')}</option>
        </select>
      </div>

      {/* Generate */}
      <button
        className="btn btn--primary control-bar__generate"
        onClick={onGenerate}
        disabled={isGenerating}
      >
        {isGenerating ? t('arrange_generating') : t('arrange_generate')}
      </button>

      {/* Right: lang + back */}
      <div className="control-bar__right">
        <LanguageSwitcher />
        <button className="btn btn--small" onClick={onBack}>
          {t('nav_back_to_site')}
        </button>
      </div>
    </div>
  );
}
