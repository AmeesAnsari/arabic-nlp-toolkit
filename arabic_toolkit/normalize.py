"""Normalisation for Arabic text.

Arabic text that "looks the same" often isn't byte-identical: optional diacritics,
the tatweel stretch character, several forms of alef, alef maksura vs. ya, two digit
systems. Search, matching and speech scoring all need these folded together first.

Every rule is a keyword argument, so you choose how aggressive to be. The defaults
suit search and matching: they keep the word recognisable while removing variation
that rarely changes meaning in practice.
"""

from __future__ import annotations

import re
import unicodedata

# Harakat and related marks: fathatan .. sukun (U+064B-U+0652), plus maddah above,
# hamza above/below, subscript alef, inverted damma, and the small Quranic annotation
# marks (U+0610-U+061A, U+06D6-U+06ED).
DIACRITICS = re.compile(
    "[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06dc\u06df-\u06e4\u06e7\u06e8\u06ea-\u06ed]"
)
TATWEEL = "\u0640"

ALEF_FORMS = str.maketrans({
    "\u0622": "\u0627",  # آ alef with madda   -> ا
    "\u0623": "\u0627",  # أ alef with hamza above -> ا
    "\u0625": "\u0627",  # إ alef with hamza below -> ا
    "\u0671": "\u0627",  # ٱ alef wasla        -> ا
})
ALEF_MAKSURA_TO_YA = str.maketrans({"\u0649": "\u064a"})  # ى -> ي
TA_MARBUTA_TO_HA = str.maketrans({"\u0629": "\u0647"})  # ة -> ه
HAMZA_CARRIERS = str.maketrans({"\u0624": "\u0648", "\u0626": "\u064a"})  # ؤ -> و, ئ -> ي

# Arabic-Indic (U+0660-0669) and Extended Arabic-Indic / Persian (U+06F0-06F9) digits -> ASCII.
DIGITS = str.maketrans({**{chr(0x0660 + i): str(i) for i in range(10)},
                        **{chr(0x06F0 + i): str(i) for i in range(10)}})

ARABIC_PUNCTUATION = str.maketrans({"\u060c": ",", "\u061b": ";", "\u061f": "?", "\u066a": "%",
                                    "\u066b": ".", "\u066c": ",", "\u06d4": "."})

# Zero-width and direction-control characters common in text copied from the web or Word:
# ZWSP, ZWNJ, ZWJ, LRM, RLM, Arabic letter mark, LRE..RLO, word joiner .. invisible operators, BOM.
INVISIBLE = re.compile("[\u200b-\u200f\u061c\u202a-\u202e\u2060-\u2064\ufeff]")

# Presentation forms (ligatures and contextual shapes, often from PDFs) fold back via NFKC.
PRESENTATION_FORMS = re.compile("[\ufb50-\ufdff\ufe70-\ufeff]")


def strip_diacritics(text: str) -> str:
    """Remove harakat, shadda, sukun, tanween and Quranic annotation marks."""
    return DIACRITICS.sub("", text)


def remove_tatweel(text: str) -> str:
    """Remove the tatweel (kashida) stretching character: كـــتاب -> كتاب."""
    return text.replace(TATWEEL, "")


def normalize(
    text: str,
    *,
    diacritics: bool = True,
    tatweel: bool = True,
    alef: bool = True,
    alef_maksura: bool = True,
    ta_marbuta: bool = False,
    hamza: bool = False,
    digits: bool = True,
    punctuation: bool = True,
    presentation_forms: bool = True,
    invisible: bool = True,
    whitespace: bool = True,
) -> str:
    """Normalise Arabic text. Each flag turns one rule on or off.

    ta_marbuta and hamza are off by default because they merge distinct words
    (e.g. ة/ه can mark gender); turn them on for loose matching, such as comparing
    speech-to-text output with a script.
    """
    # Compose first, so a letter typed as base + combining hamza (e.g. U+0627 U+0654) becomes one
    # character and the diacritic rule below can't silently change it.
    text = unicodedata.normalize("NFC", text)
    if invisible:
        text = INVISIBLE.sub("", text)
    if presentation_forms and PRESENTATION_FORMS.search(text):
        # NFKC maps presentation forms to base letters; apply it only to those runs.
        text = PRESENTATION_FORMS.sub(lambda m: unicodedata.normalize("NFKC", m.group()), text)
    if diacritics:
        text = strip_diacritics(text)
    if tatweel:
        text = remove_tatweel(text)
    if alef:
        text = text.translate(ALEF_FORMS)
    if alef_maksura:
        text = text.translate(ALEF_MAKSURA_TO_YA)
    if ta_marbuta:
        text = text.translate(TA_MARBUTA_TO_HA)
    if hamza:
        text = text.translate(HAMZA_CARRIERS)
    if digits:
        text = text.translate(DIGITS)
    if punctuation:
        text = text.translate(ARABIC_PUNCTUATION)
    if whitespace:
        text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_loose(text: str) -> str:
    """The most aggressive preset, for matching noisy text (speech-to-text, OCR) against a reference."""
    return normalize(text, ta_marbuta=True, hamza=True)
