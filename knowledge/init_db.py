#!/usr/bin/env python3
"""Initialize the music knowledge SQLite database."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "knowledge.db"


def init_db(db_path: str | Path = DB_PATH):
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS scales_modes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        aliases TEXT DEFAULT '',
        intervals TEXT NOT NULL,
        notes_from_c TEXT DEFAULT '',
        category TEXT DEFAULT 'diatonic',
        description TEXT DEFAULT '',
        source TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(name)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS chord_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        symbol TEXT NOT NULL,
        intervals TEXT NOT NULL,
        category TEXT DEFAULT 'triad',
        description TEXT DEFAULT '',
        source TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(name)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS chord_progressions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT DEFAULT '',
        style TEXT NOT NULL,
        roman_numerals TEXT NOT NULL,
        mode TEXT DEFAULT 'major',
        bars INTEGER DEFAULT 4,
        description TEXT DEFAULT '',
        example_songs TEXT DEFAULT '',
        energy_level TEXT DEFAULT 'medium',
        source TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS rhythm_patterns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT DEFAULT '',
        style TEXT NOT NULL,
        instrument TEXT NOT NULL,
        time_signature TEXT DEFAULT '4/4',
        bpm_range TEXT DEFAULT '80-140',
        pattern_data TEXT NOT NULL,
        description TEXT DEFAULT '',
        source TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS bass_patterns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT DEFAULT '',
        style TEXT NOT NULL,
        pattern_type TEXT NOT NULL,
        pattern_data TEXT NOT NULL,
        description TEXT DEFAULT '',
        source TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS instrumentation (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        gm_program INTEGER DEFAULT -1,
        family TEXT DEFAULT '',
        range_low TEXT DEFAULT '',
        range_high TEXT DEFAULT '',
        sweet_spot TEXT DEFAULT '',
        styles TEXT DEFAULT '',
        role TEXT DEFAULT '',
        description TEXT DEFAULT '',
        source TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(name)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS arrangement_techniques (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        style TEXT DEFAULT '',
        category TEXT DEFAULT '',
        description TEXT NOT NULL,
        example TEXT DEFAULT '',
        source TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS melody_techniques (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT DEFAULT '',
        description TEXT NOT NULL,
        example TEXT DEFAULT '',
        source TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS voice_leading_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        rule_text TEXT NOT NULL,
        category TEXT DEFAULT '',
        priority INTEGER DEFAULT 5,
        source TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # 歌曲整体分析 — 真实工程文件/编曲拆解
    c.execute("""CREATE TABLE IF NOT EXISTS song_analyses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        artist TEXT DEFAULT '',
        style TEXT DEFAULT '',
        key TEXT DEFAULT '',
        bpm INTEGER DEFAULT 0,
        time_signature TEXT DEFAULT '4/4',
        structure TEXT DEFAULT '',
        chord_progression TEXT DEFAULT '',
        tracks TEXT DEFAULT '',
        arrangement_notes TEXT DEFAULT '',
        mood TEXT DEFAULT '',
        energy_curve TEXT DEFAULT '',
        midi_source TEXT DEFAULT '',
        source TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # 主旋律与伴奏关系 — 编曲的核心维度
    c.execute("""CREATE TABLE IF NOT EXISTS melody_accompaniment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        style TEXT DEFAULT '',
        section_type TEXT DEFAULT '',
        melody_instrument TEXT DEFAULT '',
        accomp_instrument TEXT DEFAULT '',
        relationship TEXT NOT NULL,
        rhythm_relation TEXT DEFAULT '',
        register_relation TEXT DEFAULT '',
        dynamic_relation TEXT DEFAULT '',
        mood TEXT DEFAULT '',
        tension_level TEXT DEFAULT 'medium',
        description TEXT DEFAULT '',
        example_song TEXT DEFAULT '',
        source TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # 情绪-音乐要素映射
    c.execute("""CREATE TABLE IF NOT EXISTS mood_mappings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mood TEXT NOT NULL,
        mood_cn TEXT DEFAULT '',
        tempo_range TEXT DEFAULT '',
        key_preference TEXT DEFAULT '',
        mode_preference TEXT DEFAULT '',
        chord_types TEXT DEFAULT '',
        rhythm_density TEXT DEFAULT '',
        dynamics TEXT DEFAULT '',
        register TEXT DEFAULT '',
        instruments TEXT DEFAULT '',
        texture TEXT DEFAULT '',
        articulation TEXT DEFAULT '',
        harmonic_rhythm TEXT DEFAULT '',
        example_progressions TEXT DEFAULT '',
        description TEXT DEFAULT '',
        source TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(mood)
    )""")

    # 段落编排模式 — intro/verse/chorus/bridge 各段怎么编
    c.execute("""CREATE TABLE IF NOT EXISTS section_patterns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        section_type TEXT NOT NULL,
        style TEXT DEFAULT '',
        active_instruments TEXT DEFAULT '',
        texture_density TEXT DEFAULT '',
        energy_level TEXT DEFAULT '',
        melody_treatment TEXT DEFAULT '',
        harmony_treatment TEXT DEFAULT '',
        rhythm_treatment TEXT DEFAULT '',
        bass_treatment TEXT DEFAULT '',
        transition_in TEXT DEFAULT '',
        transition_out TEXT DEFAULT '',
        mood_function TEXT DEFAULT '',
        description TEXT DEFAULT '',
        source TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # 张力曲线模板 — 整首歌的情绪走向
    c.execute("""CREATE TABLE IF NOT EXISTS tension_curves (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        style TEXT DEFAULT '',
        structure TEXT NOT NULL,
        curve_data TEXT NOT NULL,
        description TEXT DEFAULT '',
        example_song TEXT DEFAULT '',
        source TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS search_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query TEXT NOT NULL,
        result_count INTEGER DEFAULT 0,
        source_urls TEXT DEFAULT '',
        worker TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    conn.commit()
    conn.close()
    print(f"Database initialized at {db_path}")


if __name__ == "__main__":
    init_db()
