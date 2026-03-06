import CreativityLevel from './CreativityLevel.tsx';
import type { CreativityLevelValue } from './CreativityLevel.tsx';
import TransportControls from './TransportControls.tsx';
import './ArrangeView.css';

interface ArrangeViewProps {
  creativityLevel: CreativityLevelValue;
  onCreativityChange: (level: CreativityLevelValue) => void;
  transport: {
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
  };
}

export default function ArrangeView({ creativityLevel, onCreativityChange, transport }: ArrangeViewProps) {
  return (
    <section className="arrange-view">
      <TransportControls {...transport} />
      <CreativityLevel level={creativityLevel} onChange={onCreativityChange} />
    </section>
  );
}
