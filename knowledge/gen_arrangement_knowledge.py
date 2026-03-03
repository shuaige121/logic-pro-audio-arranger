#!/usr/bin/env python3
"""Generate arrangement/melody/voice-leading knowledge and save into SQLite."""

from __future__ import annotations

import re
import sqlite3
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from knowledge.brave_search import batch_search, search
from knowledge.init_db import init_db

DB_PATH = Path(__file__).parent / "knowledge.db"
SOURCE_PREFIX = "gen_arrangement_knowledge"


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def clean_snippet(text: str, max_len: int = 180) -> str:
    text = normalize_whitespace(text)
    if len(text) <= max_len:
        return text
    return text[: max_len - 3].rstrip() + "..."


def dedupe_by_name(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for rec in records:
        name = normalize_whitespace(str(rec.get("name", ""))).casefold()
        if not name or name in seen:
            continue
        seen.add(name)
        deduped.append(rec)
    return deduped


def pick_best_result(results: list[dict[str, str]], keywords: list[str]) -> dict[str, str] | None:
    if not results:
        return None
    lowered = [k.casefold() for k in keywords]
    best_score = -1
    best: dict[str, str] | None = None
    for item in results:
        blob = f"{item.get('title', '')} {item.get('description', '')}".casefold()
        score = sum(1 for k in lowered if k in blob)
        if score > best_score:
            best_score = score
            best = item
    return best if best is not None else results[0]


def enrich_description(base_text: str, result: dict[str, str] | None) -> str:
    if not result:
        return base_text
    snippet = clean_snippet(result.get("description", ""))
    if not snippet:
        return base_text
    return f"{base_text} 参考线索：{snippet}"


def result_source(result: dict[str, str] | None, fallback_tag: str) -> str:
    if result and result.get("url"):
        return f"{SOURCE_PREFIX}:brave|{result['url']}"
    return f"{SOURCE_PREFIX}:{fallback_tag}"


VOICE_LEADING_HARDCODED: list[dict[str, Any]] = [
    {
        "name": "Avoid Parallel Perfect Fifths and Octaves",
        "rule_text": "两个声部从一个纯五度或纯八度平行移动到另一个纯五度/纯八度会削弱独立性，四部写作中应避免。",
        "category": "parallel_motion",
        "priority": 10,
    },
    {
        "name": "Retain Common Tones",
        "rule_text": "和弦转换时，若声部可保持共同音不动，应优先保持以获得平滑连接。",
        "category": "smoothness",
        "priority": 8,
    },
    {
        "name": "Prefer Contrary Motion",
        "rule_text": "声部进行中反向进行通常比同向进行更稳定，尤其外声部更应优先反向。",
        "category": "motion_balance",
        "priority": 9,
    },
    {
        "name": "Leading Tone Resolves to Tonic",
        "rule_text": "在主调语境下，导音（7级）通常上行半音解决到主音（1级）。",
        "category": "tendency_tone",
        "priority": 10,
    },
    {
        "name": "Chordal Seventh Resolves Downward",
        "rule_text": "属七或其他七和弦中的七音通常下行级进解决。",
        "category": "tendency_tone",
        "priority": 10,
    },
    {
        "name": "No Voice Crossing",
        "rule_text": "下方声部音高不应高于上方声部，避免声部交叉导致层次混乱。",
        "category": "spacing",
        "priority": 9,
    },
    {
        "name": "Upper Voices Within an Octave",
        "rule_text": "女高-女低、女低-男高等相邻上声部间距通常不超过八度，保证融合度。",
        "category": "spacing",
        "priority": 8,
    },
    {
        "name": "Bass May Leap with Compensation",
        "rule_text": "低音允许四度、五度、八度等跳进，但应通过后续反向或级进平衡线条。",
        "category": "bass_motion",
        "priority": 7,
    },
    {
        "name": "Contrary Motion in Outer Voices",
        "rule_text": "终止、转位或功能转换时，外声部优先采用反向进行以提升清晰度。",
        "category": "cadential",
        "priority": 8,
    },
    {
        "name": "Avoid Hidden Fifths and Octaves",
        "rule_text": "外声部同向进行并跳进到纯五/纯八（隐伏五八）应谨慎，尤其高声部跳进时通常避免。",
        "category": "parallel_motion",
        "priority": 9,
    },
    {
        "name": "Prepare and Resolve Suspensions",
        "rule_text": "挂留音需先准备（前一和弦为协和），再在下一拍按级进解决，常见为下行解决。",
        "category": "dissonance_control",
        "priority": 9,
    },
    {
        "name": "V7 to I Resolution Map",
        "rule_text": "属七到主和弦时，3音（导音）上行到1，7音下行到3或1，优先保持共同音与反向外声部。",
        "category": "cadential",
        "priority": 10,
    },
    {
        "name": "Do Not Double Leading Tone",
        "rule_text": "三和弦配器中通常避免导音加倍，以减少强烈不稳定倾向造成的解决压力。",
        "category": "doubling",
        "priority": 9,
    },
    {
        "name": "Double Stable Chord Tones",
        "rule_text": "根位三和弦优先加倍根音；一转位常加倍稳定音，避免加倍倾向音。",
        "category": "doubling",
        "priority": 8,
    },
    {
        "name": "Dissonance by Stepwise Treatment",
        "rule_text": "非和声音（经过、辅助、延留等）通常以级进进入或离开，减少生硬跳出。",
        "category": "dissonance_control",
        "priority": 8,
    },
    {
        "name": "Melodic Singability in Each Voice",
        "rule_text": "各声部都应保持可唱性，避免连续大跳和难以自然解决的增减音程。",
        "category": "line_quality",
        "priority": 7,
    },
]


VOICE_LEADING_BRAVE_TEMPLATES: list[dict[str, Any]] = [
    {
        "name": "Resolve Tendency Tones in Secondary Dominants",
        "rule_text": "次属和弦中的临时导音仍应按目标和弦方向解决，避免无准备离开。",
        "category": "tendency_tone",
        "priority": 8,
        "keywords": ["secondary dominant", "leading tone", "resolution"],
    },
    {
        "name": "Use 6/4 Chords as Controlled Functions",
        "rule_text": "终止6/4、经过6/4、辅助6/4应按功能处理，不把二转位三和弦当稳定主功能长期停留。",
        "category": "cadential",
        "priority": 8,
        "keywords": ["cadential 6/4", "second inversion", "passing 6/4"],
    },
    {
        "name": "Prepare Large Leaps with Opposite Recovery",
        "rule_text": "单声部出现六度以上跳进后，通常用反向级进回收轮廓，保持线条可唱。",
        "category": "line_quality",
        "priority": 7,
        "keywords": ["large leap", "recovery", "stepwise", "melodic line"],
    },
    {
        "name": "Avoid Unequal Fifth Relation in Similar Motion",
        "rule_text": "外声部同向到纯五时若由减五或增四引出，需要谨慎以避免听感上的平行趋同。",
        "category": "parallel_motion",
        "priority": 7,
        "keywords": ["unequal fifth", "similar motion", "voice leading"],
    },
    {
        "name": "Control Unison Usage Between Inner Voices",
        "rule_text": "短时同音可用于重音强化，但持续同音会削弱复调独立性，需尽快分离。",
        "category": "independence",
        "priority": 6,
        "keywords": ["unison", "inner voices", "independence"],
    },
    {
        "name": "Keep Soprano as Direction Anchor",
        "rule_text": "高声部通常承担感知主线，和声转换时可先保证其流畅再分配内声部。",
        "category": "line_quality",
        "priority": 6,
        "keywords": ["soprano line", "top voice", "voice leading"],
    },
]


ARRANGEMENT_HARDCODED: list[dict[str, Any]] = [
    {
        "name": "Layering for Thickness",
        "style": "general",
        "category": "texture",
        "description": "同一和声材料在不同音区或不同音色叠加，可显著提升密度与能量；需通过频段分工避免互相遮蔽。",
        "example": "副歌把钢琴和弦与合成器pad叠加，钢琴突出瞬态，pad负责延展。",
    },
    {
        "name": "Octave Doubling",
        "style": "general",
        "category": "texture",
        "description": "把同一旋律或动机在八度上加倍，可增强清晰度与穿透力，同时保持音高身份一致。",
        "example": "主旋律由女声与高八度吉他同步演奏，形成更强记忆点。",
    },
    {
        "name": "Section Contrast",
        "style": "general",
        "category": "form",
        "description": "段落之间在配器、和声节奏、密度与动态上形成可感差异，防止整曲单调平铺。",
        "example": "主歌保留鼓+贝斯，副歌加入和声铺底与高频打击。",
    },
    {
        "name": "Builds and Drops",
        "style": "general",
        "category": "dynamics",
        "description": "通过逐步加层、上行噪声、滚奏与节奏加密建立预期，再通过drop释放张力。",
        "example": "EDM预副歌逐渐加快军鼓滚奏，drop处低频与主lead同时进入。",
    },
    {
        "name": "Countermelody",
        "style": "general",
        "category": "texture",
        "description": "在主旋律旁加入次旋律，使用互补节奏与反向轮廓，增强横向流动与复调感。",
        "example": "副歌人声长音时，弦乐做短句对位填补空隙。",
    },
    {
        "name": "Fills",
        "style": "general",
        "category": "rhythm",
        "description": "在句尾或段落边界用短填充连接结构节点，提示听众即将转场。",
        "example": "每4小节末尾加入鼓fill，引导进入下一乐句。",
    },
    {
        "name": "Rests and Space",
        "style": "general",
        "category": "texture",
        "description": "主动留白可让主元素更清晰，并提高后续进入新层时的对比感与冲击力。",
        "example": "副歌前最后半拍全体休止，下一拍主旋律进入更醒目。",
    },
    {
        "name": "Dynamic Variation",
        "style": "general",
        "category": "dynamics",
        "description": "利用力度起伏、渐强渐弱和编配密度配合，形成情绪弧线而非恒定能量。",
        "example": "桥段整体降到mp，结尾再逐步推至ff。",
    },
    {
        "name": "Timbral Contrast",
        "style": "general",
        "category": "texture",
        "description": "不同段落切换主导音色可重置听觉注意力，让重复和声也保持新鲜感。",
        "example": "主歌以电钢为主，副歌改由失真吉他与铜管主导。",
    },
    {
        "name": "Rhythmic Density Shift",
        "style": "general",
        "category": "rhythm",
        "description": "通过音符时值与事件密度变化控制推进速度，常用于预副歌到副歌的抬升。",
        "example": "主歌以四分音符为主，预副歌加入十六分切分音型。",
    },
    {
        "name": "Call and Response",
        "style": "general",
        "category": "form",
        "description": "把素材分成问句与答句，在不同乐器或声部间对话，提升结构辨识度。",
        "example": "人声唱问句后，铜管短句模仿回应。",
    },
    {
        "name": "Harmonic Rhythm Control",
        "style": "general",
        "category": "rhythm",
        "description": "和弦更替速度决定段落张力；慢更替更稳，快更替更紧凑，可配合歌词密度调整。",
        "example": "主歌每小节一和弦，副歌改为每半小节一和弦制造推进。",
    },
    {
        "name": "Texture Changes",
        "style": "general",
        "category": "texture",
        "description": "在齐奏、主旋律+伴奏、分层复调等纹理间切换，塑造段落层次与呼吸。",
        "example": "第一遍副歌齐奏，第二遍副歌改为分层和声+对位。",
    },
    {
        "name": "Transition Devices",
        "style": "general",
        "category": "form",
        "description": "使用反拍切入、反向音效、上行过门、和声预告等手法平滑跨段落跳转。",
        "example": "桥段结束用反向镲片和导向音过门进入最终副歌。",
    },
    {
        "name": "Endings and Outros",
        "style": "general",
        "category": "form",
        "description": "结尾可采用突然收束、循环淡出、终止式延长或主旋律回收，以统一叙事闭环。",
        "example": "最后一次副歌后保留主hook并逐层减配淡出。",
    },
]


ARRANGEMENT_BRAVE_TEMPLATES: list[dict[str, Any]] = [
    {
        "name": "Register Zoning",
        "style": "general",
        "category": "texture",
        "description": "把低中高频段分配给不同乐器组，避免所有元素堆在同一音区导致混浊。",
        "example": "贝斯占低频、钢琴占中频、铃音和空气感元素占高频。",
        "keywords": ["register", "orchestration", "frequency", "arrangement"],
    },
    {
        "name": "Pedal Point Anchor",
        "style": "general",
        "category": "form",
        "description": "在低声部或中声部持续保持一个音，叠加和声变化形成张力与统一感。",
        "example": "副歌持续低音5级，上方和弦轮换制造推进。",
        "keywords": ["pedal point", "sustained note", "orchestration"],
    },
    {
        "name": "Ostinato Bed",
        "style": "general",
        "category": "rhythm",
        "description": "使用短循环音型作为底层驱动，让段落在稳定重复中承载旋律与和声变化。",
        "example": "弦乐八分音符ostinato贯穿预副歌，鼓组负责逐步加速感。",
        "keywords": ["ostinato", "pattern", "arrangement", "orchestration"],
    },
    {
        "name": "Dropout Before Chorus",
        "style": "pop",
        "category": "dynamics",
        "description": "副歌前短暂抽离鼓组或低频，制造真空再回归全编制以放大冲击。",
        "example": "预副歌最后一小节仅留人声与pad，副歌全体回归。",
        "keywords": ["dropout", "before chorus", "arrangement tip"],
    },
    {
        "name": "Instrument Rotation",
        "style": "general",
        "category": "texture",
        "description": "重复动机在不同乐器间轮换呈现，在保持主题统一的同时避免疲劳。",
        "example": "主旋律先由钢琴演奏，第二遍交给弦乐，第三遍由合成器接管。",
        "keywords": ["instrumentation", "rotation", "motif", "arrangement"],
    },
    {
        "name": "Ear Candy Inserts",
        "style": "pop",
        "category": "rhythm",
        "description": "在句尾或空拍处加入短促音效与装饰线条，增强可重复聆听价值。",
        "example": "每两小节末尾加入反向吸气与短上行琶音点缀。",
        "keywords": ["ear candy", "production", "arrangement"],
    },
    {
        "name": "Unison Accent Hits",
        "style": "general",
        "category": "rhythm",
        "description": "多个乐器在关键拍点齐奏重音，可强化节奏骨架和段落标记。",
        "example": "副歌首拍鼓、贝斯、铜管同步重击。",
        "keywords": ["unison", "accent", "hit", "orchestration"],
    },
    {
        "name": "Low-End Management by Section",
        "style": "general",
        "category": "texture",
        "description": "按段落管理低频元素数量，避免整曲低频持续过满导致对比不足。",
        "example": "主歌只留贝斯，副歌再加入低音合成器加厚。",
        "keywords": ["low end", "section", "arrangement", "production"],
    },
    {
        "name": "Pre-Chorus Lift",
        "style": "pop",
        "category": "form",
        "description": "预副歌通过上行和声、节奏加密与配器扩展，为副歌建立预期与抬升。",
        "example": "预副歌连用一级上行动机并逐层加入和声人声。",
        "keywords": ["pre-chorus", "lift", "song arrangement"],
    },
    {
        "name": "Automation-Led Dynamics",
        "style": "edm",
        "category": "dynamics",
        "description": "使用音量、滤波、混响发送等自动化在不换素材的情况下制造动态起伏。",
        "example": "build段逐步打开低通滤波并提高混响发送量。",
        "keywords": ["automation", "filter sweep", "dynamic", "production arrangement"],
    },
    {
        "name": "Percussion Layer Staggering",
        "style": "general",
        "category": "rhythm",
        "description": "打击层按段落交错进入而非同时堆满，可在保持律动下形成纵向演化。",
        "example": "先进入clap，再加入shaker，最后加入高频闭镲滚奏。",
        "keywords": ["percussion layering", "stagger", "groove arrangement"],
    },
    {
        "name": "Arrangement by Role Separation",
        "style": "general",
        "category": "texture",
        "description": "把每个声部明确为主旋律、和声支撑、节奏驱动或装饰角色，避免功能重叠。",
        "example": "人声主旋律、钢琴和声、贝斯根音、合成器负责装饰过门。",
        "keywords": ["role", "arrangement", "orchestration", "support"],
    },
]


MELODY_HARDCODED: list[dict[str, Any]] = [
    {
        "name": "Stepwise Motion",
        "category": "motion",
        "description": "旋律以级进为主更易歌唱和记忆，尤其在主句中可提高自然流畅度。",
        "example": "主歌句首使用1-2-3-2的级进轮廓建立亲和感。",
    },
    {
        "name": "Leaps with Recovery",
        "category": "motion",
        "description": "跳进可快速制造强调，但后续常用反向级进回收，维持可唱性。",
        "example": "高点八度跳进后，连续下行级进回落。",
    },
    {
        "name": "Sequence",
        "category": "development",
        "description": "将动机按同一音程关系平移，能在重复中产生推进感和结构感。",
        "example": "动机先在I和弦出现，随后上移二度在ii上重复。",
    },
    {
        "name": "Inversion",
        "category": "development",
        "description": "保持节奏与音程关系方向相反，可得到既相关又新鲜的旋律版本。",
        "example": "原型上行三度改为下行三度，节奏不变。",
    },
    {
        "name": "Retrograde",
        "category": "development",
        "description": "按时间反向重排动机，适合作为桥段或过渡材料以形成呼应。",
        "example": "原动机四音按逆序出现在乐句尾端。",
    },
    {
        "name": "Rhythmic Variation",
        "category": "rhythm",
        "description": "在保持音高核心不变时改变节奏型，可增加重复段落的变化度。",
        "example": "第一次用四分音符，第二次改为附点与切分组合。",
    },
    {
        "name": "Ornamentation",
        "category": "ornament",
        "description": "倚音、波音、滑音等装饰可强化风格特征，但应服务主旋律重音点。",
        "example": "长音前加上方短倚音增强情绪张力。",
    },
    {
        "name": "Motivic Development",
        "category": "development",
        "description": "通过拆分、扩展、缩短与重组同一动机构建整段旋律的一致性。",
        "example": "副歌先给完整动机，后半句只保留前两音作重复强化。",
    },
    {
        "name": "Antecedent-Consequent Period",
        "category": "form",
        "description": "问答句结构用不完全终止提出问题，再用较稳定落点回应，易形成句法感。",
        "example": "前句停在2级，后句回到1级完成回答。",
    },
    {
        "name": "Climax Placement",
        "category": "form",
        "description": "把最高音或最长重音放在段落后半，可制造“到达感”并避免过早泄力。",
        "example": "副歌第6小节出现全段最高音作为情绪峰值。",
    },
    {
        "name": "Hook Design Principles",
        "category": "hook",
        "description": "hook通常短小、重复、节奏明确并与歌词重音对齐，便于快速记忆。",
        "example": "4音核心动机在副歌重复三次，仅结尾音变化。",
    },
    {
        "name": "Melodic Contour Types",
        "category": "contour",
        "description": "常见轮廓包括拱形、下行、上行、波浪形，不同轮廓适配不同情绪叙事。",
        "example": "主歌用下行轮廓营造叙述感，副歌改为上行拱形提升张力。",
    },
]


MELODY_BRAVE_TEMPLATES: list[dict[str, Any]] = [
    {
        "name": "Chord-Tone Targeting",
        "category": "harmony_link",
        "description": "强拍优先落在和弦音，弱拍可穿插非和声音，能同时保证稳定与流动。",
        "example": "每小节第一拍落根音或三音，其余拍使用经过音连接。",
        "keywords": ["chord tone", "target note", "melody writing"],
    },
    {
        "name": "Repetition with Small Mutation",
        "category": "development",
        "description": "重复同一短句并仅改变结尾音或节奏，能兼顾记忆度与新鲜度。",
        "example": "前两小节相同，第三小节只把句尾上移二度。",
        "keywords": ["repetition", "variation", "melody"],
    },
    {
        "name": "Rhythmic Displacement",
        "category": "rhythm",
        "description": "将同一动机前移或后移半拍/一拍，可在不改音高的前提下获得新律动。",
        "example": "副歌第二遍把动机起点从强拍改到反拍。",
        "keywords": ["rhythmic displacement", "syncopation", "melody"],
    },
    {
        "name": "Fragmentation",
        "category": "development",
        "description": "把完整旋律拆成更短片段反复处理，常用于build段制造紧张感。",
        "example": "只取主hook前3音做连续上行重复。",
        "keywords": ["fragmentation", "motif", "melodic development"],
    },
    {
        "name": "Range Expansion Across Sections",
        "category": "form",
        "description": "主歌保持较窄音域，副歌扩大音域与高点，形成段落能量差。",
        "example": "主歌在五度内活动，副歌扩展到九度范围。",
        "keywords": ["range", "verse chorus", "melody writing"],
    },
    {
        "name": "Prosody Alignment",
        "category": "lyric_link",
        "description": "歌词重音和语义关键词应对齐旋律重拍或高点，提升表达自然度。",
        "example": "关键词放在长时值或高音位置，弱词放在经过位置。",
        "keywords": ["prosody", "lyric stress", "songwriting melody"],
    },
    {
        "name": "Tension-Release via Non-Chord Tones",
        "category": "harmony_link",
        "description": "在弱位使用经过音、辅助音、倚音制造紧张，再在强位回归和弦音释放。",
        "example": "句中先触及9度张力音，句尾回到3度稳定落点。",
        "keywords": ["non-chord tone", "tension", "release", "melody"],
    },
    {
        "name": "Pentatonic Skeleton",
        "category": "pitch_material",
        "description": "先用五声音阶搭建骨架可降低冲突概率，再局部补充导音与色彩音。",
        "example": "先写1-2-3-5-6骨架，再加4或7制造方向性。",
        "keywords": ["pentatonic", "melody", "songwriting"],
    },
    {
        "name": "Question Hook Answer Hook",
        "category": "hook",
        "description": "hook内部也可采用问答分句，前半句制造悬念，后半句给出明确落点。",
        "example": "前2拍停在2级，后2拍回到1级并重复节奏。",
        "keywords": ["hook", "question answer", "melody"],
    },
    {
        "name": "Contour Contrast Repetition",
        "category": "contour",
        "description": "保持同一节奏而切换轮廓方向（如上行改下行），可在重复中保留辨识度。",
        "example": "第二遍保持节奏不变，但把拱形改为下行收束。",
        "keywords": ["contour", "ascending", "descending", "melody writing"],
    },
]


VOICE_QUERIES = [
    "voice leading rules avoid parallel fifths octaves",
    "SATB part writing spacing voice crossing doubling rules",
    "leading tone and chordal seventh resolution rules",
    "cadential 6/4 and suspension resolution voice leading",
    "common practice harmony voice leading guidelines",
]

ARRANGEMENT_QUERIES = [
    "music arrangement techniques layering contrast transitions",
    "orchestration tips register spacing doubling",
    "production arrangement ideas pop",
    "production arrangement ideas edm",
    "production arrangement ideas hip hop",
    "song arrangement pre chorus build drop techniques",
]

MELODY_QUERIES = [
    "melody writing techniques for songs",
    "songwriting melody tips hook contour rhythm",
    "melodic development methods sequence fragmentation inversion",
    "how to write memorable melody with chord tones",
    "prosody lyric stress melody writing",
]


def build_voice_records(brave_results: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in VOICE_LEADING_HARDCODED:
        rows.append({**item, "source": f"{SOURCE_PREFIX}:hardcoded"})

    for template in VOICE_LEADING_BRAVE_TEMPLATES:
        best = pick_best_result(brave_results, template["keywords"])
        rows.append(
            {
                "name": template["name"],
                "rule_text": enrich_description(template["rule_text"], best),
                "category": template["category"],
                "priority": template["priority"],
                "source": result_source(best, "voice_template"),
            }
        )
    return dedupe_by_name(rows)


def build_arrangement_records(brave_results: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in ARRANGEMENT_HARDCODED:
        rows.append({**item, "source": f"{SOURCE_PREFIX}:hardcoded"})

    for template in ARRANGEMENT_BRAVE_TEMPLATES:
        best = pick_best_result(brave_results, template["keywords"])
        rows.append(
            {
                "name": template["name"],
                "style": template["style"],
                "category": template["category"],
                "description": enrich_description(template["description"], best),
                "example": template["example"],
                "source": result_source(best, "arrangement_template"),
            }
        )
    return dedupe_by_name(rows)


def build_melody_records(brave_results: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in MELODY_HARDCODED:
        rows.append({**item, "source": f"{SOURCE_PREFIX}:hardcoded"})

    for template in MELODY_BRAVE_TEMPLATES:
        best = pick_best_result(brave_results, template["keywords"])
        rows.append(
            {
                "name": template["name"],
                "category": template["category"],
                "description": enrich_description(template["description"], best),
                "example": template["example"],
                "source": result_source(best, "melody_template"),
            }
        )
    return dedupe_by_name(rows)


def insert_search_log(
    conn: sqlite3.Connection,
    worker: str,
    query_results_map: dict[str, list[dict[str, str]]],
) -> None:
    payload: list[tuple[str, int, str, str]] = []
    for query, results in query_results_map.items():
        urls = ",".join(r.get("url", "") for r in results[:5] if r.get("url"))
        payload.append((query, len(results), urls, worker))
    conn.executemany(
        """
        INSERT INTO search_log (query, result_count, source_urls, worker)
        VALUES (?, ?, ?, ?)
        """,
        payload,
    )


def run_brave_queries(queries: list[str], count: int = 10) -> tuple[list[dict[str, str]], dict[str, list[dict[str, str]]]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    batched = batch_search(queries, count=count, delay=0.08)
    for query in queries:
        grouped[query] = [r for r in batched if r.get("query") == query]

    # Add one focused query using the single search API to satisfy both interfaces.
    focused_query = f"{queries[0]} best practices"
    focused_results = search(focused_query, count=8)
    grouped[focused_query] = focused_results

    merged: list[dict[str, str]] = batched + focused_results
    # Basic URL dedupe to reduce repeated snippets.
    seen_urls: set[str] = set()
    unique: list[dict[str, str]] = []
    for r in merged:
        url = r.get("url", "")
        if url and url in seen_urls:
            continue
        if url:
            seen_urls.add(url)
        unique.append(r)
    return unique, grouped


def main() -> None:
    init_db(DB_PATH)

    print("Running Brave searches...")
    voice_results, voice_grouped = run_brave_queries(VOICE_QUERIES, count=10)
    arrangement_results, arrangement_grouped = run_brave_queries(ARRANGEMENT_QUERIES, count=10)
    melody_results, melody_grouped = run_brave_queries(MELODY_QUERIES, count=10)

    voice_rows = build_voice_records(voice_results)
    arrangement_rows = build_arrangement_records(arrangement_results)
    melody_rows = build_melody_records(melody_results)

    if len(voice_rows) < 15:
        raise RuntimeError(f"voice_leading_rules insufficient rows: {len(voice_rows)}")
    if len(arrangement_rows) < 25:
        raise RuntimeError(f"arrangement_techniques insufficient rows: {len(arrangement_rows)}")
    if len(melody_rows) < 20:
        raise RuntimeError(f"melody_techniques insufficient rows: {len(melody_rows)}")

    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    for table in ("voice_leading_rules", "arrangement_techniques", "melody_techniques"):
        c.execute(f"DELETE FROM {table} WHERE source LIKE ?", (f"{SOURCE_PREFIX}:%",))

    c.executemany(
        """
        INSERT INTO voice_leading_rules (name, rule_text, category, priority, source)
        VALUES (:name, :rule_text, :category, :priority, :source)
        """,
        voice_rows,
    )
    c.executemany(
        """
        INSERT INTO arrangement_techniques (name, style, category, description, example, source)
        VALUES (:name, :style, :category, :description, :example, :source)
        """,
        arrangement_rows,
    )
    c.executemany(
        """
        INSERT INTO melody_techniques (name, category, description, example, source)
        VALUES (:name, :category, :description, :example, :source)
        """,
        melody_rows,
    )

    insert_search_log(conn, "codex-4", voice_grouped)
    insert_search_log(conn, "codex-4", arrangement_grouped)
    insert_search_log(conn, "codex-4", melody_grouped)

    conn.commit()

    print("Inserted rows:")
    print(f"  voice_leading_rules: {len(voice_rows)}")
    print(f"  arrangement_techniques: {len(arrangement_rows)}")
    print(f"  melody_techniques: {len(melody_rows)}")

    print("Current table counts:")
    for table in ("voice_leading_rules", "arrangement_techniques", "melody_techniques"):
        total = c.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        mine = c.execute(
            f"SELECT COUNT(*) FROM {table} WHERE source LIKE ?",
            (f"{SOURCE_PREFIX}:%",),
        ).fetchone()[0]
        print(f"  {table}: total={total}, {SOURCE_PREFIX}={mine}")

    conn.close()


if __name__ == "__main__":
    main()
