import { createContext, useContext, useState, useCallback } from 'react';

export type Locale = 'zh' | 'en' | 'ja' | 'ms' | 'ta';

export const LOCALE_LABELS: Record<Locale, string> = {
  zh: '中文',
  en: 'EN',
  ja: '日本語',
  ms: 'BM',
  ta: 'தமிழ்',
};

const translations: Record<Locale, Record<string, string>> = {
  en: {
    step_upload: 'Upload',
    step_analyze: 'Analyze',
    step_arrange: 'Arrange',
    step_edit: 'Edit',
    step_export: 'Export',

    upload_title: 'Upload Your Music',
    upload_subtitle: 'Drag and drop your audio or MIDI file',
    upload_formats: 'Supports: MIDI, MP3, WAV, MusicXML, CSV',
    upload_or: 'or',
    upload_browse: 'Browse Files',
    upload_demo: 'Load Demo',
    upload_draw: 'Draw Manually',

    analyze_title: 'Analysis Results',
    analyze_key: 'Detected Key',
    analyze_bpm: 'BPM',
    analyze_time_sig: 'Time Signature',
    analyze_bars: 'Bars',
    analyze_notes: 'Notes',
    analyze_phrases: 'Phrases',
    analyze_correct: 'Correct manually if needed',

    arrange_title: 'Generate Arrangement',
    arrange_style: 'Style',
    arrange_creativity: 'Creativity Level',
    arrange_conservative: 'Conservative',
    arrange_balanced: 'Balanced',
    arrange_creative: 'Creative',
    arrange_generate: 'Generate',
    arrange_generating: 'Generating arrangement...',

    edit_title: 'Edit Arrangement',
    edit_mute: 'Mute',
    edit_solo: 'Solo',
    edit_volume: 'Volume',

    export_title: 'Export',
    export_midi: 'Export MIDI',
    export_mp3: 'Export MP3',
    export_logic: 'Export Logic Pro Kit',
    export_midi_desc: 'Standard DAW workflow and editable notes.',
    export_mp3_desc: 'Quick listening draft for sharing.',
    export_logic_desc: 'Session package optimized for Logic Pro.',
    export_ready: 'Arrangement ready',
    export_not_ready: 'Generate arrangement first',

    proc_humanizer: 'Humanizer',
    proc_timing: 'Timing Variation',
    proc_velocity: 'Velocity Variation',
    proc_swing: 'Swing',

    nav_back: 'Back',
    nav_next: 'Next',
    nav_back_to_site: '← zhouruby.com',

    loading: 'Loading...',
    error: 'Error',
    success: 'Success',

    // Legacy / shared keys used by existing components
    'upload.analyzing': 'Analyzing your file...',
    'upload.dragDrop': 'Drag & drop your music file here',
    'upload.dropHere': 'Drop your file here',
    'upload.clickBrowse': 'or click to browse',
    'upload.formats': 'Supported: MIDI (.mid) / Audio (.wav, .mp3, .flac, .ogg, .aac) / MusicXML (.xml, .musicxml) / CSV',
    'upload.noNotes': 'No notes detected in this file. Try a different file or draw manually.',

    'transport.rewind': 'Rewind',
    'transport.play': 'Play',
    'transport.pause': 'Pause',
    'transport.stop': 'Stop',
    'transport.bars': 'Bars',
    'transport.style': 'Style',
    'transport.complexity': 'Complexity',
    'transport.stylePop': 'Pop',
    'transport.styleModal': 'Modal',
    'transport.styleJazz': 'Jazz',
    'transport.complexityBasic': 'Basic',
    'transport.complexityRich': 'Rich',

    'trackList.title': 'Tracks',
    'trackList.empty': 'Generate arrangement to see tracks',

    'arrangement.emptyTitle': 'Click Generate to create arrangement',
    'arrangement.emptyDesc': 'Upload or draw a melody, then generate tracks for bass, harmony, and drums.',

    'sidebar.instruments': 'Instruments (128 GM)',
    'sidebar.leadMelody': 'Lead Melody',
    'sidebar.bass': 'Bass',
    'sidebar.harmonyArp': 'Harmony / Arp',
    'sidebar.melodyInput': 'Melody Input',
    'sidebar.melody': 'Melody',
    'sidebar.demo': 'Demo',
    'sidebar.uploadFile': 'Upload File',

    'pianoRoll.title': 'Piano Roll',

    'error.noNotes': 'No notes to arrange. Draw some notes in the piano roll first.',
    'error.generateFirst': 'Generate an arrangement first.',
    'error.playbackFailed': 'Playback failed',
    'error.stopFailed': 'Stop failed',
    'error.midiExport': 'MIDI export failed',
    'error.jsonExport': 'JSON export failed',

    'demo.name': 'Demo: C Major Scale',
  },
  zh: {
    step_upload: '上传',
    step_analyze: '分析',
    step_arrange: '编曲',
    step_edit: '编辑',
    step_export: '导出',

    upload_title: '上传你的音乐',
    upload_subtitle: '拖放音频或 MIDI 文件',
    upload_formats: '支持: MIDI, MP3, WAV, MusicXML, CSV',
    upload_or: '或',
    upload_browse: '选择文件',
    upload_demo: '加载演示',
    upload_draw: '手动绘制',

    analyze_title: '分析结果',
    analyze_key: '检测到的调',
    analyze_bpm: '速度',
    analyze_time_sig: '拍号',
    analyze_bars: '小节',
    analyze_notes: '音符',
    analyze_phrases: '乐句',
    analyze_correct: '如有需要可手动修正',

    arrange_title: '生成编曲',
    arrange_style: '风格',
    arrange_creativity: '创意档位',
    arrange_conservative: '保守',
    arrange_balanced: '平衡',
    arrange_creative: '创意',
    arrange_generate: '生成',
    arrange_generating: '正在生成编曲...',

    edit_title: '编辑编曲',
    edit_mute: '静音',
    edit_solo: '独奏',
    edit_volume: '音量',

    export_title: '导出',
    export_midi: '导出 MIDI',
    export_mp3: '导出 MP3',
    export_logic: '导出 Logic Pro 套件',
    export_midi_desc: '标准 DAW 工作流，可编辑音符。',
    export_mp3_desc: '快速试听草稿，方便分享。',
    export_logic_desc: '为 Logic Pro 优化的会话包。',
    export_ready: '编曲已就绪',
    export_not_ready: '请先生成编曲',

    proc_humanizer: '人性化',
    proc_timing: '时值变化',
    proc_velocity: '力度变化',
    proc_swing: '摇摆感',

    nav_back: '返回',
    nav_next: '下一步',
    nav_back_to_site: '← zhouruby.com',

    loading: '加载中...',
    error: '错误',
    success: '成功',

    'upload.analyzing': '正在分析你的文件...',
    'upload.dragDrop': '将音乐文件拖放到此处',
    'upload.dropHere': '松开鼠标放置文件',
    'upload.clickBrowse': '或点击选择文件',
    'upload.formats': '支持格式：MIDI (.mid) / 音频 (.wav, .mp3, .flac, .ogg, .aac) / MusicXML (.xml, .musicxml) / CSV',
    'upload.noNotes': '未在文件中检测到音符，请尝试其他文件或手动绘制。',

    'transport.rewind': '回到开头',
    'transport.play': '播放',
    'transport.pause': '暂停',
    'transport.stop': '停止',
    'transport.bars': '小节',
    'transport.style': '风格',
    'transport.complexity': '丰富度',
    'transport.stylePop': '流行',
    'transport.styleModal': '调式',
    'transport.styleJazz': '爵士',
    'transport.complexityBasic': '基础',
    'transport.complexityRich': '丰富',

    'trackList.title': '轨道',
    'trackList.empty': '生成编曲后显示轨道',

    'arrangement.emptyTitle': '点击生成开始编曲',
    'arrangement.emptyDesc': '上传或绘制旋律后，系统会生成贝斯、和声和鼓组轨道。',

    'sidebar.instruments': '乐器选择 (128 GM)',
    'sidebar.leadMelody': '主旋律',
    'sidebar.bass': '贝斯',
    'sidebar.harmonyArp': '和声 / 琶音',
    'sidebar.melodyInput': '旋律输入',
    'sidebar.melody': '旋律',
    'sidebar.demo': '示例',
    'sidebar.uploadFile': '上传文件',

    'pianoRoll.title': '钢琴卷帘',

    'error.noNotes': '没有音符可以编曲。请先在钢琴卷帘中绘制音符。',
    'error.generateFirst': '请先生成编曲。',
    'error.playbackFailed': '播放失败',
    'error.stopFailed': '停止失败',
    'error.midiExport': 'MIDI 导出失败',
    'error.jsonExport': 'JSON 导出失败',

    'demo.name': '示例: C 大调音阶',
  },
  ja: {
    step_upload: 'アップロード',
    step_analyze: '分析',
    step_arrange: 'アレンジ',
    step_edit: '編集',
    step_export: 'エクスポート',
    upload_title: '音楽をアップロード',
    upload_subtitle: 'オーディオまたはMIDIファイルをドラッグ＆ドロップ',
    upload_formats: '対応: MIDI, MP3, WAV, MusicXML, CSV',
    upload_or: 'または',
    upload_browse: 'ファイルを選択',
    upload_demo: 'デモを読み込む',
    upload_draw: '手動で描画',
    analyze_title: '分析結果',
    analyze_key: '検出されたキー',
    analyze_bpm: 'BPM',
    analyze_time_sig: '拍子',
    analyze_bars: '小節',
    analyze_notes: '音符',
    analyze_phrases: 'フレーズ',
    analyze_correct: '必要に応じて手動で修正',
    arrange_title: 'アレンジを生成',
    arrange_style: 'スタイル',
    arrange_creativity: 'クリエイティブレベル',
    arrange_conservative: '控えめ',
    arrange_balanced: 'バランス',
    arrange_creative: 'クリエイティブ',
    arrange_generate: '生成',
    arrange_generating: 'アレンジ生成中...',
    edit_title: 'アレンジを編集',
    edit_mute: 'ミュート',
    edit_solo: 'ソロ',
    edit_volume: '音量',
    export_title: 'エクスポート',
    export_midi: 'MIDIエクスポート',
    export_mp3: 'MP3エクスポート',
    export_logic: 'Logic Proキットエクスポート',
    export_midi_desc: '標準DAWワークフロー、ノート編集可能。',
    export_mp3_desc: '共有用のクイックリスニングドラフト。',
    export_logic_desc: 'Logic Pro用に最適化されたセッションパッケージ。',
    export_ready: 'アレンジ準備完了',
    export_not_ready: 'まずアレンジを生成してください',
    proc_humanizer: 'ヒューマナイザー',
    proc_timing: 'タイミング変化',
    proc_velocity: 'ベロシティ変化',
    proc_swing: 'スウィング',
    nav_back: '戻る',
    nav_next: '次へ',
    nav_back_to_site: '← zhouruby.com',
    loading: '読み込み中...',
    error: 'エラー',
    success: '成功',
  },
  ms: {
    step_upload: 'Muat Naik',
    step_analyze: 'Analisis',
    step_arrange: 'Aransemen',
    step_edit: 'Sunting',
    step_export: 'Eksport',
    upload_title: 'Muat Naik Muzik Anda',
    upload_subtitle: 'Seret dan lepaskan fail audio atau MIDI',
    upload_formats: 'Sokongan: MIDI, MP3, WAV, MusicXML, CSV',
    upload_or: 'atau',
    upload_browse: 'Pilih Fail',
    upload_demo: 'Muat Demo',
    upload_draw: 'Lukis Manual',
    analyze_title: 'Keputusan Analisis',
    analyze_key: 'Kunci Dikesan',
    analyze_bpm: 'BPM',
    analyze_time_sig: 'Tanda Masa',
    analyze_bars: 'Bar',
    analyze_notes: 'Nota',
    analyze_phrases: 'Frasa',
    analyze_correct: 'Betulkan secara manual jika perlu',
    arrange_title: 'Jana Aransemen',
    arrange_style: 'Gaya',
    arrange_creativity: 'Tahap Kreativiti',
    arrange_conservative: 'Konservatif',
    arrange_balanced: 'Seimbang',
    arrange_creative: 'Kreatif',
    arrange_generate: 'Jana',
    arrange_generating: 'Menjana aransemen...',
    edit_title: 'Sunting Aransemen',
    edit_mute: 'Senyap',
    edit_solo: 'Solo',
    edit_volume: 'Kelantangan',
    export_title: 'Eksport',
    export_midi: 'Eksport MIDI',
    export_mp3: 'Eksport MP3',
    export_logic: 'Eksport Kit Logic Pro',
    export_midi_desc: 'Aliran kerja DAW standard dan nota boleh disunting.',
    export_mp3_desc: 'Draf pendengaran pantas untuk perkongsian.',
    export_logic_desc: 'Pakej sesi dioptimumkan untuk Logic Pro.',
    export_ready: 'Aransemen sedia',
    export_not_ready: 'Jana aransemen dahulu',
    proc_humanizer: 'Humanizer',
    proc_timing: 'Variasi Masa',
    proc_velocity: 'Variasi Kelajuan',
    proc_swing: 'Swing',
    nav_back: 'Kembali',
    nav_next: 'Seterusnya',
    nav_back_to_site: '← zhouruby.com',
    loading: 'Memuatkan...',
    error: 'Ralat',
    success: 'Berjaya',
  },
  ta: {
    step_upload: 'பதிவேற்றம்',
    step_analyze: 'பகுப்பாய்வு',
    step_arrange: 'ஏற்பாடு',
    step_edit: 'திருத்தம்',
    step_export: 'ஏற்றுமதி',
    upload_title: 'உங்கள் இசையை பதிவேற்றவும்',
    upload_subtitle: 'ஆடியோ அல்லது MIDI கோப்பை இழுத்து விடவும்',
    upload_formats: 'ஆதரவு: MIDI, MP3, WAV, MusicXML, CSV',
    upload_or: 'அல்லது',
    upload_browse: 'கோப்புகளை தேர்வு',
    upload_demo: 'டெமோ ஏற்று',
    upload_draw: 'கைமுறை வரைய',
    analyze_title: 'பகுப்பாய்வு முடிவுகள்',
    analyze_key: 'கண்டறியப்பட்ட சாவி',
    analyze_bpm: 'BPM',
    analyze_time_sig: 'தாள அடையாளம்',
    analyze_bars: 'பட்டைகள்',
    analyze_notes: 'குறிப்புகள்',
    analyze_phrases: 'சொற்றொடர்கள்',
    analyze_correct: 'தேவைப்பட்டால் கைமுறையாக திருத்தவும்',
    arrange_title: 'ஏற்பாட்டை உருவாக்கு',
    arrange_style: 'பாணி',
    arrange_creativity: 'படைப்பாற்றல் நிலை',
    arrange_conservative: 'பாரம்பரிய',
    arrange_balanced: 'சமநிலை',
    arrange_creative: 'படைப்பாற்றல்',
    arrange_generate: 'உருவாக்கு',
    arrange_generating: 'ஏற்பாடு உருவாக்கப்படுகிறது...',
    edit_title: 'ஏற்பாட்டை திருத்து',
    edit_mute: 'அமைதி',
    edit_solo: 'தனி',
    edit_volume: 'ஒலியளவு',
    export_title: 'ஏற்றுமதி',
    export_midi: 'MIDI ஏற்றுமதி',
    export_mp3: 'MP3 ஏற்றுமதி',
    export_logic: 'Logic Pro கிட் ஏற்றுமதி',
    export_midi_desc: 'நிலையான DAW பணிப்பாய்வு மற்றும் திருத்தக்கூடிய குறிப்புகள்.',
    export_mp3_desc: 'பகிர்வுக்கான விரைவான கேட்பு வரைவு.',
    export_logic_desc: 'Logic Pro க்கு உகந்த அமர்வு தொகுப்பு.',
    export_ready: 'ஏற்பாடு தயார்',
    export_not_ready: 'முதலில் ஏற்பாட்டை உருவாக்கவும்',
    proc_humanizer: 'மனிதமயமாக்கி',
    proc_timing: 'நேர மாறுபாடு',
    proc_velocity: 'வேக மாறுபாடு',
    proc_swing: 'ஊசல்',
    nav_back: 'பின்செல்',
    nav_next: 'அடுத்து',
    nav_back_to_site: '← zhouruby.com',
    loading: 'ஏற்றுகிறது...',
    error: 'பிழை',
    success: 'வெற்றி',
  },
};

function detectLocale(): Locale {
  const lang = (navigator.language || '').toLowerCase();
  if (lang.startsWith('zh')) return 'zh';
  if (lang.startsWith('ja')) return 'ja';
  if (lang.startsWith('ms')) return 'ms';
  if (lang.startsWith('ta')) return 'ta';
  return 'en';
}

interface I18nContextValue {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: string, vars?: Record<string, string | number>) => string;
}

export const I18nContext = createContext<I18nContextValue>({
  locale: 'en',
  setLocale: () => {},
  t: (key) => key,
});

export function useI18n() {
  return useContext(I18nContext);
}

export function useI18nProvider() {
  const [locale, setLocale] = useState<Locale>(detectLocale);

  const t = useCallback((key: string, vars?: Record<string, string | number>): string => {
    let text = translations[locale][key] ?? translations.en[key] ?? key;
    if (vars) {
      for (const [k, v] of Object.entries(vars)) {
        text = text.replace(`{${k}}`, String(v));
      }
    }
    return text;
  }, [locale]);

  return { locale, setLocale, t };
}
