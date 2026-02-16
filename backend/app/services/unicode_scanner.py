"""Core Unicode scanning and cleaning logic for Ghosted.

Detects invisible Unicode characters that AI detectors may flag,
and provides cleaning (removal) with detailed reporting.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Invisible characters grouped by category.
# threat_level is assigned based on experiment data; defaults are initial estimates.
INVISIBLE_CHARS: dict[str, tuple[str, str, str]] = {
    # char -> (name, category, default_threat_level)
    # Zero-width characters (most suspicious to detectors)
    "\u200B": ("ZERO WIDTH SPACE", "zero-width", "high"),
    "\u200C": ("ZERO WIDTH NON-JOINER", "zero-width", "high"),
    "\u200D": ("ZERO WIDTH JOINER", "zero-width", "high"),
    "\u2060": ("WORD JOINER", "zero-width", "high"),
    "\uFEFF": ("ZERO WIDTH NO-BREAK SPACE / BOM", "zero-width", "high"),
    # Bidirectional marks
    "\u200E": ("LEFT-TO-RIGHT MARK", "bidi", "medium"),
    "\u200F": ("RIGHT-TO-LEFT MARK", "bidi", "medium"),
    "\u202A": ("LEFT-TO-RIGHT EMBEDDING", "bidi", "medium"),
    "\u202B": ("RIGHT-TO-LEFT EMBEDDING", "bidi", "medium"),
    "\u202C": ("POP DIRECTIONAL FORMATTING", "bidi", "medium"),
    "\u202D": ("LEFT-TO-RIGHT OVERRIDE", "bidi", "medium"),
    "\u202E": ("RIGHT-TO-LEFT OVERRIDE", "bidi", "medium"),
    "\u2066": ("LEFT-TO-RIGHT ISOLATE", "bidi", "medium"),
    "\u2067": ("RIGHT-TO-LEFT ISOLATE", "bidi", "medium"),
    "\u2068": ("FIRST STRONG ISOLATE", "bidi", "medium"),
    "\u2069": ("POP DIRECTIONAL ISOLATE", "bidi", "medium"),
    "\u061C": ("ARABIC LETTER MARK", "bidi", "medium"),
    # Unusual whitespace
    "\u00AD": ("SOFT HYPHEN", "whitespace", "low"),
    "\u180E": ("MONGOLIAN VOWEL SEPARATOR", "whitespace", "medium"),
    "\u2000": ("EN QUAD", "whitespace", "low"),
    "\u2001": ("EM QUAD", "whitespace", "low"),
    "\u2002": ("EN SPACE", "whitespace", "low"),
    "\u2003": ("EM SPACE", "whitespace", "low"),
    "\u2004": ("THREE-PER-EM SPACE", "whitespace", "low"),
    "\u2005": ("FOUR-PER-EM SPACE", "whitespace", "low"),
    "\u2006": ("SIX-PER-EM SPACE", "whitespace", "low"),
    "\u2007": ("FIGURE SPACE", "whitespace", "low"),
    "\u2008": ("PUNCTUATION SPACE", "whitespace", "low"),
    "\u2009": ("THIN SPACE", "whitespace", "low"),
    "\u200A": ("HAIR SPACE", "whitespace", "low"),
    "\u202F": ("NARROW NO-BREAK SPACE", "whitespace", "low"),
    # Deprecated formatting
    "\u206A": ("INHIBIT SYMMETRIC SWAPPING", "deprecated", "low"),
    "\u206B": ("ACTIVATE SYMMETRIC SWAPPING", "deprecated", "low"),
    "\u206C": ("INHIBIT ARABIC FORM SHAPING", "deprecated", "low"),
    "\u206D": ("ACTIVATE ARABIC FORM SHAPING", "deprecated", "low"),
    "\u206E": ("NATIONAL DIGIT SHAPES", "deprecated", "low"),
    "\u206F": ("NOMINAL DIGIT SHAPES", "deprecated", "low"),
    # Invisible math operators
    "\u2061": ("FUNCTION APPLICATION", "invisible-math", "low"),
    "\u2062": ("INVISIBLE TIMES", "invisible-math", "low"),
    "\u2063": ("INVISIBLE SEPARATOR", "invisible-math", "low"),
    "\u2064": ("INVISIBLE PLUS", "invisible-math", "low"),
    # Annotation characters
    "\uFFF9": ("INTERLINEAR ANNOTATION ANCHOR", "annotation", "low"),
    "\uFFFA": ("INTERLINEAR ANNOTATION SEPARATOR", "annotation", "low"),
    "\uFFFB": ("INTERLINEAR ANNOTATION TERMINATOR", "annotation", "low"),
    # Hangul fillers
    "\u115F": ("HANGUL CHOSEONG FILLER", "formatting", "low"),
    "\u1160": ("HANGUL JUNGSEONG FILLER", "formatting", "low"),
    # Khmer vowels
    "\u17B4": ("KHMER VOWEL INHERENT AQ", "formatting", "low"),
    "\u17B5": ("KHMER VOWEL INHERENT AA", "formatting", "low"),
    # Combining grapheme joiner
    "\u034F": ("COMBINING GRAPHEME JOINER", "formatting", "low"),
}

# Smart characters that aren't invisible but are AI tells (em-dashes, smart quotes).
SMART_CHARS: dict[str, tuple[str, str]] = {
    # char -> (ascii_replacement, name)
    "\u2018": ("'", "LEFT SINGLE QUOTATION MARK"),
    "\u2019": ("'", "RIGHT SINGLE QUOTATION MARK"),
    "\u201C": ('"', "LEFT DOUBLE QUOTATION MARK"),
    "\u201D": ('"', "RIGHT DOUBLE QUOTATION MARK"),
    "\u2013": ("-", "EN DASH"),
    "\u2014": ("--", "EM DASH"),
    "\u2026": ("...", "HORIZONTAL ELLIPSIS"),
}

# Build a fast lookup set for scanning
_INVISIBLE_SET = set(INVISIBLE_CHARS.keys())


@dataclass
class CharFinding:
    char: str  # The Unicode escape, e.g. "\\u200B"
    name: str
    category: str
    threat_level: str  # "high", "medium", "low"
    count: int
    positions: list[int] = field(default_factory=list)


@dataclass
class SmartCharFinding:
    char: str
    name: str
    count: int
    replacement: str


@dataclass
class ScanResult:
    has_invisible_chars: bool
    total_invisible_count: int
    char_count: int
    categories: dict[str, int]
    findings: list[CharFinding]
    smart_chars: list[SmartCharFinding] | None
    context: dict[str, str]


@dataclass
class CleanResult:
    cleaned_text: str
    original_length: int
    cleaned_length: int
    chars_removed: int
    removals: list[dict[str, str | int]]


def scan(text: str, include_smart_chars: bool = False) -> ScanResult:
    """Scan text for invisible Unicode characters.

    Returns detailed findings about which invisible characters are present,
    their positions, counts, categories, and threat levels.
    """
    # Count and locate invisible characters
    char_data: dict[str, list[int]] = {}
    for i, ch in enumerate(text):
        if ch in _INVISIBLE_SET:
            char_data.setdefault(ch, []).append(i)

    # Build findings list, sorted by threat level (high first)
    threat_order = {"high": 0, "medium": 1, "low": 2}
    findings: list[CharFinding] = []
    for ch, positions in char_data.items():
        name, category, threat_level = INVISIBLE_CHARS[ch]
        findings.append(
            CharFinding(
                char=f"U+{ord(ch):04X}",
                name=name,
                category=category,
                threat_level=threat_level,
                count=len(positions),
                positions=positions[:50],  # Cap at 50 positions to keep response sane
            )
        )
    findings.sort(key=lambda f: (threat_order.get(f.threat_level, 3), -f.count))

    # Aggregate categories
    categories: dict[str, int] = {}
    for f in findings:
        categories[f.category] = categories.get(f.category, 0) + f.count

    total_invisible = sum(f.count for f in findings)

    # Smart characters (optional)
    smart_findings: list[SmartCharFinding] | None = None
    if include_smart_chars:
        smart_data: dict[str, int] = {}
        for ch in text:
            if ch in SMART_CHARS:
                smart_data[ch] = smart_data.get(ch, 0) + 1
        if smart_data:
            smart_findings = []
            for ch, count in smart_data.items():
                replacement, name = SMART_CHARS[ch]
                smart_findings.append(
                    SmartCharFinding(char=f"U+{ord(ch):04X}", name=name, count=count, replacement=replacement)
                )
        else:
            smart_findings = []

    # Context: guess likely source
    if total_invisible == 0:
        likely_source = "none"
        explanation = "No invisible characters detected. Your text is clean."
    elif categories.get("zero-width", 0) > 0:
        likely_source = "tokenizer_artifact"
        explanation = (
            "Zero-width characters found. These are commonly inserted by AI language model "
            "tokenizers (especially ChatGPT's newer models) and are invisible to the naked eye. "
            "AI detection tools may use these as signals, potentially causing false positives."
        )
    elif categories.get("bidi", 0) > 0 and categories.get("zero-width", 0) == 0:
        likely_source = "copy_paste"
        explanation = (
            "Bidirectional marks found. These typically come from copying text that includes "
            "right-to-left language content or from certain web pages and document editors."
        )
    else:
        likely_source = "formatting"
        explanation = (
            "Unusual whitespace or formatting characters found. These may come from "
            "copy-pasting from formatted documents, web pages, or specific text editors."
        )

    return ScanResult(
        has_invisible_chars=total_invisible > 0,
        total_invisible_count=total_invisible,
        char_count=len(text),
        categories=categories,
        findings=findings,
        smart_chars=smart_findings,
        context={"explanation": explanation, "likely_source": likely_source},
    )


def clean(text: str, normalize_smart_chars: bool = False) -> CleanResult:
    """Remove invisible Unicode characters from text.

    Optionally normalizes smart characters (smart quotes, em-dashes) to ASCII.
    """
    original_length = len(text)
    removals_count: dict[str, int] = {}

    # Remove invisible characters
    cleaned_chars: list[str] = []
    for ch in text:
        if ch in _INVISIBLE_SET:
            name, _, _ = INVISIBLE_CHARS[ch]
            key = f"U+{ord(ch):04X}"
            removals_count[key] = removals_count.get(key, 0) + 1
        elif normalize_smart_chars and ch in SMART_CHARS:
            replacement, name = SMART_CHARS[ch]
            cleaned_chars.append(replacement)
            key = f"U+{ord(ch):04X}"
            removals_count[key] = removals_count.get(key, 0) + 1
        else:
            cleaned_chars.append(ch)

    cleaned_text = "".join(cleaned_chars)

    # Build removals list
    removals: list[dict[str, str | int]] = []
    for char_code, count in removals_count.items():
        # Look up the name
        ch = chr(int(char_code[2:], 16))
        if ch in INVISIBLE_CHARS:
            name = INVISIBLE_CHARS[ch][0]
        elif ch in SMART_CHARS:
            name = SMART_CHARS[ch][1]
        else:
            name = "UNKNOWN"
        removals.append({"char": char_code, "name": name, "count": count})

    return CleanResult(
        cleaned_text=cleaned_text,
        original_length=original_length,
        cleaned_length=len(cleaned_text),
        chars_removed=sum(r["count"] for r in removals),  # type: ignore[arg-type]
        removals=removals,
    )
