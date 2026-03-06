import { useMemo, useState } from 'react';
import { useI18n } from '../i18n.ts';
import './ExportView.css';

type ExportFormat = 'midi' | 'mp3' | 'logic';

interface ExportViewProps {
  isReady: boolean;
  onExportMidi: () => void;
  onExportMp3: () => void;
  onExportLogic: () => void;
}

const EXPORT_ICONS: Record<ExportFormat, string> = {
  midi: '\u{1F3BC}',
  mp3: '\u{1F3A7}',
  logic: '\u{1F3B9}',
};

export default function ExportView({
  isReady,
  onExportMidi,
  onExportMp3,
  onExportLogic,
}: ExportViewProps) {
  const { t } = useI18n();
  const [format, setFormat] = useState<ExportFormat>('midi');
  const [humanizerEnabled, setHumanizerEnabled] = useState(true);
  const [timingAmount, setTimingAmount] = useState(25);
  const [velocityAmount, setVelocityAmount] = useState(30);
  const [swingAmount, setSwingAmount] = useState(18);

  const formatCards = useMemo(
    () => [
      {
        id: 'midi' as const,
        title: t('export_midi'),
        description: 'Standard DAW workflow and editable notes.',
      },
      {
        id: 'mp3' as const,
        title: t('export_mp3'),
        description: 'Quick listening draft for sharing.',
      },
      {
        id: 'logic' as const,
        title: t('export_logic'),
        description: 'Session package optimized for Logic Pro.',
      },
    ],
    [t],
  );

  const handleExport = () => {
    if (format === 'midi') onExportMidi();
    if (format === 'mp3') onExportMp3();
    if (format === 'logic') onExportLogic();
  };

  return (
    <section className="export-view">
      <header className="export-view__header">
        <h2>{t('export_title')}</h2>
        <p>{t('success')}: {isReady ? 'Arrangement ready' : 'Generate arrangement first'}</p>
      </header>

      <div className="export-view__cards">
        {formatCards.map((card) => {
          const active = format === card.id;
          return (
            <button
              type="button"
              key={card.id}
              className={`export-view__card ${active ? 'export-view__card--active' : ''}`}
              onClick={() => setFormat(card.id)}
            >
              <span className="export-view__icon">{EXPORT_ICONS[card.id]}</span>
              <span className="export-view__card-title">{card.title}</span>
              <span className="export-view__card-desc">{card.description}</span>
            </button>
          );
        })}
      </div>

      <div className="export-view__processors">
        <label className="export-view__toggle">
          <input
            type="checkbox"
            checked={humanizerEnabled}
            onChange={(event) => setHumanizerEnabled(event.target.checked)}
          />
          <span>{t('proc_humanizer')}</span>
        </label>

        <label className="export-view__slider">
          <span>{t('proc_timing')}</span>
          <input
            type="range"
            min={0}
            max={100}
            value={timingAmount}
            onChange={(event) => setTimingAmount(Number(event.target.value))}
            disabled={!humanizerEnabled}
          />
          <strong>{timingAmount}%</strong>
        </label>

        <label className="export-view__slider">
          <span>{t('proc_velocity')}</span>
          <input
            type="range"
            min={0}
            max={100}
            value={velocityAmount}
            onChange={(event) => setVelocityAmount(Number(event.target.value))}
            disabled={!humanizerEnabled}
          />
          <strong>{velocityAmount}%</strong>
        </label>

        <label className="export-view__slider">
          <span>{t('proc_swing')}</span>
          <input
            type="range"
            min={0}
            max={100}
            value={swingAmount}
            onChange={(event) => setSwingAmount(Number(event.target.value))}
            disabled={!humanizerEnabled}
          />
          <strong>{swingAmount}%</strong>
        </label>
      </div>

      <button className="btn btn--primary export-view__download" onClick={handleExport} disabled={!isReady}>
        {t('nav_next')} · {formatCards.find((card) => card.id === format)?.title}
      </button>
    </section>
  );
}
