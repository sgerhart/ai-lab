"""AISVS Level 1 Chapter C2 input validation and steering defenses (IWO-086).

Implements controls for:
- 2.1.1: Input normalization before tokenization (Unicode NFKC)
- 2.1.2: Encoding smuggling and zero-width / bidi control character detection
- 2.1.3: Screening untrusted steering input (prompts, tool results, retrieved text)
- 2.1.4: Strict length bounding (reject over-long, do not truncate)
- 2.1.5: Character boundary verification and disallowed control character blocking
- 2.2.1: Deterministic harmful content and prompt injection risk scoring
- 2.2.2: Multi-lingual input support and cross-script homoglyph detection
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .events import SecurityEvent

# Length limits (AISVS 2.1.4): Reject, never truncate
MAX_USER_PROMPT_LENGTH: int = 32_000
MAX_TOOL_RESULT_LENGTH: int = 64_000
HARMFUL_RISK_THRESHOLD: float = 0.70

# Smuggling code points (AISVS 2.1.2): zero-width, invisible separators, directional overrides
_ZERO_WIDTH_AND_INVISIBLE: frozenset[int] = frozenset(
    {
        0x200B,  # Zero-width space
        0x200C,  # Zero-width non-joiner
        0x200D,  # Zero-width joiner (when outside standard emoji modifier sequences)
        0x200E,  # Left-to-right mark
        0x200F,  # Right-to-left mark
        0x2060,  # Word joiner
        0xFEFF,  # Zero-width no-break space / BOM
    }
)

_BIDI_CONTROLS: frozenset[int] = frozenset(
    {
        0x202A,  # Left-to-Right Embedding (LRE)
        0x202B,  # Right-to-Left Embedding (RLE)
        0x202C,  # Pop Directional Formatting (PDF)
        0x202D,  # Left-to-Right Override (LRO)
        0x202E,  # Right-to-Left Override (RLO)
        0x2066,  # Left-to-Right Isolate (LRI)
        0x2067,  # Right-to-Left Isolate (RLI)
        0x2068,  # First Strong Isolate (FSI)
        0x2069,  # Pop Directional Isolate (PDI)
    }
)

# Control characters disallowed in input (AISVS 2.1.5): null bytes, raw terminal escapes, non-whitespace C0/C1
_DISALLOWED_CONTROL_CHARS: frozenset[int] = frozenset(
    set(range(0x00, 0x09))  # \x00 through \x08 (including null byte)
    | {0x0B, 0x0C}          # vertical tab, form feed
    | set(range(0x0E, 0x20))  # \x0e through \x1f (including \x1b ESC)
    | {0x7F}                # DEL
)

# English and Multilingual Injection / System Override Patterns (AISVS 2.1.3 & 2.2.2)
_INJECTION_PATTERNS: tuple[tuple[str, re.Pattern[str], float], ...] = (
    # Direct instruction ignore
    (
        "ignore_previous_instructions",
        re.compile(
            r"(ignore|disregard|forget|bypass|override)\s+(all\s+)?(previous|prior|above|system)\s+(instructions|directives|prompts|rules)",
            re.IGNORECASE,
        ),
        0.85,
    ),
    # System roleplay hijacking
    (
        "system_role_hijack",
        re.compile(
            r"(you\s+are\s+now|act\s+as|pretend\s+to\s+be)\s+(in\s+developer\s+mode|dan|an\s+unrestricted\s+ai|jailbroken|god\s+mode)",
            re.IGNORECASE,
        ),
        0.80,
    ),
    # Chat template delimiter smuggling
    (
        "template_delimiter_smuggling",
        re.compile(
            r"(<\|im_start\|>|<\|im_end\|>|\[INST\]|\[/INST\]|<<SYS>>|<</SYS>>|<\|system\|>|<\|user\|>)",
            re.IGNORECASE,
        ),
        0.90,
    ),
    # System prompt extraction / secret probing
    (
        "system_prompt_exfiltration",
        re.compile(
            r"(output|print|reveal|repeat|echo|display)\s+(your\s+)?(full\s+)?(system\s+prompt|initial\s+instructions|master\s+prompt|secret\s+key|env\s+vars)",
            re.IGNORECASE,
        ),
        0.75,
    ),
    # Host command / shell escape injection
    (
        "shell_command_escape",
        re.compile(
            r"(\b(curl|wget|bash|sh|nc|ncat|netcat)\b.*(http|\||;\s*rm\b|\/etc\/(passwd|shadow)))",
            re.IGNORECASE,
        ),
        0.85,
    ),
    # Multi-lingual injections (AISVS 2.2.2)
    (
        "multilingual_injection_es",
        re.compile(
            r"(ignora|olvida|descarta)\s+(todas\s+las\s+)?(instrucciones|reglas)\s+(anteriores|previas)",
            re.IGNORECASE,
        ),
        0.85,
    ),
    (
        "multilingual_injection_de",
        re.compile(
            r"(ignoriere|vergiss)\s+(alle\s+)?(vorherigen|bisherigen)\s+(anweisungen|regeln)",
            re.IGNORECASE,
        ),
        0.85,
    ),
    (
        "multilingual_injection_fr",
        re.compile(
            r"(ignore|ignorez|oublie|oubliez)\s+(toutes\s+les\s+)?(instructions|directives)\s+(précédentes|anterieures)",
            re.IGNORECASE,
        ),
        0.85,
    ),
    (
        "multilingual_injection_zh",
        re.compile(
            r"(忽略|忘记|跳过)(所有)?(先前|之前)的(指示|命令|规则|提示)",
            re.IGNORECASE,
        ),
        0.85,
    ),
    (
        "multilingual_injection_ru",
        re.compile(
            r"(забудь|игнорируй|отмени)\s+(все\s+)?(предыдущие|прошлые)\s+(инструкции|команды)",
            re.IGNORECASE,
        ),
        0.85,
    ),
)


@dataclass(frozen=True)
class HarmfulContentScore:
    """Detailed risk scoring for user prompts and tool outputs (AISVS 2.2.1)."""

    risk_score: float
    is_blocked: bool
    flags: tuple[str, ...]
    category_scores: dict[str, float]
    language_notes: str


@dataclass(frozen=True)
class ValidationResult:
    """Result of AISVS Level 1 input validation."""

    valid: bool
    normalized_text: str
    error_message: str | None = None
    violation_id: str | None = None
    harmful_score: HarmfulContentScore | None = None
    security_event: SecurityEvent | None = None


def normalize_input(text: str) -> str:
    """Normalizes input before tokenization via Unicode NFKC (AISVS 2.1.1).

    Converts compatibility characters to canonical equivalents and normalizes line endings.
    """
    if not text:
        return ""
    # Standardize line endings
    standardized = text.replace("\r\n", "\n").replace("\r", "\n")
    # Unicode NFKC normalization
    normalized = unicodedata.normalize("NFKC", standardized)
    # Strip any dangling leading BOM
    if normalized.startswith("\ufeff"):
        normalized = normalized[1:]
    return normalized


def detect_encoding_smuggling(text: str) -> tuple[bool, str, list[str]]:
    """Detects encoding smuggling, zero-width characters, and bidi overrides (AISVS 2.1.2)."""
    detected_smuggling: list[str] = []

    for char in text:
        cp = ord(char)
        if cp in _ZERO_WIDTH_AND_INVISIBLE:
            detected_smuggling.append(f"U+{cp:04X} (zero-width/invisible)")
        elif cp in _BIDI_CONTROLS:
            detected_smuggling.append(f"U+{cp:04X} (directional-override)")

    if detected_smuggling:
        summary = f"Detected {len(detected_smuggling)} smuggling characters: {', '.join(sorted(set(detected_smuggling))[:5])}"
        return True, summary, detected_smuggling

    return False, "", []


def check_character_bounds(text: str) -> tuple[bool, str]:
    """Ensures input respects character boundaries and contains no disallowed controls (AISVS 2.1.5)."""
    for idx, char in enumerate(text):
        cp = ord(char)
        if cp in _DISALLOWED_CONTROL_CHARS:
            if cp == 0:
                return False, f"Disallowed character null byte (U+0000) at position {idx}"
            if cp == 0x1B:
                return False, f"Disallowed character raw ANSI escape (U+001B) at position {idx}"
            return False, f"Disallowed control character (U+{cp:04X}) at position {idx}"

    return True, ""


def check_length_bounds(
    text: str, max_length: int = MAX_USER_PROMPT_LENGTH
) -> tuple[bool, str]:
    """Enforces strict length boundary (AISVS 2.1.4: Reject over-long input, do not truncate)."""
    length = len(text)
    if length > max_length:
        return (
            False,
            f"Input length {length} exceeds maximum limit of {max_length} characters (AISVS 2.1.4: over-long input rejected, not truncated)",
        )
    return True, ""


def detect_homoglyph_script_mixing(text: str) -> tuple[bool, str]:
    """Detects cross-alphabet homoglyph mixing within alphanumeric words (AISVS 2.2.2)."""
    words = re.findall(r"\b\w+\b", text)
    mixed_words: list[str] = []

    for word in words:
        scripts: set[str] = set()
        for char in word:
            if not char.isalpha():
                continue
            name = unicodedata.name(char, "")
            if "LATIN" in name:
                scripts.add("LATIN")
            elif "CYRILLIC" in name:
                scripts.add("CYRILLIC")
            elif "GREEK" in name:
                scripts.add("GREEK")

        # Flag if Latin is mixed with Cyrillic or Greek in a single word
        if len(scripts) > 1 and "LATIN" in scripts:
            mixed_words.append(word)

    if mixed_words:
        return True, f"Suspicious cross-script homoglyph mixing detected in words: {', '.join(mixed_words[:3])}"

    return False, ""


def score_harmful_content(
    text: str,
    *,
    is_tool_output: bool = False,
    smuggling_detected: bool = False,
) -> HarmfulContentScore:
    """Scores input prompts or untrusted tool steering results for harmful content (AISVS 2.2.1, 2.2.2)."""
    category_scores: dict[str, float] = {
        "prompt_injection": 0.0,
        "template_smuggling": 0.0,
        "shell_escape": 0.0,
        "exfiltration": 0.0,
        "encoding_smuggling": 1.0 if smuggling_detected else 0.0,
        "homoglyph_obfuscation": 0.0,
    }
    flags: list[str] = []

    # Check homoglyph mixing
    is_mixed, mix_reason = detect_homoglyph_script_mixing(text)
    if is_mixed:
        category_scores["homoglyph_obfuscation"] = 0.75
        flags.append(mix_reason)

    if smuggling_detected:
        flags.append("Encoding smuggling characters present")

    # Match injection patterns
    for tag, pattern, weight in _INJECTION_PATTERNS:
        if pattern.search(text):
            flags.append(f"pattern_matched:{tag}")
            if "template" in tag:
                category_scores["template_smuggling"] = max(category_scores["template_smuggling"], weight)
            elif "shell" in tag:
                category_scores["shell_escape"] = max(category_scores["shell_escape"], weight)
            elif "exfiltration" in tag:
                category_scores["exfiltration"] = max(category_scores["exfiltration"], weight)
            else:
                category_scores["prompt_injection"] = max(category_scores["prompt_injection"], weight)

    # Compute overall risk score (maximum of category scores)
    max_risk = max(category_scores.values()) if category_scores else 0.0

    # If untrusted tool output attempts to inject steering directives (AISVS 2.1.3)
    if is_tool_output and max_risk >= 0.70:
        flags.append("untrusted_tool_steering_injection")

    is_blocked = max_risk >= HARMFUL_RISK_THRESHOLD

    lang_notes = (
        "Checked multi-lingual patterns (EN, ES, DE, FR, ZH, RU) and cross-script homoglyphs per AISVS 2.2.2"
    )

    return HarmfulContentScore(
        risk_score=round(max_risk, 3),
        is_blocked=is_blocked,
        flags=tuple(flags),
        category_scores=category_scores,
        language_notes=lang_notes,
    )


def validate_input(
    raw_text: str,
    *,
    is_tool_output: bool = False,
    agent_id: str = "studio",
    conversation_id: str = "",
    run_id: str = "",
) -> ValidationResult:
    """Executes the complete AISVS Level 1 input validation pipeline (AISVS 2.1.1 - 2.2.2).

    Pipeline:
    1. Length boundary check (rejects over-long input without truncating) - AISVS 2.1.4
    2. Character bound check (rejects null bytes and illegal control codes) - AISVS 2.1.5
    3. Encoding smuggling check (zero-width, bidi overrides) - AISVS 2.1.2
    4. Unicode NFKC normalization - AISVS 2.1.1
    5. Harmful content & prompt injection scoring - AISVS 2.1.3, 2.2.1, 2.2.2
    6. Security event emission upon violation
    """
    max_len = MAX_TOOL_RESULT_LENGTH if is_tool_output else MAX_USER_PROMPT_LENGTH

    # 1. Length Boundary (AISVS 2.1.4)
    len_ok, len_msg = check_length_bounds(raw_text, max_length=max_len)
    if not len_ok:
        event = SecurityEvent.create(
            provider="platform",
            severity="medium",
            classification="policy",
            summary=f"Input rejected: {len_msg}",
            agent_id=agent_id,
            resource_id=conversation_id or "input_gate",
            run_id=run_id,
            details={"violation": "2.1.4", "raw_length": len(raw_text), "max_allowed": max_len},
        )
        return ValidationResult(
            valid=False,
            normalized_text="",
            error_message=len_msg,
            violation_id="2.1.4",
            security_event=event,
        )

    # 2. Character Boundary & Controls (AISVS 2.1.5)
    char_ok, char_msg = check_character_bounds(raw_text)
    if not char_ok:
        event = SecurityEvent.create(
            provider="platform",
            severity="high",
            classification="finding",
            summary=f"Input rejected: {char_msg}",
            agent_id=agent_id,
            resource_id=conversation_id or "input_gate",
            run_id=run_id,
            details={"violation": "2.1.5", "error": char_msg},
        )
        return ValidationResult(
            valid=False,
            normalized_text="",
            error_message=char_msg,
            violation_id="2.1.5",
            security_event=event,
        )

    # 3. Encoding Smuggling (AISVS 2.1.2)
    smuggling_detected, smuggle_msg, smuggle_chars = detect_encoding_smuggling(raw_text)
    if smuggling_detected:
        event = SecurityEvent.create(
            provider="platform",
            severity="high",
            classification="finding",
            summary=f"Input rejected: {smuggle_msg}",
            agent_id=agent_id,
            resource_id=conversation_id or "input_gate",
            run_id=run_id,
            details={"violation": "2.1.2", "smuggle_details": smuggle_chars[:10]},
        )
        return ValidationResult(
            valid=False,
            normalized_text="",
            error_message=f"Input rejected: encoding smuggling detected (AISVS 2.1.2). {smuggle_msg}",
            violation_id="2.1.2",
            security_event=event,
        )

    # 4. Unicode Normalization (AISVS 2.1.1)
    normalized = normalize_input(raw_text)

    # 5. Harmful Content and Injection Scoring (AISVS 2.1.3, 2.2.1, 2.2.2)
    score = score_harmful_content(
        normalized,
        is_tool_output=is_tool_output,
        smuggling_detected=False,
    )

    if score.is_blocked:
        err_msg = (
            f"Input blocked by AISVS prompt defense (risk score {score.risk_score:.2f} >= {HARMFUL_RISK_THRESHOLD:.2f}). "
            f"Flags: {', '.join(score.flags)}"
        )
        event = SecurityEvent.create(
            provider="platform",
            severity="critical" if score.risk_score >= 0.85 else "high",
            classification="finding",
            summary=err_msg[:200],
            agent_id=agent_id,
            resource_id=conversation_id or "input_gate",
            run_id=run_id,
            details={
                "violation": "2.1.3/2.2.1",
                "risk_score": score.risk_score,
                "flags": list(score.flags),
                "is_tool_output": is_tool_output,
            },
        )
        return ValidationResult(
            valid=False,
            normalized_text=normalized,
            error_message=err_msg,
            violation_id="2.1.3",
            harmful_score=score,
            security_event=event,
        )

    return ValidationResult(
        valid=True,
        normalized_text=normalized,
        error_message=None,
        violation_id=None,
        harmful_score=score,
        security_event=None,
    )

