"""Small, dependency-free helpers for working with Arabic text."""

from .match import Op, align, best_match, levenshtein, similarity, word_error_rate
from .normalize import normalize, normalize_loose, remove_tatweel, strip_diacritics
from .text import arabic_ratio, from_buckwalter, is_arabic, to_buckwalter, tokenize

__version__ = "0.1.0"
__all__ = [
    "normalize", "normalize_loose", "strip_diacritics", "remove_tatweel",
    "tokenize", "arabic_ratio", "is_arabic", "to_buckwalter", "from_buckwalter",
    "levenshtein", "similarity", "best_match", "align", "word_error_rate", "Op",
]
