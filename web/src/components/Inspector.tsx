import { useState } from 'react';
import { useI18n } from '../i18n.ts';
import InstrumentPicker from './InstrumentPicker.tsx';
import './Inspector.css';

export type CreativityLevelValue = 'conservative' | 'balanced' | 'creative';

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

interface InspectorProps {
  /* Analysis */
  analysisState: AnalysisFormState;
  onAnalysisChange: (next: AnalysisFormState) => void;
  /* Creativity */
  creativityLevel: CreativityLevelValue;
  onCreativityChange: (level: CreativityLevelValue) => void;
  /* Instruments */
  leadProgram: number;
  onLeadChange: (p: number) => void;
  bassProgram: number;
  onBassChange: (p: number) => void;
  harmonyProgram: number;
  onHarmonyChange: (p: number) => void;
  /* Export */
  hasArrangement: boolean;
  onExportMidi: () => void;
  onExportMp3: () => void;
  onExportLogic: () => void;
}

const KEY_OPTIONS = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
const MODE_OPTIONS: AnalysisFormState['mode'][] = ['major', 'minor', 'dorian', 'mixolydian'];
const TIME_SIG_OPTIONS: TimeSignature[] = ['3/4', '4/4', '6/8'];

export default function Inspector({
  analysisState,
  onAnalysisChange,
  creativityLevel,
  onCreativityChange,
  leadProgram,
  onLeadChange,
  bassProgram,
  onBassChange,
  harmonyProgram,
  onHarmonyChange,
  hasArrangement,
  onExportMidi,
  onExportMp3,
  onExportLogic,
}: InspectorProps) {
  const { t } = useI18n();
  const [openPanels, setOpenPanels] = useState<Record<string, boolean>>({
    analysis: true,
    creativity: false,
    instruments: false,
    processors: false,
    export: true,
  });

  const toggle = (panel: string) =>
    setOpenPanels((p) => ({ ...p, [panel]: !p[panel] }));

  /* Humanizer state (local to Inspector for now) */
  const [humanizerEnabled, setHumanizerEnabled] = useState(true);
  const [timingAmount, setTimingAmount] = useState(25);
  const [velocityAmount, setVelocityAmount] = useState(30);
  const [swingAmount, setSwingAmount] = useState(18);

  return (
    <div className="inspector">
      {/* ── Analysis ── */}
      <div className="inspector__section">
        <button className="inspector__header" onClick={() => toggle('analysis')}>
          <span>{openPanels.analysis ? '\u25BE' : '\u25B8'} {t('analyze_title').toUpperCase()}</span>
        </button>
        {openPanels.analysis && (
          <div className="inspector__body">
            <div className="inspector__row">
              <span className="inspector__label">{t('analyze_key')}</span>
              <div className="inspector__inline">
                <select
                  className="select-control"
                  value={analysisState.key}
                  onChange={(e) => onAnalysisChange({ ...analysisState, key: e.target.value })}
                >
                  {KEY_OPTIONS.map((k) => <option key={k} value={k}>{k}</option>)}
                </select>
                <select
                  className="select-control"
                  value={analysisState.mode}
                  onChange={(e) => onAnalysisChange({ ...analysisState, mode: e.target.value as AnalysisFormState['mode'] })}
                >
                  {MODE_OPTIONS.map((m) => <option key={m} value={m}>{m}</option>)}
                </select>
              </div>
            </div>
            <div className="inspector__row">
              <span className="inspector__label">BPM</span>
              <input
                type="number"
                className="select-control inspector__num"
                value={analysisState.bpm}
                min={40}
                max={240}
                onChange={(e) => {
                  const v = Number(e.target.value);
                  if (!isNaN(v) && v >= 40 && v <= 240)
                    onAnalysisChange({ ...analysisState, bpm: v });
                }}
              />
            </div>
            <div className="inspector__row">
              <span className="inspector__label">{t('analyze_time_sig')}</span>
              <select
                className="select-control"
                value={analysisState.timeSignature}
                onChange={(e) => onAnalysisChange({ ...analysisState, timeSignature: e.target.value as TimeSignature })}
              >
                {TIME_SIG_OPTIONS.map((ts) => <option key={ts} value={ts}>{ts}</option>)}
              </select>
            </div>
            <div className="inspector__stats">
              <span>{t('analyze_bars')}: <strong>{analysisState.bars}</strong></span>
              <span>{t('analyze_notes')}: <strong>{analysisState.notes}</strong></span>
              <span>{t('analyze_phrases')}: <strong>{analysisState.phrases}</strong></span>
            </div>
          </div>
        )}
      </div>

      {/* ── Creativity ── */}
      <div className="inspector__section">
        <button className="inspector__header" onClick={() => toggle('creativity')}>
          <span>{openPanels.creativity ? '\u25BE' : '\u25B8'} {t('arrange_creativity').toUpperCase()}</span>
        </button>
        {openPanels.creativity && (
          <div className="inspector__body">
            {(['conservative', 'balanced', 'creative'] as const).map((level) => (
              <label
                key={level}
                className={`inspector__radio ${creativityLevel === level ? 'inspector__radio--active' : ''}`}
              >
                <input
                  type="radio"
                  name="creativity"
                  value={level}
                  checked={creativityLevel === level}
                  onChange={() => onCreativityChange(level)}
                />
                <span className="inspector__radio-label">
                  {t(`arrange_${level}`)}
                </span>
              </label>
            ))}
          </div>
        )}
      </div>

      {/* ── Instruments ── */}
      <div className="inspector__section">
        <button className="inspector__header" onClick={() => toggle('instruments')}>
          <span>{openPanels.instruments ? '\u25BE' : '\u25B8'} {t('sidebar.instruments').toUpperCase()}</span>
        </button>
        {openPanels.instruments && (
          <div className="inspector__body">
            <InstrumentPicker label={t('sidebar.leadMelody')} selectedProgram={leadProgram} onChange={onLeadChange} />
            <InstrumentPicker label={t('sidebar.bass')} selectedProgram={bassProgram} onChange={onBassChange} />
            <InstrumentPicker label={t('sidebar.harmonyArp')} selectedProgram={harmonyProgram} onChange={onHarmonyChange} />
          </div>
        )}
      </div>

      {/* ── Processors / Humanizer ── */}
      <div className="inspector__section">
        <button className="inspector__header" onClick={() => toggle('processors')}>
          <span>{openPanels.processors ? '\u25BE' : '\u25B8'} {t('proc_humanizer').toUpperCase()}</span>
        </button>
        {openPanels.processors && (
          <div className="inspector__body">
            <label className="inspector__toggle">
              <input
                type="checkbox"
                checked={humanizerEnabled}
                onChange={(e) => setHumanizerEnabled(e.target.checked)}
              />
              <span>{t('proc_humanizer')}</span>
            </label>
            <div className="inspector__slider">
              <span>{t('proc_timing')}</span>
              <input type="range" min={0} max={100} value={timingAmount}
                onChange={(e) => setTimingAmount(Number(e.target.value))}
                disabled={!humanizerEnabled}
              />
              <strong>{timingAmount}%</strong>
            </div>
            <div className="inspector__slider">
              <span>{t('proc_velocity')}</span>
              <input type="range" min={0} max={100} value={velocityAmount}
                onChange={(e) => setVelocityAmount(Number(e.target.value))}
                disabled={!humanizerEnabled}
              />
              <strong>{velocityAmount}%</strong>
            </div>
            <div className="inspector__slider">
              <span>{t('proc_swing')}</span>
              <input type="range" min={0} max={100} value={swingAmount}
                onChange={(e) => setSwingAmount(Number(e.target.value))}
                disabled={!humanizerEnabled}
              />
              <strong>{swingAmount}%</strong>
            </div>
          </div>
        )}
      </div>

      {/* ── Export ── */}
      <div className="inspector__section">
        <button className="inspector__header" onClick={() => toggle('export')}>
          <span>{openPanels.export ? '\u25BE' : '\u25B8'} {t('export_title').toUpperCase()}</span>
        </button>
        {openPanels.export && (
          <div className="inspector__body">
            <button className="btn inspector__export-btn" onClick={onExportMidi} disabled={!hasArrangement}>
              {t('export_midi')}
            </button>
            <button className="btn inspector__export-btn" onClick={onExportMp3} disabled={!hasArrangement}>
              {t('export_mp3')}
            </button>
            <button className="btn inspector__export-btn" onClick={onExportLogic} disabled={!hasArrangement}>
              {t('export_logic')}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
