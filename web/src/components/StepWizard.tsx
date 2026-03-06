import type { ReactNode } from 'react';
import { useI18n } from '../i18n.ts';
import './StepWizard.css';

interface StepWizardProps {
  currentStep: number;
  onBack: () => void;
  onNext: () => void;
  canGoBack: boolean;
  canGoNext: boolean;
  children: ReactNode;
}

const STEP_NUMBERS = [1, 2, 3, 4, 5] as const;

export default function StepWizard({
  currentStep,
  onBack,
  onNext,
  canGoBack,
  canGoNext,
  children,
}: StepWizardProps) {
  const { t } = useI18n();

  const stepTitles = [
    t('step_upload'),
    t('step_analyze'),
    t('step_arrange'),
    t('step_edit'),
    t('step_export'),
  ];

  return (
    <div className="step-wizard">
      <div className="step-wizard__header">
        {STEP_NUMBERS.map((step, index) => {
          const isActive = step === currentStep;
          const isCompleted = step < currentStep;
          return (
            <div
              key={step}
              className={`step-wizard__step ${isActive ? 'step-wizard__step--active' : ''} ${isCompleted ? 'step-wizard__step--completed' : ''}`}
            >
              <div className="step-wizard__bubble">
                {isCompleted ? '\u2713' : step}
              </div>
              <span className="step-wizard__label">{stepTitles[index]}</span>
            </div>
          );
        })}
      </div>

      <div className="step-wizard__body">{children}</div>

      <div className="step-wizard__footer">
        <button className="btn" onClick={onBack} disabled={!canGoBack}>
          {t('nav_back')}
        </button>
        <button className="btn btn--primary" onClick={onNext} disabled={!canGoNext}>
          {t('nav_next')}
        </button>
      </div>
    </div>
  );
}
