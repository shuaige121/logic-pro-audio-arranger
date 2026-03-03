import { useState, useRef, useCallback } from 'react';
import { useI18n } from '../i18n.ts';
import './FileUpload.css';

interface FileUploadProps {
  onFileSelected: (file: File) => void;
  isProcessing: boolean;
  error: string | null;
  supportedFormats: string[];
  sourceType?: string;
  onSourceTypeChange?: (type: string) => void;
}

const SOURCE_TYPE_OPTIONS = [
  { value: 'vocal', label: 'Vocal', description: 'Acapella' },
  { value: 'piano', label: 'Piano', description: 'Piano recording' },
  { value: 'guitar', label: 'Guitar', description: 'Guitar recording' },
  { value: 'other', label: 'Other', description: 'Other instrument' },
] as const;

export default function FileUpload({
  onFileSelected,
  isProcessing,
  error,
  supportedFormats,
  sourceType,
  onSourceTypeChange,
}: FileUploadProps) {
  const { t } = useI18n();
  const [isDragOver, setIsDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const selectedSourceType = sourceType ?? 'vocal';

  const acceptString = supportedFormats.join(',');

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) onFileSelected(file);
  }, [onFileSelected]);

  const handleClick = () => inputRef.current?.click();

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) onFileSelected(file);
    e.target.value = '';
  };

  return (
    <div className="file-upload-panel">
      <div
        className={`file-upload ${isDragOver ? 'file-upload--drag-over' : ''} ${isProcessing ? 'file-upload--processing' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleClick}
      >
        <input ref={inputRef} type="file" className="file-upload__input" accept={acceptString} onChange={handleInputChange} />

        {isProcessing ? (
          <div className="file-upload__processing">
            <div className="file-upload__spinner" />
            <span className="file-upload__processing-text">{t('upload.analyzing')}</span>
          </div>
        ) : (
          <>
            <div className="file-upload__title">{isDragOver ? t('upload.dropHere') : t('upload.dragDrop')}</div>
            <div className="file-upload__subtitle">{t('upload.clickBrowse')}</div>
            <div className="file-upload__formats">{t('upload.formats')}</div>
          </>
        )}

        {error && <div className="file-upload__error">{error}</div>}
      </div>

      <div className="file-upload__source-type">
        <div className="file-upload__source-title">Source Type</div>
        <div className="file-upload__source-options">
          {SOURCE_TYPE_OPTIONS.map((option) => (
            <label
              key={option.value}
              className={`file-upload__source-option ${selectedSourceType === option.value ? 'file-upload__source-option--active' : ''}`}
            >
              <input
                type="radio"
                name="source-type"
                value={option.value}
                checked={selectedSourceType === option.value}
                onChange={() => onSourceTypeChange?.(option.value)}
                className="file-upload__source-radio"
              />
              <span className="file-upload__source-label">{option.label}</span>
              <span className="file-upload__source-desc">{option.description}</span>
            </label>
          ))}
        </div>
      </div>
    </div>
  );
}
