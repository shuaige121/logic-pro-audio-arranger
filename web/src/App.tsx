import { useState, useCallback, useRef, useEffect } from 'react';
import type { NoteEvent, Arrangement, KeyEstimate, HarmonyCandidate } from './types/music.ts';
import {
  arrangementToMidi,
  downloadMidi,
  PlaybackEngine,
  parseFile,
  generateArrangementWithAI,
  SUPPORTED_EXTENSIONS,
  estimateKey,
  detectPhrasesInfo,
  nameToPitchClass,
} from './engine/index.ts';
import { useI18n } from './i18n.ts';
import StepWizard from './components/StepWizard.tsx';
import FileUpload from './components/FileUpload.tsx';
import AnalysisView from './components/AnalysisView.tsx';
import type { AnalysisFormState } from './components/AnalysisView.tsx';
import ArrangeView from './components/ArrangeView.tsx';
import TrackList from './components/TrackList.tsx';
import type { TrackState } from './components/TrackList.tsx';
import ArrangementView from './components/ArrangementView.tsx';
import InstrumentPicker from './components/InstrumentPicker.tsx';
import MidiPlayer from './components/MidiPlayer.tsx';
import PianoRoll from './components/PianoRoll.tsx';
import ExportView from './components/ExportView.tsx';
import LanguageSwitcher from './components/LanguageSwitcher.tsx';
import type { CreativityLevelValue } from './components/CreativityLevel.tsx';
import './App.css';

function createDemoNotes(tempoBpm: number): NoteEvent[] {
  const secondsPerBeat = 60 / tempoBpm;
  const pitches = [60, 62, 64, 65, 67, 69, 71, 72];
  return pitches.map((pitch, index) => ({
    pitch,
    start: index * secondsPerBeat,
    duration: secondsPerBeat * 0.9,
    velocity: 100,
  }));
}

