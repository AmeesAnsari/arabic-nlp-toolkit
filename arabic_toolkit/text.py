"""Tokenising, script detection and Buckwalter transliteration."""

from __future__ import annotations

import re

ARABIC_LETTER = re.compile("[\u0621-\u063a\u0641-\u064a\u0671-\u06d3\u06fa-\u06fc]")
# A word: Arabic letters (with any marks/tatweel inside), Latin letters, or digits in either system.
WORD = re.compile(
    "[\u0621-\u063a\u0640-\u065f\u0670-\u06d3\u06d6-\u06ed\u06fa-\u06fc]+"
    "|[A-Za-z]+(?:'[A-Za-z]+)?"
    "|[0-9\u0660-\u0669\u06f0-\u06f9]+(?:[.,][0-9\u0660-\u0669\u06f0-\u06f9]+)*"
)


def tokenize(text: str) -> list[str]:
    """Split into words. Punctuation is dropped; diacritics stay attached to their word."""
    return WORD.findall(text)


def arabic_ratio(text: str) -> float:
    """Share of letters that are Arabic (0.0-1.0). Spaces, digits and punctuation are ignored."""
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    return sum(1 for c in letters if ARABIC_LETTER.match(c)) / len(letters)


def is_arabic(text: str, threshold: float = 0.5) -> bool:
    return arabic_ratio(text) >= threshold


# Buckwalter transliteration (Tim Buckwalter's standard table): a reversible ASCII form
# of Arabic script, widely used in Arabic NLP corpora and tools.
BUCKWALTER = {
    "\u0621": "'", "\u0622": "|", "\u0623": ">", "\u0624": "&", "\u0625": "<", "\u0626": "}",
    "\u0627": "A", "\u0628": "b", "\u0629": "p", "\u062a": "t", "\u062b": "v", "\u062c": "j",
    "\u062d": "H", "\u062e": "x", "\u062f": "d", "\u0630": "*", "\u0631": "r", "\u0632": "z",
    "\u0633": "s", "\u0634": "$", "\u0635": "S", "\u0636": "D", "\u0637": "T", "\u0638": "Z",
    "\u0639": "E", "\u063a": "g", "\u0640": "_", "\u0641": "f", "\u0642": "q", "\u0643": "k",
    "\u0644": "l", "\u0645": "m", "\u0646": "n", "\u0647": "h", "\u0648": "w", "\u0649": "Y",
    "\u064a": "y", "\u064b": "F", "\u064c": "N", "\u064d": "K", "\u064e": "a", "\u064f": "u",
    "\u0650": "i", "\u0651": "~", "\u0652": "o", "\u0670": "`", "\u0671": "{",
}
_TO_BW = str.maketrans(BUCKWALTER)
_FROM_BW = str.maketrans({v: k for k, v in BUCKWALTER.items()})


def to_buckwalter(text: str) -> str:
    """Arabic script -> Buckwalter ASCII. Characters outside the table pass through unchanged."""
    return text.translate(_TO_BW)


def from_buckwalter(text: str) -> str:
    """Buckwalter ASCII -> Arabic script. Only use on pure Buckwalter input: Latin letters are remapped."""
    return text.translate(_FROM_BW)
