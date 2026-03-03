import { useState } from 'react';
import { useI18n } from '../i18n.ts';
import FileUpload from './FileUpload.tsx';
import { SUPPORTED_EXTENSIONS } from '../engine/index.ts';
import './ProjectChooser.css';

interface ProjectChooserProps {
  onFileSelected: (file: File) => void;
  isProcessing: boolean;
  uploadError: string | null;
  sourceType: string;
  onSourceTypeChange: (type: string) => void;
  onLoadDemo: () => void;
  onDrawManually: () => void;
  tempo: number;
  onTempoChange: (v: number) => void;
  keyName: string;
  onKeyChange: (v: string) => void;
  timeSignature: string;
  onTimeSignatureChange: (v: string) => void;
}

const KEY_OPTIONS = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
const TIME_SIG_OPTIONS = ['3/4', '4/4', '6/8'];

export default function ProjectChooser({
  onFileSelected,
  isProcessing,
  uploadError,
  sourceType,
  onSourceTypeChange,
  onLoadDemo,
  onDrawManually,
  tempo,
  onTempoChange,
  keyName,
  onKeyChange,
  timeSignature,
  onTimeSignatureChange,
}: ProjectChooserProps) {
  const { t } = useI18n();
  const [showSettings, setShowSettings] = useState(false);

  return (
    <div className="project-chooser">
      <div className="project-chooser__panel">
        <h1 className="project-chooser__title">Arranger</h1>
        <p className="project-chooser__subtitle">{t('upload_subtitle')}</p>

        <FileUpload
          onFileSelected={onFileSelected}
          isProcessing={isProcessing}
          error={uploadError}
          supportedFormats={SUPPORTED_EXTENSIONS}
          sourceType={sourceType}
          onSourceTypeChange={onSourceTypeChange}
        />

        <div className="project-chooser__actions">
          <button className="btn btn--outline" onClick={onLoadDemo}>
            {t('upload_demo')}
          </button>
          <button className="btn btn--outline" onClick={onDrawManually}>
            {t('upload_draw')}
          </button>
        </div>

        <div className="project-chooser__settings-bar">
          <button
            className="project-chooser__settings-toggle"
            onClick={() => setShowSettings((p) => !p)}
          >
            {showSettings ? '\u25BE' : '\u25B8'} Project Settings
          </button>

          {showSettings && (
            <div className="project-chooser__settings">
              <div className="project-chooser__setting">
                <span className="control-label">BPM</span>
                <input
                  type="number"
                  className="select-control"
                  value={tempo}
                  min={40}
                  max={240}
                  onChange={(e) => {
                    const v = Number(e.target.value);
                    if (!isNaN(v) && v >= 40 && v <= 240) onTempoChange(v);
                  }}
                />
              </div>
              <div className="project-chooser__setting">
                <span className="control-label">Key</span>
                <select
                  className="select-control"
                  value={keyName}
                  onChange={(e) => onKeyChange(e.target.value)}
                >
                  {KEY_OPTIONS.map((k) => (
                    <option key={k} value={k}>{k}</option>
                  ))}
                </select>
              </div>
              <div className="project-chooser__setting">
                <span className="control-label">Time Sig</span>
                <select
                  className="select-control"
                  value={timeSignature}
                  onChange={(e) => onTimeSignatureChange(e.target.value)}
                >
                  {TIME_SIG_OPTIONS.map((ts) => (
                    <option key={ts} value={ts}>{ts}</option>
                  ))}
                </select>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
