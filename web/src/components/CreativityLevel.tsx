import { useI18n } from '../i18n.ts';
import './CreativityLevel.css';

export type CreativityLevelValue = 'conservative' | 'balanced' | 'creative';

interface CreativityLevelProps {
  level: CreativityLevelValue;
  onChange: (level: CreativityLevelValue) => void;
}

const CREATIVITY_OPTIONS: Array<{ value: CreativityLevelValue; icon: string; key: string }> = [
  { value: 'conservative', icon: '\u{1F3AF}', key: 'arrange_conservative' },
  { value: 'balanced', icon: '\u2696\uFE0F', key: 'arrange_balanced' },
  { value: 'creative', icon: '\u{1F3A8}', key: 'arrange_creative' },
];

export default function CreativityLevel({ level, onChange }: CreativityLevelProps) {
  const { t } = useI18n();

  return (
    <section className="creativity-level" aria-label={t('arrange_creativity')}>
      <div className="creativity-level__header">{t('arrange_creativity')}</div>
      <div className="creativity-level__grid" role="group" aria-label={t('arrange_creativity')}>
        {CREATIVITY_OPTIONS.map((option) => {
          const isActive = level === option.value;
          return (
            <button
              type="button"
              key={option.value}
              className={`creativity-level__card ${isActive ? 'creativity-level__card--active' : ''}`}
              onClick={() => onChange(option.value)}
              aria-pressed={isActive}
            >
              <span className="creativity-level__icon" aria-hidden="true">{option.icon}</span>
              <span className="creativity-level__title">{t(option.key)}</span>
            </button>
          );
        })}
      </div>
    </section>
  );
}
