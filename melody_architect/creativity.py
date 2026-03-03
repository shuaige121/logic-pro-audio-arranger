"""Creativity level system for arrangement generation.

Three levels control the balance between deterministic music theory rules (Python)
and LLM creative freedom:

- conservative: Python generates ~90% of decisions. LLM only picks from pre-made options.
- balanced: Python handles structure/theory (~60%), LLM adds creative touches (~40%).
- creative: LLM has maximum freedom (~70%), but must respect user constraints and basic theory.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from typing import Literal


DecisionMode = Literal["fixed", "choose_from_list", "free"]
VoiceLeadingMode = Literal["strict", "relaxed", "free"]

DEFAULT_CHORD_OPTIONS = ("I-V-vi-IV", "I-vi-IV-V", "vi-IV-I-V")
_CHOICE_LETTERS = tuple("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
_ROMAN_TOKEN_PATTERN = re.compile(r"^(?:b|#)?[ivIV]+(?:°|dim|aug|sus2|sus4|add9|6|7|9|11|13|maj7|m7)?$")
_CHORD_NAME_PATTERN = re.compile(r"^[A-G](?:#|b)?(?:m|maj|min|dim|aug|sus2|sus4|add9|6|7|9|11|13|maj7|m7)?$")


class CreativityLevel(Enum):
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    CREATIVE = "creative"


@dataclass(frozen=True)
class CreativityConfig:
    """Configuration for a creativity level."""

    level: CreativityLevel

    # What Python controls (deterministic)
    chord_selection: DecisionMode
    rhythm_pattern: DecisionMode
    bass_pattern: DecisionMode
    instrumentation: DecisionMode
    section_structure: DecisionMode
    voice_leading: VoiceLeadingMode

    # What LLM can decide
    llm_can_add_instruments: bool
    llm_can_modify_rhythm: bool
    llm_can_reharmonize: bool
    llm_can_change_structure: bool
    llm_can_add_effects: bool

    # Constraints LLM must always respect
    must_respect_key: bool = True
    must_respect_tempo: bool = True
    must_respect_time_signature: bool = True
    must_follow_voice_leading: bool = True  # only False for creative


CREATIVITY_CONFIGS = {
    CreativityLevel.CONSERVATIVE: CreativityConfig(
        level=CreativityLevel.CONSERVATIVE,
        chord_selection="choose_from_list",  # Python提供选项，LLM选一个
        rhythm_pattern="fixed",  # Python直接生成
        bass_pattern="fixed",  # Python直接生成
        instrumentation="fixed",  # 风格决定乐器
        section_structure="fixed",  # Python按bar数自动分段
        voice_leading="strict",  # 严格遵循规则
        llm_can_add_instruments=False,
        llm_can_modify_rhythm=False,
        llm_can_reharmonize=False,
        llm_can_change_structure=False,
        llm_can_add_effects=False,
    ),
    CreativityLevel.BALANCED: CreativityConfig(
        level=CreativityLevel.BALANCED,
        chord_selection="choose_from_list",
        rhythm_pattern="choose_from_list",
        bass_pattern="choose_from_list",
        instrumentation="choose_from_list",
        section_structure="choose_from_list",
        voice_leading="relaxed",
        llm_can_add_instruments=True,
        llm_can_modify_rhythm=True,
        llm_can_reharmonize=False,
        llm_can_change_structure=False,
        llm_can_add_effects=True,
    ),
    CreativityLevel.CREATIVE: CreativityConfig(
        level=CreativityLevel.CREATIVE,
        chord_selection="free",
        rhythm_pattern="free",
        bass_pattern="free",
        instrumentation="free",
        section_structure="choose_from_list",
        voice_leading="relaxed",
        llm_can_add_instruments=True,
        llm_can_modify_rhythm=True,
        llm_can_reharmonize=True,
        llm_can_change_structure=True,
        llm_can_add_effects=True,
        must_follow_voice_leading=False,
    ),
}


def get_config(level: str | CreativityLevel) -> CreativityConfig:
    """Return config by creativity level."""

    if isinstance(level, CreativityLevel):
        resolved = level
    elif isinstance(level, str):
        normalized = level.strip().lower()
        try:
            resolved = CreativityLevel(normalized)
        except ValueError as exc:
            allowed = ", ".join(item.value for item in CreativityLevel)
            raise ValueError(f"Unknown creativity level: {level!r}. Expected one of: {allowed}.") from exc
    else:
        raise TypeError(f"level must be str or CreativityLevel, got {type(level).__name__}")

    return CREATIVITY_CONFIGS[resolved]


def build_llm_prompt(config: CreativityConfig, context: dict) -> str:
    """Build level-specific prompt for LLM arrangement decisions."""

    options_raw = context.get("chord_options", DEFAULT_CHORD_OPTIONS)
    options = [str(item).strip() for item in options_raw if str(item).strip()]
    if not options:
        options = list(DEFAULT_CHORD_OPTIONS)

    if config.level is CreativityLevel.CONSERVATIVE:
        formatted = " ".join(
            f"[{_CHOICE_LETTERS[idx]}] {option}" for idx, option in enumerate(options[: len(_CHOICE_LETTERS)])
        )
        return f"Choose the best option from the following list: {formatted}. Answer with just the letter."

    if config.level is CreativityLevel.BALANCED:
        key = context.get("key", "C")
        mode = context.get("mode", "major")
        return (
            f"Given these chord progression options [{', '.join(options)}], "
            f"you may choose one or suggest a variation. Stay within {key} {mode}."
        )

    style = context.get("style", "pop")
    key = context.get("key", "C")
    bpm = context.get("bpm", 120)
    return (
        f"Create an arrangement for this melody in {style} style. "
        f"You must use key={key}, tempo={bpm}. "
        "Be creative with harmony and instrumentation."
    )


def filter_llm_output(config: CreativityConfig, output: dict, constraints: dict) -> dict:
    """Validate and filter LLM output against creativity-level constraints."""

    filtered = dict(output)
    violations: list[str] = []

    _enforce_hard_constraints(config, filtered, constraints, violations)

    if config.level is CreativityLevel.CONSERVATIVE:
        _validate_conservative_choice(filtered, constraints, violations)
    elif config.level is CreativityLevel.BALANCED:
        _validate_balanced_theory(filtered, violations)
    elif config.level is CreativityLevel.CREATIVE:
        # Creative mode only enforces hard user constraints.
        pass

    return {
        "accepted": len(violations) == 0,
        "level": config.level.value,
        "output": filtered,
        "violations": violations,
    }


def _enforce_hard_constraints(
    config: CreativityConfig,
    filtered: dict,
    constraints: dict,
    violations: list[str],
) -> None:
    checks = (
        ("key", config.must_respect_key),
        ("tempo", config.must_respect_tempo),
        ("time_signature", config.must_respect_time_signature),
    )
    for field, should_enforce in checks:
        if not should_enforce:
            continue
        if field not in constraints:
            continue
        expected = constraints[field]
        actual = filtered.get(field)
        if actual is None:
            filtered[field] = expected
            violations.append(f"Missing required field '{field}'. Restored to {expected!r}.")
            continue
        if actual != expected:
            filtered[field] = expected
            violations.append(f"Field '{field}' changed ({actual!r} -> {expected!r}); reverted.")


def _validate_conservative_choice(filtered: dict, constraints: dict, violations: list[str]) -> None:
    allowed_raw = constraints.get("allowed_options", DEFAULT_CHORD_OPTIONS)
    allowed = [str(item).strip() for item in allowed_raw if str(item).strip()]
    if not allowed:
        allowed = list(DEFAULT_CHORD_OPTIONS)

    allowed_by_letter = {letter: option for letter, option in zip(_CHOICE_LETTERS, allowed)}
    selected_value = filtered.get("choice") or filtered.get("answer") or filtered.get("selection")

    if selected_value is None and "chord_progression" in filtered:
        selected_value = filtered["chord_progression"]

    if selected_value is None:
        default_letter = next(iter(allowed_by_letter), "A")
        filtered["choice"] = default_letter
        filtered["chord_progression"] = allowed_by_letter.get(default_letter, allowed[0])
        violations.append("No choice found; defaulted to first allowed option.")
        return

    selected_text = str(selected_value).strip()
    normalized = selected_text.upper()
    if normalized in allowed_by_letter:
        filtered["choice"] = normalized
        filtered["chord_progression"] = allowed_by_letter[normalized]
        return
    if selected_text in allowed:
        filtered["chord_progression"] = selected_text
        idx = allowed.index(selected_text)
        filtered["choice"] = _CHOICE_LETTERS[idx]
        return

    default_letter = next(iter(allowed_by_letter), "A")
    filtered["choice"] = default_letter
    filtered["chord_progression"] = allowed_by_letter.get(default_letter, allowed[0])
    violations.append(f"Choice {selected_text!r} is not in allowed options {list(allowed_by_letter)}.")


def _validate_balanced_theory(filtered: dict, violations: list[str]) -> None:
    tokens = _extract_progression_tokens(filtered)
    if not tokens:
        return

    if len(tokens) < 2:
        violations.append("Balanced mode expects at least 2 chords in a progression.")

    roman_like = all(_ROMAN_TOKEN_PATTERN.match(token) for token in tokens)
    chord_like = all(_CHORD_NAME_PATTERN.match(token) for token in tokens)
    if not (roman_like or chord_like):
        violations.append("Progression contains unsupported chord token format for balanced mode.")
        return

    if roman_like and not any(token.lower().startswith("i") for token in tokens):
        violations.append("Balanced mode progression should include tonic function (I/i).")


def _extract_progression_tokens(payload: dict) -> list[str]:
    for key in ("chord_progression", "progression", "chords"):
        value = payload.get(key)
        if value is None:
            continue
        if isinstance(value, (list, tuple)):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return []
            if "-" in text:
                return [part.strip() for part in text.split("-") if part.strip()]
            if "," in text:
                return [part.strip() for part in text.split(",") if part.strip()]
            return [part.strip() for part in text.split() if part.strip()]
    return []


__all__ = [
    "CreativityLevel",
    "CreativityConfig",
    "CREATIVITY_CONFIGS",
    "get_config",
    "build_llm_prompt",
    "filter_llm_output",
]