function App() {
  const { t } = useI18n();

  const [currentStep, setCurrentStep] = useState(1);
  const [sourceFileName, setSourceFileName] = useState<string | null>(null);

  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [sourceType, setSourceType] = useState<string>('vocal');

  const [notes, setNotes] = useState<NoteEvent[]>([]);
  const [arrangement, setArrangement] = useState<Arrangement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentBeat, setCurrentBeat] = useState(0);
  const [tempo, setTempo] = useState(120);
  const [style, setStyle] = useState<'pop' | 'modal' | 'jazz'>('pop');
  const [complexity, setComplexity] = useState<'basic' | 'rich'>('basic');
  const [creativityLevel, setCreativityLevel] = useState<CreativityLevelValue>('balanced');
  const [bars, setBars] = useState(8);
  const [isGenerating, setIsGenerating] = useState(false);

  const [leadProgram, setLeadProgram] = useState(80);
  const [bassProgram, setBassProgram] = useState(33);
  const [harmonyProgram, setHarmonyProgram] = useState(0);

  const [keyEstimate, setKeyEstimate] = useState<KeyEstimate | null>(null);
  const [harmony, setHarmony] = useState<HarmonyCandidate | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showInstrumentPanel, setShowInstrumentPanel] = useState(false);

  const [selectedTrack, setSelectedTrack] = useState<string | null>(null);
  const [trackStates, setTrackStates] = useState<Record<string, TrackState>>({});
  const [showPianoRoll, setShowPianoRoll] = useState(true);
  const [showMidiPlayer, setShowMidiPlayer] = useState(true);

  const [analysisState, setAnalysisState] = useState<AnalysisFormState>({
    key: 'C',
    mode: 'major',
    bpm: 120,
    timeSignature: '4/4',
    bars: 8,
    notes: 0,
    phrases: 0,
  });

  const beatsPerBar = analysisState.timeSignature === '3/4' ? 3 : analysisState.timeSignature === '6/8' ? 6 : 4;

  const playbackRef = useRef<PlaybackEngine | null>(null);
  const animFrameRef = useRef<number>(0);
  const loadedArrangementRef = useRef<Arrangement | null>(null);

  const getPlaybackEngine = useCallback((): PlaybackEngine => {
    if (!playbackRef.current) playbackRef.current = new PlaybackEngine();
    return playbackRef.current;
  }, []);

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  useEffect(() => {
    if (!arrangement) return;
    setTrackStates((prev) => {
      const next: Record<string, TrackState> = {};
      for (const track of arrangement.tracks) {
        next[track.name] = prev[track.name] || { muted: false, soloed: false, volume: 0.8 };
      }
      return next;
    });
    if (!selectedTrack && arrangement.tracks.length > 0) {
      setSelectedTrack(arrangement.tracks[0].name);
    }
  }, [arrangement, selectedTrack]);

  useEffect(() => {
    if (!isPlaying) {
      cancelAnimationFrame(animFrameRef.current);
      return;
    }
    const engine = playbackRef.current;
    if (!engine) return;

    const secondsPerBeat = 60 / tempo;
    const tick = () => {
      const position = engine.getPosition();
      setCurrentBeat(position / secondsPerBeat);
      if (position >= engine.getDuration() && engine.getDuration() > 0) {
        engine.stop();
        setIsPlaying(false);
        setCurrentBeat(0);
        return;
      }
      animFrameRef.current = requestAnimationFrame(tick);
    };

    animFrameRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(animFrameRef.current);
  }, [isPlaying, tempo]);

  useEffect(() => {
    return () => {
      playbackRef.current?.dispose();
    };
  }, []);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (currentStep < 3) return;
      if (
        event.target instanceof HTMLInputElement ||
        event.target instanceof HTMLSelectElement ||
        event.target instanceof HTMLTextAreaElement
      ) {
        return;
      }
      if (event.code === 'Space') {
        event.preventDefault();
        void handlePlay();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentStep]);

  const applyParsedMelody = useCallback((parsedNotes: NoteEvent[], tempoBpm: number, fileName: string | null) => {
    const roundedTempo = Math.max(40, Math.min(240, Math.round(tempoBpm)));
    const phraseCount = parsedNotes.length > 0 ? detectPhrasesInfo(parsedNotes, 60 / roundedTempo).length : 0;
    const maxNoteEnd = parsedNotes.length > 0
      ? Math.max(...parsedNotes.map((note) => note.start + note.duration))
      : 0;
    const inferredBars = parsedNotes.length > 0
      ? Math.max(4, Math.ceil(maxNoteEnd / (60 / roundedTempo * 4)))
      : 8;
    const nextBars = Math.min(32, inferredBars);
    const detectedKey = parsedNotes.length > 0 ? estimateKey(parsedNotes) : null;

    setNotes(parsedNotes);
    setTempo(roundedTempo);
    setBars(nextBars);
    setSourceFileName(fileName);
    setArrangement(null);
    setKeyEstimate(detectedKey);
    setHarmony(null);
    setCurrentBeat(0);
    setIsPlaying(false);
    playbackRef.current?.stop();
    setAnalysisState({
      key: detectedKey?.tonicName ?? 'C',
      mode: detectedKey?.mode ?? 'major',
      bpm: roundedTempo,
      timeSignature: '4/4',
      bars: nextBars,
      notes: parsedNotes.length,
      phrases: phraseCount,
    });
    setCurrentStep(2);
  }, []);

  const handleFileSelected = useCallback(async (file: File) => {
    setIsUploading(true);
    setUploadError(null);
    try {
      const result = await parseFile(file, style);
      if (result.notes.length === 0) throw new Error(t('upload.noNotes'));
      applyParsedMelody(result.notes, result.tempoBpm, file.name);
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Failed to parse file');
    } finally {
      setIsUploading(false);
    }
  }, [style, t, applyParsedMelody]);

  const handleLoadDemo = useCallback(() => {
    applyParsedMelody(createDemoNotes(120), 120, t('demo.name'));
  }, [t, applyParsedMelody]);

  const handleStartManual = useCallback(() => {
    playbackRef.current?.stop();
    setIsPlaying(false);
    setCurrentBeat(0);
    setNotes([]);
    setArrangement(null);
    setKeyEstimate(null);
    setHarmony(null);
    setTempo(120);
    setBars(8);
    setSourceFileName(t('upload_draw'));
    setAnalysisState({
      key: 'C',
      mode: 'major',
      bpm: 120,
      timeSignature: '4/4',
      bars: 8,
      notes: 0,
      phrases: 0,
    });
    setCurrentStep(4);
  }, [t]);

  const handleAnalysisConfirm = useCallback(() => {
    try {
      const tonicPc = nameToPitchClass(analysisState.key);
      setTempo(analysisState.bpm);
      setBars(analysisState.bars);
      setKeyEstimate({
        tonicPc,
        tonicName: analysisState.key,
        mode: analysisState.mode,
        score: keyEstimate?.score ?? 1,
      });
      setCurrentStep(3);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('error'));
    }
  }, [analysisState, keyEstimate, t]);

  const handlePlay = useCallback(async () => {
    try {
      const engine = getPlaybackEngine();
      if (isPlaying) {
        engine.pause();
        setIsPlaying(false);
      } else {
        await engine.init();
        if (arrangement && arrangement !== loadedArrangementRef.current) {
          engine.loadArrangement(arrangement);
          loadedArrangementRef.current = arrangement;
        }
        engine.play();
        setIsPlaying(true);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : t('error.playbackFailed'));
    }
  }, [isPlaying, arrangement, getPlaybackEngine, t]);

  const handleStop = useCallback(() => {
    try {
      playbackRef.current?.stop();
      setIsPlaying(false);
      setCurrentBeat(0);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('error.stopFailed'));
    }
  }, [t]);

  const handleGenerate = useCallback(async () => {
    if (notes.length === 0) {
      setError(t('error.noNotes'));
      return;
    }
    setIsGenerating(true);
    setError(null);
    try {
      const result = await generateArrangementWithAI(notes, tempo, bars, style, complexity, beatsPerBar);
      const nextArrangement = result.arrangement;

      for (const track of nextArrangement.tracks) {
        if (track.name === 'Lead Melody') track.program = leadProgram;
        else if (track.name === 'Bass') track.program = bassProgram;
        else if (track.name === 'Harmony' || track.name === 'Arp Keys') track.program = harmonyProgram;
      }

      setArrangement(nextArrangement);
      setKeyEstimate(result.key);
      setHarmony(result.harmony);
      loadedArrangementRef.current = null;
      setCurrentStep(4);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('error'));
    } finally {
      setIsGenerating(false);
    }
  }, [notes, tempo, bars, style, complexity, beatsPerBar, leadProgram, bassProgram, harmonyProgram, t]);

  const handleTempoChange = useCallback((nextTempo: number) => {
    setTempo(nextTempo);
    setAnalysisState((prev) => ({ ...prev, bpm: nextTempo }));
  }, []);

  const handleBarsChange = useCallback((nextBars: number) => {
    setBars(nextBars);
    setAnalysisState((prev) => ({ ...prev, bars: nextBars }));
  }, []);

  const handleDownloadMidi = useCallback(() => {
    if (!arrangement) {
      setError(t('error.generateFirst'));
      return;
    }
    try {
      const midi = arrangementToMidi(arrangement);
      downloadMidi(midi, `arrangement-${arrangement.style}-${arrangement.bars}bars.mid`);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('error.midiExport'));
    }
  }, [arrangement, t]);

  const handleExportMp3 = useCallback(() => {
    if (!arrangement) {
      setError(t('error.generateFirst'));
      return;
    }
    setError('MP3 export is not available yet in browser mode.');
  }, [arrangement, t]);

  const handleExportLogic = useCallback(() => {
    if (!arrangement) {
      setError(t('error.generateFirst'));
      return;
    }
    const payload = {
      type: 'logic-pro-kit',
      arrangement,
      keyEstimate,
      harmony,
      exportedAt: new Date().toISOString(),
    };

    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `logic-pro-kit-${arrangement.style}-${arrangement.bars}bars.json`;
    document.body.appendChild(anchor);
    anchor.click();
    document.body.removeChild(anchor);
    URL.revokeObjectURL(url);
  }, [arrangement, keyEstimate, harmony, t]);

  const handleMuteToggle = useCallback((name: string) => {
    setTrackStates((prev) => {
      const state = prev[name] || { muted: false, soloed: false, volume: 0.8 };
      const next = { ...prev, [name]: { ...state, muted: !state.muted } };
      playbackRef.current?.setTrackMute(name, !state.muted);
      return next;
    });
  }, []);

  const handleSoloToggle = useCallback((name: string) => {
    setTrackStates((prev) => {
      const state = prev[name] || { muted: false, soloed: false, volume: 0.8 };
      const next = { ...prev, [name]: { ...state, soloed: !state.soloed } };
      playbackRef.current?.setTrackSolo(name, !state.soloed);
      return next;
    });
  }, []);

  const handleVolumeChange = useCallback((name: string, volume: number) => {
    setTrackStates((prev) => {
      const state = prev[name] || { muted: false, soloed: false, volume: 0.8 };
      return { ...prev, [name]: { ...state, volume } };
    });
    playbackRef.current?.setTrackVolume(name, volume);
  }, []);

  const canGoBack = currentStep > 1;
  const canGoNext =
    currentStep === 1 ? notes.length > 0 :
      currentStep === 2 ? true :
        currentStep === 3 ? arrangement !== null :
          currentStep === 4;

  const handleWizardBack = useCallback(() => {
    setCurrentStep((prev) => Math.max(1, prev - 1));
  }, []);

  const handleWizardNext = useCallback(() => {
    if (currentStep === 2) {
      handleAnalysisConfirm();
      return;
    }
    if (currentStep >= 5) return;
    setCurrentStep((prev) => Math.min(5, prev + 1));
  }, [currentStep, handleAnalysisConfirm]);

  const renderCurrentStep = () => {
    if (currentStep === 1) {
      return (
        <section className="upload-step">
          <h1 className="upload-step__title">{t('upload_title')}</h1>
          <p className="upload-step__subtitle">{t('upload_subtitle')}</p>
          <p className="upload-step__formats">{t('upload_formats')}</p>

          <FileUpload
            onFileSelected={handleFileSelected}
            isProcessing={isUploading}
            error={uploadError}
            supportedFormats={SUPPORTED_EXTENSIONS}
            sourceType={sourceType}
            onSourceTypeChange={setSourceType}
          />

          <div className="upload-step__alt">
            <span>{t('upload_or')}</span>
            <div className="upload-step__alt-buttons">
              <button className="btn btn--outline" onClick={handleLoadDemo}>{t('upload_demo')}</button>
              <button className="btn btn--outline" onClick={handleStartManual}>{t('upload_draw')}</button>
            </div>
          </div>
        </section>
      );
    }

    if (currentStep === 2) {
      return (
        <AnalysisView
          value={analysisState}
          onChange={setAnalysisState}
          onConfirm={handleAnalysisConfirm}
        />
      );
    }

    if (currentStep === 3) {
      return (
        <ArrangeView
          creativityLevel={creativityLevel}
          onCreativityChange={setCreativityLevel}
          transport={{
            isPlaying,
            tempo,
            style,
            complexity,
            bars,
            currentBeat,
            beatsPerBar,
            onPlay: () => { void handlePlay(); },
            onStop: handleStop,
            onTempoChange: handleTempoChange,
            onStyleChange: setStyle,
            onComplexityChange: setComplexity,
            onBarsChange: handleBarsChange,
            onGenerate: () => { void handleGenerate(); },
            isGenerating,
          }}
        />
      );
    }

    if (currentStep === 4) {
      return (
        <section className="workspace-step">
          <div className="workspace-step__toolbar">
            <h2>{t('edit_title')}</h2>
            <div className="workspace-step__toolbar-actions">
              <button className="btn btn--small" onClick={() => { void handlePlay(); }}>
                {isPlaying ? t('transport.pause') : t('transport.play')}
              </button>
              <button className="btn btn--small" onClick={handleStop}>{t('transport.stop')}</button>
              <button className="btn btn--small btn--primary" onClick={() => { void handleGenerate(); }} disabled={isGenerating}>
                {isGenerating ? t('arrange_generating') : t('arrange_generate')}
              </button>
            </div>
          </div>

          <div className="daw-body">
            <div className="daw-sidebar">
              <TrackList
                tracks={arrangement?.tracks || []}
                trackStates={trackStates}
                selectedTrack={selectedTrack}
                onTrackSelect={setSelectedTrack}
                onMuteToggle={handleMuteToggle}
                onSoloToggle={handleSoloToggle}
                onVolumeChange={handleVolumeChange}
              />

              <div className="daw-sidebar__section">
                <div className="daw-sidebar__section-header" onClick={() => setShowInstrumentPanel((prev) => !prev)}>
                  <span>{t('sidebar.instruments')}</span>
                  <span className="daw-sidebar__toggle-icon">{showInstrumentPanel ? '\u25B2' : '\u25BC'}</span>
                </div>
                {showInstrumentPanel && (
                  <div className="daw-sidebar__instruments-body">
                    <InstrumentPicker label={t('sidebar.leadMelody')} selectedProgram={leadProgram} onChange={setLeadProgram} />
                    <InstrumentPicker label={t('sidebar.bass')} selectedProgram={bassProgram} onChange={setBassProgram} />
                    <InstrumentPicker label={t('sidebar.harmonyArp')} selectedProgram={harmonyProgram} onChange={setHarmonyProgram} />
                  </div>
                )}
              </div>

              <div className="daw-sidebar__footer">
                <span className="daw-sidebar__source">
                  {sourceFileName ? `${t('sidebar.melody')}: ${sourceFileName}` : t('sidebar.melodyInput')}
                </span>
                <div className="daw-sidebar__footer-btns">
                  <button className="btn btn--small btn--demo" onClick={handleLoadDemo}>{t('sidebar.demo')}</button>
                  <button className="btn btn--small" onClick={() => setCurrentStep(1)}>{t('sidebar.uploadFile')}</button>
                </div>
              </div>
            </div>

            <div className="daw-arrange-area">
              {!arrangement && notes.length > 0 && (
                <div className="daw-arrange-area__cta">
                  <button className="btn btn--primary btn--large" onClick={() => { void handleGenerate(); }} disabled={isGenerating}>
                    {isGenerating ? t('arrange_generating') : t('arrange_generate')}
                  </button>
                </div>
              )}
              <ArrangementView arrangement={arrangement} currentBeat={currentBeat} beatsPerBar={beatsPerBar} />
            </div>
          </div>

          <div className={`daw-midi-player ${showMidiPlayer ? 'daw-midi-player--open' : 'daw-midi-player--closed'}`}>
            <div className="daw-midi-player__header" onClick={() => setShowMidiPlayer((prev) => !prev)}>
              <span>MIDI Player</span>
              <span className="daw-midi-player__toggle">{showMidiPlayer ? '\u25BC' : '\u25B2'}</span>
            </div>
            {showMidiPlayer && <MidiPlayer />}
          </div>

          <div className={`daw-piano-roll ${showPianoRoll ? 'daw-piano-roll--open' : 'daw-piano-roll--closed'}`}>
            <div className="daw-piano-roll__header" onClick={() => setShowPianoRoll((prev) => !prev)}>
              <span>{t('pianoRoll.title')}{selectedTrack ? ` — ${selectedTrack}` : ''}</span>
              <span className="daw-piano-roll__toggle">{showPianoRoll ? '\u25BC' : '\u25B2'}</span>
            </div>
            {showPianoRoll && (
              <PianoRoll
                notes={notes}
                onNotesChange={setNotes}
                bars={bars}
                beatsPerBar={beatsPerBar}
                tempoBpm={tempo}
              />
            )}
          </div>
        </section>
      );
    }

    return (
      <ExportView
        isReady={Boolean(arrangement)}
        onExportMidi={handleDownloadMidi}
        onExportMp3={handleExportMp3}
        onExportLogic={handleExportLogic}
      />
    );
  };

  return (
    <div className="app-shell">
      <header className="app-shell__topbar">
        <a href="/" className="btn btn--small" style={{ textDecoration: 'none' }}>
          {t('nav_back_to_site')}
        </a>
        <div className="app-shell__topbar-right">
          {sourceFileName && <span className="app-shell__source">{sourceFileName}</span>}
          <LanguageSwitcher />
        </div>
      </header>

      {error && (
        <div className="error-banner" onClick={() => setError(null)}>
          <span className="error-banner__message">{error}</span>
          <button className="error-banner__dismiss">&times;</button>
        </div>
      )}

      <StepWizard
        currentStep={currentStep}
        onBack={handleWizardBack}
        onNext={handleWizardNext}
        canGoBack={canGoBack}
        canGoNext={canGoNext}
      >
        {renderCurrentStep()}
      </StepWizard>
    </div>
  );
}

export default App;
