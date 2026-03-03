#!/usr/bin/env python3
"""Generate classic song analysis records and write into song_analyses table."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

try:
    from knowledge.init_db import init_db
except ModuleNotFoundError:
    from init_db import init_db  # type: ignore

DB_PATH = Path(__file__).parent / "knowledge.db"
SEARCH_JSON_PATH = Path(__file__).parent / "extracted" / "song_analysis_enriched.json"
SOURCE_PREFIX = "gen_song_analyses"


def to_json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def normalize(text: str) -> str:
    return " ".join(text.strip().lower().split())


def load_search_results(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if not isinstance(raw, list):
        return []
    out: list[dict[str, str]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        out.append(
            {
                "title": str(item.get("title", "")),
                "query": str(item.get("query", "")),
                "description": str(item.get("description", "")),
                "url": str(item.get("url", "")),
            }
        )
    return out


def result_blob(item: dict[str, str]) -> str:
    return normalize(
        f"{item.get('title', '')} {item.get('query', '')} {item.get('description', '')}"
    )


def match_search_urls(
    title: str, artist: str, search_results: list[dict[str, str]], fallback_urls: list[str]
) -> list[str]:
    title_n = normalize(title)
    artist_n = normalize(artist)
    ranked: list[tuple[int, str]] = []

    for item in search_results:
        url = item.get("url", "").strip()
        if not url:
            continue
        blob = result_blob(item)
        score = 0
        if title_n and title_n in blob:
            score += 8
        if artist_n and artist_n in blob:
            score += 6
        if title_n:
            for token in title_n.replace(",", " ").split():
                if len(token) >= 4 and token in blob:
                    score += 1
        if artist_n:
            for token in artist_n.replace(",", " ").split():
                if len(token) >= 4 and token in blob:
                    score += 1
        if score > 0:
            ranked.append((score, url))

    ranked.sort(key=lambda x: x[0], reverse=True)
    urls: list[str] = []
    for _, url in ranked:
        if url not in urls:
            urls.append(url)
        if len(urls) >= 2:
            break

    if not urls:
        urls = fallback_urls[:2] if fallback_urls else []
    return urls


def build_source(title: str, artist: str, urls: list[str]) -> str:
    if urls:
        return f"{SOURCE_PREFIX}|search:{'|'.join(urls)}|curated:classic_manual_dataset"
    return f"{SOURCE_PREFIX}|curated:classic_manual_dataset"


def record(
    *,
    title: str,
    artist: str,
    style: str,
    key: str,
    bpm: int,
    time_signature: str,
    structure: str,
    chord_progression: str,
    tracks: list[str],
    arrangement_notes: str,
    mood: str,
    energy_curve: dict[str, int],
    midi_source: str = "",
) -> dict[str, Any]:
    return {
        "title": title,
        "artist": artist,
        "style": style,
        "key": key,
        "bpm": bpm,
        "time_signature": time_signature,
        "structure": structure,
        "chord_progression": chord_progression,
        "tracks": tracks,
        "arrangement_notes": arrangement_notes,
        "mood": mood,
        "energy_curve": energy_curve,
        "midi_source": midi_source,
    }


def build_dataset() -> list[dict[str, Any]]:
    return [
        record(
            title="Someone Like You",
            artist="Adele",
            style="pop / piano ballad",
            key="A major",
            bpm=67,
            time_signature="4/4",
            structure="intro-verse-pre-chorus-chorus-verse-pre-chorus-chorus-bridge-chorus-outro",
            chord_progression="verse: I-V-vi-IV | chorus: I-V-vi-IV",
            tracks=["lead vocal", "piano", "backing vocal", "room reverb FX"],
            arrangement_notes="主旋律由人声主导，钢琴以分解和弦与低音根音同步支撑；伴奏几乎不抢频段，让歌词和呼吸感成为前景。主歌维持稀疏钢琴织体，副歌通过更高音区钢琴击弦和和声叠加抬升情绪；标志性手法是整曲克制动态与尾段人声爆发对比，把失落感从内省推向宣泄。",
            mood="伤感, 真挚, 克制",
            energy_curve={"intro": 2, "verse": 3, "pre_chorus": 4, "chorus": 6, "bridge": 7, "outro": 3},
            midi_source="",
        ),
        record(
            title="Shape of You",
            artist="Ed Sheeran",
            style="modern pop",
            key="C# minor",
            bpm=96,
            time_signature="4/4",
            structure="intro-verse-pre-chorus-chorus-verse-pre-chorus-chorus-bridge-chorus-outro",
            chord_progression="verse: i-III-VI-VII | chorus: i-III-VI-VII",
            tracks=["lead vocal", "plucked synth hook", "sub bass", "kick", "snare", "percussion loop", "fx riser"],
            arrangement_notes="主旋律是人声，标志性木琴感 pluck synth 作为副旋律反复勾连；低频由sub bass与kick做侧链配合，保证律动黏性。主歌打击乐较干、留白多，副歌增加和声与高频打击层；核心编曲手法是单一hook循环+逐层叠加，借音色密度变化而非和声复杂度来传递暧昧到兴奋的情绪推进。",
            mood="轻快, 性感, 律动",
            energy_curve={"intro": 3, "verse": 5, "pre_chorus": 6, "chorus": 8, "bridge": 7, "outro": 6},
            midi_source="",
        ),
        record(
            title="Blinding Lights",
            artist="The Weeknd",
            style="synth pop",
            key="F minor",
            bpm=171,
            time_signature="4/4",
            structure="intro-verse-pre-chorus-chorus-verse-pre-chorus-chorus-breakdown-chorus-outro",
            chord_progression="verse: i-VI-III-VII | chorus: i-VI-III-VII",
            tracks=["lead vocal", "analog synth lead", "synth bass", "drum machine", "gated snare", "arpeggiator", "pads"],
            arrangement_notes="主旋律由人声承担，合成器lead与其形成问答；鼓机与合成贝斯稳定八分音符脉冲，制造80s奔跑感。主歌用较薄pad和干鼓维持空间，副歌加入更亮主音色与更宽立体声；标志性做法是连续推动的脉冲节奏与复古音色统一，情绪从夜行孤独逐步推到失控亢奋。",
            mood="怀旧, 驱动, 夜色",
            energy_curve={"intro": 4, "verse": 6, "pre_chorus": 7, "chorus": 9, "breakdown": 6, "outro": 7},
            midi_source="",
        ),
        record(
            title="All of Me",
            artist="John Legend",
            style="R&B ballad",
            key="A♭ major",
            bpm=63,
            time_signature="4/4",
            structure="intro-verse-pre-chorus-chorus-verse-pre-chorus-chorus-bridge-chorus-outro",
            chord_progression="verse: I-V/vi-vi-IV | pre-chorus: ii-V-I | chorus: I-V-vi-IV",
            tracks=["lead vocal", "piano", "bass", "strings pad", "backing vocal"],
            arrangement_notes="主旋律由人声控制细腻动态，钢琴左手根音+右手和弦分解构成主要伴奏框架；低音在句尾补强终止感。主歌以钢琴独奏为主，副歌加厚和声与弦乐铺底；标志性编曲是保留大量呼吸与停顿，让旋律句尾自然下沉，情绪从告白式平静走向坚定承诺。",
            mood="温柔, 深情, 婚礼感",
            energy_curve={"intro": 2, "verse": 3, "pre_chorus": 4, "chorus": 6, "bridge": 7, "outro": 4},
            midi_source="",
        ),
        record(
            title="Rolling in the Deep",
            artist="Adele",
            style="pop rock",
            key="C minor",
            bpm=105,
            time_signature="4/4",
            structure="intro-verse-pre-chorus-chorus-verse-pre-chorus-chorus-bridge-chorus-outro",
            chord_progression="verse: i-VII-VI-VII | chorus: i-VII-VI-VII",
            tracks=["lead vocal", "drums", "stomp/clap", "bass", "guitar", "backing vocal", "piano"],
            arrangement_notes="主旋律由强攻击性人声驱动，伴奏以鼓组、拍手和低音构成硬朗骨架；吉他与钢琴在中频交替填空。主歌偏干、节奏型明确，副歌增加和声堆叠与鼓组力度；标志性手法是拍手与重拍强调形成集体感，情绪由压抑不甘逐步爆发为复仇宣言。",
            mood="愤怒, 决绝, 张力",
            energy_curve={"intro": 3, "verse": 5, "pre_chorus": 6, "chorus": 9, "bridge": 7, "outro": 6},
            midi_source="",
        ),
        record(
            title="Bad Guy",
            artist="Billie Eilish",
            style="dark pop",
            key="G minor",
            bpm=135,
            time_signature="4/4",
            structure="intro-verse-chorus-verse-chorus-breakdown-outro",
            chord_progression="verse: i-VII-i-VI | chorus: i-VII-VI-V",
            tracks=["lead vocal", "sub bass", "kick", "snare", "finger snap", "synth stab", "whisper backing vocal"],
            arrangement_notes="主旋律以近讲耳语人声呈现，超低频sub bass与稀疏鼓点做主要伴奏，形成极简压迫感。主歌保留大量空拍，副歌与尾段通过低音加厚和音色突变增强冲击；标志性手法是反流行的留白与突兀转场，情绪从冷静挑衅切换到失重式黑暗。",
            mood="冷感, 挑衅, 阴郁",
            energy_curve={"intro": 3, "verse": 5, "chorus": 7, "breakdown": 8, "outro": 6},
            midi_source="",
        ),
        record(
            title="Bohemian Rhapsody",
            artist="Queen",
            style="progressive rock",
            key="B♭ major / G minor",
            bpm=72,
            time_signature="4/4",
            structure="intro-ballad-opera-hard-rock-ballad-outro",
            chord_progression="ballad: I-V/vi-vi-IV-I-IV-V | opera: chromatic modal sequence | rock: I-bVII-I-bVII",
            tracks=["lead vocal", "multi-layer choir", "piano", "electric guitar", "bass", "drums", "orchestral hits"],
            arrangement_notes="主旋律在人声与吉他之间多次交接，钢琴在抒情段承担和声框架，歌剧段由多轨人声堆叠制造戏剧冲突。抒情段编制稀疏，重摇滚段加入失真吉他和全鼓组实现能量跃迁；标志性手法是跨体裁段落拼接与动态断崖式切换，情绪从自白、荒诞到爆裂再回归空落。",
            mood="戏剧化, 史诗, 反差",
            energy_curve={"intro": 2, "ballad": 4, "opera": 8, "hard_rock": 9, "outro": 3},
            midi_source="",
        ),
        record(
            title="Hotel California",
            artist="Eagles",
            style="classic rock",
            key="B minor",
            bpm=75,
            time_signature="4/4",
            structure="intro-verse-chorus-verse-chorus-guitar-solo-chorus-outro",
            chord_progression="verse: i-VII-VI-VII | chorus: i-VII-VI-VII",
            tracks=["lead vocal", "12-string guitar", "electric guitar", "bass", "drums", "conga/shaker", "backing vocal"],
            arrangement_notes="主旋律由人声与尾段双吉他solo共同定义，节奏吉他做和弦铺底，贝斯在句尾推动和声循环。主歌纹理较通透，副歌通过和声与鼓镲打开声场；标志性编曲是双吉他对位solo和拉丁打击乐渗透，情绪从叙事性迷离逐步推进到宿命感高潮。",
            mood="神秘, 漂泊, 电影感",
            energy_curve={"intro": 3, "verse": 5, "chorus": 7, "guitar_solo": 9, "outro": 6},
            midi_source="",
        ),
        record(
            title="Smells Like Teen Spirit",
            artist="Nirvana",
            style="grunge",
            key="F minor",
            bpm=117,
            time_signature="4/4",
            structure="intro-verse-chorus-verse-chorus-bridge-chorus-outro",
            chord_progression="verse: i-IV-bIII-bVI | chorus: i-IV-bIII-bVI",
            tracks=["lead vocal", "distorted guitar", "bass", "drums", "backing vocal"],
            arrangement_notes="主旋律在粗粝人声与主riff吉他间互相强化，贝斯跟随根音保证冲击，鼓组用强反拍维持爆发感。主歌收敛到半清音与低动态，副歌瞬间全失真与吼唱抬升；标志性手法是 quiet-loud 对比，情绪由压抑青年焦躁直接推向失控呐喊。",
            mood="躁动, 反叛, 粗砺",
            energy_curve={"intro": 5, "verse": 4, "chorus": 9, "bridge": 7, "outro": 8},
            midi_source="",
        ),
        record(
            title="Stairway to Heaven",
            artist="Led Zeppelin",
            style="progressive rock",
            key="A minor",
            bpm=82,
            time_signature="4/4",
            structure="intro-verse-verse-verse-build-solo-chorus-outro",
            chord_progression="intro/verse: i-bVII-bVI-C | build: Am-G-F-G | finale: i-bVII-bVI-bVII",
            tracks=["lead vocal", "acoustic guitar", "recorder", "bass", "drums", "electric guitar solo"],
            arrangement_notes="主旋律由人声起始，木吉他分解和弦与竖笛形成空灵前景；后半段电吉他和鼓组接管推动。前段几乎室内乐编制，后段逐步加层到摇滚满编；标志性手法是长线渐强编排，情绪从神秘叙事缓慢堆高至史诗式释放。",
            mood="神秘, 史诗, 递进",
            energy_curve={"intro": 2, "verse": 3, "build": 6, "solo": 8, "finale": 9, "outro": 4},
            midi_source="",
        ),
        record(
            title="Take Five",
            artist="The Dave Brubeck Quartet",
            style="cool jazz",
            key="E♭ minor",
            bpm=174,
            time_signature="5/4",
            structure="intro-theme-sax-solo-piano-solo-drum-solo-theme-outro",
            chord_progression="theme: i-IV7 | solos: i-IV7 modal vamp",
            tracks=["alto sax", "piano", "double bass", "drums"],
            arrangement_notes="主旋律由中音萨克斯演奏，钢琴和低音提琴以5/4切分型提供稳定框架，鼓组在ride上维持流动。主题段旋律清晰、配器克制，独奏段让钢琴与鼓逐步扩展节奏复杂度；标志性手法是非常规拍号中的律动稳定，情绪从冷静都市感推向机智灵动。",
            mood="冷静, 机智, 都市",
            energy_curve={"intro": 3, "theme": 5, "sax_solo": 7, "piano_solo": 7, "drum_solo": 8, "outro": 5},
            midi_source="",
        ),
        record(
            title="So What",
            artist="Miles Davis",
            style="modal jazz",
            key="D Dorian",
            bpm=138,
            time_signature="4/4",
            structure="intro-theme-solo1-solo2-solo3-theme-outro",
            chord_progression="A section: i7 (D Dorian) | B section: bIIm7 (E♭ Dorian) | form: AABA",
            tracks=["trumpet", "tenor sax", "alto sax", "piano", "double bass", "drums"],
            arrangement_notes="主旋律由贝斯标志性问答动机引出并由管乐接手，钢琴以稀疏quartal voicing给和声空间。主题段音符少而清晰，独奏段伴奏保持极简以突出即兴线条；标志性手法是模态和声长时间静置，情绪通过音色和句法变化传达克制却深邃的张力。",
            mood="冷峻, 沉思, 空间感",
            energy_curve={"intro": 2, "theme": 4, "solos": 7, "return_theme": 5, "outro": 3},
            midi_source="",
        ),
        record(
            title="Autumn Leaves",
            artist="Jazz Standard",
            style="jazz standard",
            key="G minor",
            bpm=130,
            time_signature="4/4",
            structure="intro-head-solo1-solo2-head-outro",
            chord_progression="A: iiø7-V7-i | B: iv7-VII7-IIImaj7-VImaj7-iiø7-V7",
            tracks=["lead instrument", "piano or guitar", "double bass", "drums"],
            arrangement_notes="主旋律通常由萨克斯或人声演绎，钢琴/吉他以walking shell voicing支撑，低音提琴负责功能走向。主题段强调旋律线条，独奏段通过comping密度与鼓刷变化增减能量；标志性手法是循环二五一与转调色彩，情绪呈现秋意般温暖与微苦。",
            mood="怀旧, 温暖, 微苦",
            energy_curve={"intro": 2, "head": 5, "solos": 7, "return_head": 5, "outro": 3},
            midi_source="",
        ),
        record(
            title="Superstition",
            artist="Stevie Wonder",
            style="funk / R&B",
            key="E♭ minor",
            bpm=101,
            time_signature="4/4",
            structure="intro-verse-chorus-verse-chorus-bridge-chorus-outro",
            chord_progression="verse: i7-IV7-i7-VII7 | chorus: i7-IV7",
            tracks=["clavinet riff", "lead vocal", "drums", "electric bass", "horns", "percussion"],
            arrangement_notes="主旋律由人声与clavinet主riff共同承担，贝斯和鼓组锁定十六分律动，形成强黏性的口袋感。主歌以riff驱动，副歌加入铜管强调重拍与句尾回应；标志性手法是clavinet切分与鼓贝斯联动，情绪从神秘警示不断推向舞池兴奋。",
            mood="律动, 神秘, 火热",
            energy_curve={"intro": 5, "verse": 7, "chorus": 8, "bridge": 7, "outro": 8},
            midi_source="",
        ),
        record(
            title="No Diggity",
            artist="Blackstreet",
            style="90s R&B / hip-hop soul",
            key="F# minor",
            bpm=92,
            time_signature="4/4",
            structure="intro-verse-chorus-verse-chorus-rap-break-chorus-outro",
            chord_progression="verse: i-VI-VII-i | chorus: i-VI-VII-i",
            tracks=["lead vocal", "rap vocal", "drum machine", "electric piano", "sub bass", "guitar comp"],
            arrangement_notes="主旋律由丝滑主唱和rap段落轮流主导，电钢与低频bassline维持松弛摆动。主歌编制偏薄突出律动空隙，副歌通过和声叠唱和鼓组加层提升记忆点；标志性手法是采样质感鼓机与R&B和声融合，情绪在慵懒与自信之间切换。",
            mood="松弛, 酷感, 都市夜晚",
            energy_curve={"intro": 3, "verse": 5, "chorus": 7, "rap_break": 6, "outro": 5},
            midi_source="",
        ),
        record(
            title="Canon in D",
            artist="Johann Pachelbel",
            style="baroque classical",
            key="D major",
            bpm=56,
            time_signature="4/4",
            structure="ground-bass-variation1-variation2-variation3-variation4-coda",
            chord_progression="ground bass: I-V-vi-iii-IV-I-IV-V",
            tracks=["violin I", "violin II", "violin III", "cello", "continuo"],
            arrangement_notes="主旋律由三把小提琴分层接力，低音大提琴持续重复八和弦地基；伴奏角色是固定低音提供和声锚点，上声部做节奏与织体递进。前段以长音和级进为主，后段通过音符密度增加形成层层推进；标志性手法是固定低音+模进，情绪从庄重平静逐步走向明亮抒情。",
            mood="庄重, 安宁, 典礼感",
            energy_curve={"opening": 2, "variation1": 3, "variation2": 4, "variation3": 5, "variation4": 6, "coda": 4},
            midi_source="",
        ),
        record(
            title="Clair de Lune",
            artist="Claude Debussy",
            style="impressionist classical",
            key="D♭ major",
            bpm=66,
            time_signature="9/8",
            structure="a-theme-development-climax-return-coda",
            chord_progression="A: Imaj9-V/ii-ii9-V | middle: modal mixture and planing | return: I-IV-I",
            tracks=["solo piano"],
            arrangement_notes="主旋律由钢琴右手歌唱线条承担，左手分解和弦像水波般托举；伴奏并非固定节型，而是通过踏板与和声色彩塑造空间。中段音区抬升与和弦密度增加形成高潮，回归段再度稀释织体；标志性手法是印象派和声平行移动，情绪从朦胧夜色走向短暂炽热后回到宁静。",
            mood="朦胧, 诗意, 月夜",
            energy_curve={"a_theme": 2, "development": 4, "climax": 7, "return": 3, "coda": 2},
            midi_source="",
        ),
        record(
            title="Moonlight Sonata (1st Movement)",
            artist="Ludwig van Beethoven",
            style="classical piano sonata",
            key="C# minor",
            bpm=52,
            time_signature="4/4",
            structure="intro-exposition-development-recap-coda",
            chord_progression="main: i-V6-iv6-V | middle: VI-iv-ii°-V | return: i-iv-V-i",
            tracks=["solo piano"],
            arrangement_notes="主旋律隐藏在右手上声部内音中，左手持续三连音分解和弦形成阴影般伴奏；两者关系是旋律若隐若现、伴奏持续流动。段落推进主要靠和声转折与音区扩展而非节奏变化；标志性手法是持续音型与弱动态控制，情绪由压抑沉思缓慢积聚成宿命感。",
            mood="阴郁, 沉思, 宿命",
            energy_curve={"intro": 2, "exposition": 3, "development": 5, "recap": 4, "coda": 3},
            midi_source="",
        ),
        record(
            title="Für Elise",
            artist="Ludwig van Beethoven",
            style="classical piano",
            key="A minor",
            bpm=118,
            time_signature="3/8",
            structure="a-b-a-c-a",
            chord_progression="A: i-V/V-V-i | B: iv-i-V-i | C: VI-III-V-i",
            tracks=["solo piano"],
            arrangement_notes="主旋律由右手标志性回旋动机承担，左手以分解和弦和低音跳进支撑和声。A段轻巧透明，B/C段通过调性偏移与音区扩展制造对比；标志性手法是回旋主题反复回归，情绪在俏皮与微忧之间摆动，形成强识别度。",
            mood="优雅, 俏皮, 微忧",
            energy_curve={"a1": 3, "b": 5, "a2": 3, "c": 6, "a3": 4},
            midi_source="",
        ),
        record(
            title="Yesterday",
            artist="The Beatles",
            style="folk pop",
            key="F major",
            bpm=97,
            time_signature="4/4",
            structure="intro-verse-verse-bridge-verse-outro",
            chord_progression="verse: I-vii°/V-iii-vi-IV-I-ii-V | bridge: iii-VI-ii-V",
            tracks=["lead vocal", "acoustic guitar", "string quartet"],
            arrangement_notes="主旋律由人声主导，木吉他负责和声框架，弦乐四重奏在句尾做回应与延音。主歌保持亲密室内乐质感，桥段通过弦乐和声密度提升制造情绪波峰；标志性手法是简编制与古典弦乐结合，情绪从回忆式低语逐渐扩展成遗憾叹息。",
            mood="怀旧, 温柔, 遗憾",
            energy_curve={"intro": 2, "verse": 4, "bridge": 6, "final_verse": 5, "outro": 3},
            midi_source="",
        ),
        record(
            title="Take Me Home, Country Roads",
            artist="John Denver",
            style="country / folk",
            key="A major",
            bpm=82,
            time_signature="4/4",
            structure="intro-verse-chorus-verse-chorus-bridge-chorus-outro",
            chord_progression="verse: I-V-vi-IV | chorus: I-V-IV-I",
            tracks=["lead vocal", "acoustic guitar", "electric guitar", "bass", "drums", "backing vocal"],
            arrangement_notes="主旋律由人声唱出叙事线，木吉他扫弦和电吉他填句构成伴奏对话；贝斯和鼓组保持稳健公路节拍。主歌偏叙事、配器简洁，副歌加入群唱扩大空间；标志性手法是集体和声在副歌集中释放，情绪从思乡独白升华为群体共鸣。",
            mood="思乡, 温暖, 开阔",
            energy_curve={"intro": 3, "verse": 4, "chorus": 7, "bridge": 5, "outro": 6},
            midi_source="",
        ),
        record(
            title="Hallelujah",
            artist="Leonard Cohen",
            style="folk ballad",
            key="C major",
            bpm=56,
            time_signature="6/8",
            structure="intro-verse-verse-verse-verse-outro",
            chord_progression="verse: I-vi-I-vi | IV-V-I-V | vi-IV-V-I",
            tracks=["lead vocal", "acoustic guitar", "piano", "subtle strings", "backing vocal"],
            arrangement_notes="主旋律由人声叙述推进，木吉他/钢琴以缓慢分解和弦托住和声重心，伴奏角色强调词句间停顿。前段极简编制突出文本，后段通过和声与弦乐微量加层提升庄严感；标志性手法是循环和弦与段落堆叠，情绪从私密祈祷逐步转为宗教式肃穆。",
            mood="神圣, 哀婉, 沉静",
            energy_curve={"intro": 1, "verse1": 3, "verse2": 4, "verse3": 5, "verse4": 6, "outro": 2},
            midi_source="",
        ),
        record(
            title="Despacito",
            artist="Luis Fonsi",
            style="latin pop / reggaeton",
            key="B minor",
            bpm=89,
            time_signature="4/4",
            structure="intro-verse-pre-chorus-chorus-verse-pre-chorus-chorus-rap-chorus-outro",
            chord_progression="verse: i-VI-III-VII | chorus: i-VI-III-VII",
            tracks=["lead vocal", "nylon guitar", "reggaeton dembow beat", "bass", "synth pad", "backing vocal"],
            arrangement_notes="主旋律由主唱与rap交替完成，尼龙吉他提供拉丁和声纹理，dembow鼓型与低音维持身体律动。主歌相对稀疏突出节奏摆动，副歌叠加和声和高频打击形成热度提升；标志性手法是拉丁吉他与都市节拍混合，情绪从暧昧挑逗推进至庆典式释放。",
            mood="热情, 性感, 夏日",
            energy_curve={"intro": 3, "verse": 5, "pre_chorus": 6, "chorus": 8, "rap": 7, "outro": 6},
            midi_source="",
        ),
        record(
            title="Bésame Mucho",
            artist="Consuelo Velázquez",
            style="bolero",
            key="D minor",
            bpm=96,
            time_signature="4/4",
            structure="intro-verse-a2-bridge-verse-outro",
            chord_progression="A: i-V7-i | B: iv-V7-i | bridge: III7-VI7-iiø7-V7",
            tracks=["lead vocal", "piano", "nylon guitar", "upright bass", "brush drums", "strings"],
            arrangement_notes="主旋律多由人声或独奏乐器歌唱化处理，钢琴与尼龙吉他分担和弦节奏，低音与刷鼓控制舞曲摆动。主段强调旋律连贯和 rubato 处理，桥段以和声转折提升戏剧性；标志性手法是半音和声与长线旋律结合，情绪从亲密低语转向浓烈眷恋。",
            mood="浪漫, 复古, 眷恋",
            energy_curve={"intro": 2, "verse": 4, "a2": 5, "bridge": 6, "outro": 3},
            midi_source="",
        ),
        record(
            title="Levels",
            artist="Avicii",
            style="EDM / progressive house",
            key="C# minor",
            bpm=126,
            time_signature="4/4",
            structure="intro-build-drop-break-build-drop-outro",
            chord_progression="drop: i-VI-III-VII | break: i-VI-III-VII",
            tracks=["vocal sample", "supersaw lead", "sidechained synth chords", "sub bass", "kick", "clap", "fx riser", "white noise"],
            arrangement_notes="主旋律由采样人声与supersaw lead共同定义，伴奏核心是四拍kick与侧链和弦泵动，低音负责能量底座。build段逐步抽离低频并叠加噪声上升，drop段一次性回填全频；标志性手法是大跨度动态反差与简洁和声循环，情绪从期待拉升到集体狂欢。",
            mood="亢奋, 明亮, 节庆",
            energy_curve={"intro": 3, "build1": 6, "drop1": 9, "break": 4, "build2": 7, "drop2": 10, "outro": 5},
            midi_source="",
        ),
        record(
            title="Strobe",
            artist="deadmau5",
            style="progressive house",
            key="A minor",
            bpm=128,
            time_signature="4/4",
            structure="ambient-intro-build-main-theme-breakdown-rebuild-climax-outro",
            chord_progression="main: i-VI-III-VII | breakdown: i-VI-III-VII",
            tracks=["ambient pad", "plucked synth", "arpeggiator", "kick", "bass", "lead synth", "fx textures"],
            arrangement_notes="主旋律由中后段lead synth接管，前段以氛围pad和琶音铺垫；伴奏角色重在长时间层次堆叠而非早期鼓点密集。前半几乎无鼓的空间营造与后半全节拍形成强反差；标志性手法是超长build与渐进滤波，情绪由漂浮冥想推进到高峰释然。",
            mood="沉浸, 渐进, 释然",
            energy_curve={"ambient_intro": 1, "build": 4, "main_theme": 7, "breakdown": 5, "rebuild": 8, "climax": 9, "outro": 3},
            midi_source="",
        ),
        record(
            title="The Thrill Is Gone",
            artist="B.B. King",
            style="blues",
            key="B minor",
            bpm=84,
            time_signature="4/4",
            structure="intro-verse-verse-guitar-solo-verse-outro",
            chord_progression="12-bar minor blues: i7-iv7-i7-V7-iv7-i7",
            tracks=["lead vocal", "electric guitar", "strings", "bass", "drums", "piano"],
            arrangement_notes="主旋律由人声和吉他lick轮流叙述，吉他在句尾回应歌词，形成典型call-and-response。主歌保持中低动态突出叙事，solo段拉开音区并增加延音与弯音强度；标志性手法是布鲁斯弯音与空拍呼吸，情绪把失落与尊严并置，呈现克制的痛感。",
            mood="忧伤, 沧桑, 克制",
            energy_curve={"intro": 2, "verse": 4, "guitar_solo": 7, "final_verse": 5, "outro": 3},
            midi_source="",
        ),
        record(
            title="No Woman, No Cry",
            artist="Bob Marley & The Wailers",
            style="reggae",
            key="C major",
            bpm=78,
            time_signature="4/4",
            structure="intro-verse-chorus-verse-chorus-bridge-chorus-outro",
            chord_progression="verse: I-V-vi-IV | chorus: I-V-vi-IV",
            tracks=["lead vocal", "rhythm guitar skank", "organ bubble", "bass", "drums", "backing vocal"],
            arrangement_notes="主旋律由人声稳定叙事，反拍skank吉他与organ bubble构成雷鬼标志伴奏，贝斯负责旋律化低频线条。主歌配器简洁强调故事感，副歌加入群唱与更宽声场增强抚慰力；标志性手法是反拍节奏与温暖和声，情绪从现实困顿转向安慰与团结。",
            mood="抚慰, 坚韧, 温暖",
            energy_curve={"intro": 2, "verse": 4, "chorus": 6, "bridge": 5, "outro": 4},
            midi_source="",
        ),
        record(
            title="Lose Yourself",
            artist="Eminem",
            style="hip-hop",
            key="D minor",
            bpm=171,
            time_signature="4/4",
            structure="intro-verse-chorus-verse-chorus-verse-chorus-outro",
            chord_progression="loop: i-bVII-bVI-bVII | chorus: i-bVII-bVI-bVII",
            tracks=["rap vocal", "piano riff", "string stabs", "bass", "kick", "snare", "hi-hat"],
            arrangement_notes="主旋律由rap flow承担，钢琴riff是全曲识别核心；鼓组与贝斯保持直给推进，弦乐点缀强化戏剧压力。verse段以紧凑节奏和较少和声变化聚焦叙事，chorus通过和声厚度与打击乐增强形成口号感；标志性手法是循环riff与递进语速，情绪持续堆高到背水一战。",
            mood="紧张, 斗志, 爆发",
            energy_curve={"intro": 3, "verse1": 6, "chorus1": 7, "verse2": 7, "chorus2": 8, "verse3": 8, "chorus3": 9},
            midi_source="",
        ),
        record(
            title="Billie Jean",
            artist="Michael Jackson",
            style="pop / funk",
            key="F# minor",
            bpm=117,
            time_signature="4/4",
            structure="intro-verse-pre-chorus-chorus-verse-pre-chorus-chorus-bridge-chorus-outro",
            chord_progression="verse: i-VII-i-VII | chorus: i-VII-VI-VII",
            tracks=["lead vocal", "iconic bassline", "drums", "rhythm guitar", "synth strings", "backing vocal"],
            arrangement_notes="主旋律由人声与贝斯riff双核心驱动，鼓组保持极稳八分律动，吉他切分提供中频黏合。主歌聚焦贝斯与鼓的空隙美学，副歌通过和声与弦乐加层抬升戏剧感；标志性手法是高辨识度低音动机反复，情绪从悬疑叙事持续推向压迫高潮。",
            mood="悬疑, 酷感, 张力",
            energy_curve={"intro": 4, "verse": 6, "pre_chorus": 7, "chorus": 8, "bridge": 7, "outro": 6},
            midi_source="",
        ),
        record(
            title="Imagine",
            artist="John Lennon",
            style="pop ballad",
            key="C major",
            bpm=75,
            time_signature="4/4",
            structure="intro-verse-verse-chorus-verse-chorus-outro",
            chord_progression="verse: I-Imaj7-IV-IVm | chorus: F-G-C-Cmaj7",
            tracks=["lead vocal", "piano", "bass", "drums", "strings"],
            arrangement_notes="主旋律由人声平稳陈述，钢琴作为主要伴奏以块和弦与分解和弦交替；贝斯和鼓组极度克制只在关键拍点支撑。主歌保持近乎独白的空间，副歌加入轻量和声与弦乐扩展情绪；标志性手法是简洁和声与留白，情绪从理性愿景转化为温柔号召。",
            mood="平和, 理想主义, 温暖",
            energy_curve={"intro": 1, "verse1": 3, "verse2": 4, "chorus1": 5, "verse3": 4, "chorus2": 6, "outro": 2},
            midi_source="",
        ),
        record(
            title="Sweet Child O' Mine",
            artist="Guns N' Roses",
            style="hard rock",
            key="D major",
            bpm=125,
            time_signature="4/4",
            structure="intro-verse-chorus-verse-chorus-solo-breakdown-final-chorus-outro",
            chord_progression="verse: I-bVII-IV | chorus: D-C-G-D | breakdown: vi-C-G-D",
            tracks=["lead vocal", "iconic lead guitar riff", "rhythm guitar", "bass", "drums", "guitar solo"],
            arrangement_notes="主旋律由人声与开场吉他riff共同定义，节奏吉他和贝斯构成厚实中低频墙体。主歌相对收束以突出riff，副歌和solo段鼓组与吉他全面打开；标志性手法是高辨识度riff贯穿全曲并在尾段延展，情绪从怀旧甜美逐步转向热血宣泄。",
            mood="热血, 怀旧, 释放",
            energy_curve={"intro": 6, "verse": 5, "chorus": 8, "solo": 9, "breakdown": 6, "final_chorus": 9, "outro": 7},
            midi_source="",
        ),
    ]


def ensure_song_analyses_columns(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(song_analyses)")
    existing_cols = {str(row[1]) for row in cur.fetchall()}

    if "mood" not in existing_cols:
        cur.execute("ALTER TABLE song_analyses ADD COLUMN mood TEXT DEFAULT ''")
    if "energy_curve" not in existing_cols:
        cur.execute("ALTER TABLE song_analyses ADD COLUMN energy_curve TEXT DEFAULT ''")
    conn.commit()


def seed_song_analyses() -> tuple[int, int]:
    init_db()
    search_results = load_search_results(SEARCH_JSON_PATH)
    fallback_urls = [r["url"] for r in search_results if r.get("url")][:3]

    dataset = build_dataset()
    payload: list[dict[str, Any]] = []
    for row in dataset:
        urls = match_search_urls(row["title"], row["artist"], search_results, fallback_urls)
        payload.append(
            {
                **row,
                "tracks": to_json_text(row["tracks"]),
                "energy_curve": to_json_text(row["energy_curve"]),
                "source": build_source(row["title"], row["artist"], urls),
            }
        )

    conn = sqlite3.connect(DB_PATH)
    ensure_song_analyses_columns(conn)
    cur = conn.cursor()

    for row in payload:
        cur.execute(
            "DELETE FROM song_analyses WHERE title = ? AND artist = ?",
            (row["title"], row["artist"]),
        )

    cur.executemany(
        """
        INSERT INTO song_analyses (
            title, artist, style, key, bpm, time_signature, structure,
            chord_progression, tracks, arrangement_notes, mood, energy_curve,
            midi_source, source
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                row["title"],
                row["artist"],
                row["style"],
                row["key"],
                row["bpm"],
                row["time_signature"],
                row["structure"],
                row["chord_progression"],
                row["tracks"],
                row["arrangement_notes"],
                row["mood"],
                row["energy_curve"],
                row["midi_source"],
                row["source"],
            )
            for row in payload
        ],
    )
    conn.commit()

    cur.execute("SELECT COUNT(*) FROM song_analyses")
    total_count = int(cur.fetchone()[0])
    conn.close()
    return len(payload), total_count


def main() -> None:
    inserted, total = seed_song_analyses()
    print(f"Inserted {inserted} song analyses. song_analyses total rows: {total}.")


if __name__ == "__main__":
    main()
