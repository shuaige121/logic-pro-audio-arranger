import { useState, useCallback, useRef, useEffect } from 'react';
import type { NoteEvent, Arrangement, KeyEstimate, HarmonyCandidate } from './types/music.ts';
import {
  arrangementToMidi,
  downloadMidi,
  PlaybackEngine,
  parseFile,
  generateArrangementWithAI,
  estimateKey,
  detectPhrasesInfo,
  nameToPitchClass,
} from './engine/index.ts';
import { useI18n } from './i18n.ts';
import type { CreativityLevelValue, AnalysisFormState } from './components/Inspector.tsx';
import type { TrackState } from './components/TrackList.tsx';
import ProjectChooser from './components/ProjectChooser.tsx';
import ControlBar from './components/ControlBar.tsx';
import Inspector from './components/Inspector.tsx';
import TrackList from './components/TrackList.tsx';
import ArrangementView from './components/ArrangementView.tsx';
import MidiPlayer from './components/MidiPlayer.tsx';
import PianoRoll from './components/PianoRoll.tsx';
import './App.css';

type Screen = 'chooser' | 'workspace';

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

  /* ── Screen state ── */
  const [screen, setScreen] = useState<Screen>('chooser');
  const [sourceFileName, setSourceFileName] = useState<string | null>(null);

  /* ── Upload ── */
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [sourceType, setSourceType] = useState<string>('vocal');

  /* ── Music data ── */
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

  /* ── Instruments ── */
  const [leadProgram, setLeadProgram] = useState(80);
  const [bassProgram, setBassProgram] = useState(33);
  const [harmonyProgram, setHarmonyProgram] = useState(0);

  /* ── Analysis ── */
  const [keyEstimate, setKeyEstimate] = useState<KeyEstimate | null>(null);
  const [harmony, setHarmony] = useState<HarmonyCandidate | null>(null);
  const [error, setError] = useState<string | null>(null);

  /* ── Track state ── */
  const [selectedTrack, setSelectedTrack] = useState<string | null>(null);
  const [trackStates, setTrackStates] = useState<Record<string, TrackState>>({});
  const [showPianoRoll, setShowPianoRoll] = useState(true);
  const [showMidiPlayer, setShowMidiPlayer] = useState(false);

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

  /* ── Playback refs ── */
  const playbackRef = useRef<PlaybackEngine | null>(null);
  const animFrameRef = useRef<number>(0);
  const loadedArrangementRef = useRef<Arrangement | null>(null);

  const getPlaybackEngine = useCallback((): PlaybackEngine => {
    if (!playbackRef.current) playbackRef.current = new PlaybackEngine();
    return playbackRef.current;
  }, []);

  /* ── Effects ── */
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
      if (screen !== 'workspace') return;
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
  }, [screen]);

  /* ── Handlers ── */
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
    setScreen('workspace');
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
    setScreen('workspace');
  }, [t]);

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
      const result = await generateArrangementWithAI(notes, tempo, bars, style, complexity, beatsPerBar, creativityLevel);
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
    } catch (err) {
      setError(err instanceof Error ? err.message : t('error'));
    } finally {
      setIsGenerating(false);
    }
  }, [notes, tempo, bars, style, complexity, beatsPerBar, creativityLevel, leadProgram, bassProgram, harmonyProgram, t]);

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
  }, [arrangement, keyEstimate, harmony]);

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

  const handleAnalysisChange = useCallback((next: AnalysisFormState) => {
    setAnalysisState(next);
    // Sync key estimate if key/mode changed
    try {
      const tonicPc = nameToPitchClass(next.key);
      setKeyEstimate((prev) => ({
        tonicPc,
        tonicName: next.key,
        mode: next.mode,
        score: prev?.score ?? 1,
      }));
    } catch {
      // ignore invalid key names
    }
    if (next.bpm !== tempo) setTempo(next.bpm);
    if (next.bars !== bars) setBars(next.bars);
  }, [tempo, bars]);

  /* ── Render ── */
  if (screen === 'chooser') {
    return (
      <div className="app-shell">
        {error && (
          <div className="error-banner" onClick={() => setError(null)}>
            <span className="error-banner__message">{error}</span>
            <button className="error-banner__dismiss">&times;</button>
          </div>
        )}
        <ProjectChooser
          onFileSelected={handleFileSelected}
          isProcessing={isUploading}
          uploadError={uploadError}
          sourceType={sourceType}
          onSourceTypeChange={setSourceType}
          onLoadDemo={handleLoadDemo}
          onDrawManually={handleStartManual}
          tempo={analysisState.bpm}
          onTempoChange={(v) => setAnalysisState((p) => ({ ...p, bpm: v }))}
          keyName={analysisState.key}
          onKeyChange={(v) => setAnalysisState((p) => ({ ...p, key: v }))}
          timeSignature={analysisState.timeSignature}
          onTimeSignatureChange={(v) => setAnalysisState((p) => ({ ...p, timeSignature: v as '3/4' | '4/4' | '6/8' }))}
        />
      </div>
    );
  }

  // Screen: workspace
  return (
    <div className="app-shell">
      {error && (
        <div className="error-banner" onClick={() => setError(null)}>
          <span className="error-banner__message">{error}</span>
          <button className="error-banner__dismiss">&times;</button>
        </div>
      )}

      <div className="daw-workspace">
        {/* Control Bar */}
        <div className="daw-workspace__control">
          <ControlBar
            isPlaying={isPlaying}
            currentBeat={currentBeat}
            beatsPerBar={beatsPerBar}
            tempo={tempo}
            bars={bars}
            style={style}
            complexity={complexity}
            keyName={keyEstimate?.tonicName ?? null}
            modeName={keyEstimate?.mode ?? null}
            isGenerating={isGenerating}
            onPlay={() => { void handlePlay(); }}
            onStop={handleStop}
            onTempoChange={handleTempoChange}
            onBarsChange={handleBarsChange}
            onStyleChange={setStyle}
            onComplexityChange={setComplexity}
            onGenerate={() => { void handleGenerate(); }}
            onBack={() => setScreen('chooser')}
          />
        </div>

        {/* Track Headers */}
        <div className="daw-workspace__tracks">
          <TrackList
            tracks={arrangement?.tracks || []}
            trackStates={trackStates}
            selectedTrack={selectedTrack}
            onTrackSelect={setSelectedTrack}
            onMuteToggle={handleMuteToggle}
            onSoloToggle={handleSoloToggle}
            onVolumeChange={handleVolumeChange}
          />
          <div className="daw-sidebar-footer">
            <span className="daw-sidebar-footer__source">
              {sourceFileName ? `${t('sidebar.melody')}: ${sourceFileName}` : t('sidebar.melodyInput')}
            </span>
            <div className="daw-sidebar-footer__btns">
              <button className="btn btn--small btn--demo" onClick={handleLoadDemo}>{t('sidebar.demo')}</button>
              <button className="btn btn--small" onClick={() => setScreen('chooser')}>{t('sidebar.uploadFile')}</button>
            </div>
          </div>
        </div>

        {/* Arrangement Timeline */}
        <div className="daw-workspace__timeline">
          {!arrangement && notes.length > 0 && (
            <div className="daw-workspace__timeline-cta">
              <button className="btn btn--primary" onClick={() => { void handleGenerate(); }} disabled={isGenerating}>
                {isGenerating ? t('arrange_generating') : t('arrange_generate')}
              </button>
            </div>
          )}
          <ArrangementView arrangement={arrangement} currentBeat={currentBeat} beatsPerBar={beatsPerBar} />
        </div>

        {/* Inspector */}
        <div className="daw-workspace__inspector">
          <Inspector
            analysisState={analysisState}
            onAnalysisChange={handleAnalysisChange}
            creativityLevel={creativityLevel}
            onCreativityChange={setCreativityLevel}
            leadProgram={leadProgram}
            onLeadChange={setLeadProgram}
            bassProgram={bassProgram}
            onBassChange={setBassProgram}
            harmonyProgram={harmonyProgram}
            onHarmonyChange={setHarmonyProgram}
            hasArrangement={Boolean(arrangement)}
            onExportMidi={handleDownloadMidi}
            onExportMp3={handleExportMp3}
            onExportLogic={handleExportLogic}
          />
        </div>

        {/* Editor panels */}
        <div className="daw-workspace__editor">
          <div className={`daw-editor-panel ${showPianoRoll ? 'daw-editor-panel--open' : 'daw-editor-panel--closed'}`}>
            <div className="daw-editor-panel__header" onClick={() => setShowPianoRoll((p) => !p)}>
              <span>{t('pianoRoll.title')}{selectedTrack ? ` — ${selectedTrack}` : ''}</span>
              <span className="daw-editor-panel__toggle">{showPianoRoll ? '\u25BC' : '\u25B2'}</span>
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

          <div className={`daw-editor-panel ${showMidiPlayer ? 'daw-editor-panel--open' : 'daw-editor-panel--closed'}`}>
            <div className="daw-editor-panel__header" onClick={() => setShowMidiPlayer((p) => !p)}>
              <span>MIDI Player</span>
              <span className="daw-editor-panel__toggle">{showMidiPlayer ? '\u25BC' : '\u25B2'}</span>
            </div>
            {showMidiPlayer && <MidiPlayer />}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
