"""Edit distance, word alignment and fuzzy matching, normalisation-aware."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Hashable, Iterable, Optional, Sequence

from .normalize import normalize


def levenshtein(a: Sequence[Hashable], b: Sequence[Hashable]) -> int:
    """Edit distance between two sequences (characters or words), O(len(a) * len(b)) time, O(len(b)) memory."""
    if len(a) < len(b):
        a, b = b, a
    previous = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        current = [i]
        for j, y in enumerate(b, 1):
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (x != y)))
        previous = current
    return previous[-1]


def similarity(a: str, b: str, normalizer: Optional[Callable[[str], str]] = normalize) -> float:
    """1.0 for identical (after normalisation), down to 0.0. Character-level."""
    if normalizer:
        a, b = normalizer(a), normalizer(b)
    if not a and not b:
        return 1.0
    return 1 - levenshtein(a, b) / max(len(a), len(b))


def best_match(query: str, candidates: Iterable[str], min_score: float = 0.0,
               normalizer: Optional[Callable[[str], str]] = normalize) -> Optional[tuple[str, float]]:
    """The most similar candidate and its score, or None if nothing reaches ``min_score``."""
    best: Optional[tuple[str, float]] = None
    for candidate in candidates:
        score = similarity(query, candidate, normalizer)
        if score >= min_score and (best is None or score > best[1]):
            best = (candidate, score)
    return best


@dataclass(frozen=True)
class Op:
    """One step of a word alignment."""

    kind: str  # "equal" | "substitute" | "delete" (in reference, missing from hypothesis) | "insert"
    ref_index: Optional[int]
    hyp_index: Optional[int]


def align(reference: Sequence[str], hypothesis: Sequence[str]) -> list[Op]:
    """Minimum-edit alignment of two token lists, the basis for word error rate.

    Several alignments often share the minimum edit count. Among those, this picks the
    one with the most exact matches: for "the cat sat on the mat" vs. "the cat sit on
    mat today" it reports "the" as deleted and "mat" as matched, rather than three
    substitutions. That matters when the alignment is used to find skipped words.
    """
    n, m = len(reference), len(hypothesis)
    # cost[i][j] = (edits, -matches): compared as tuples, so fewer edits wins, then more matches.
    cost = [[(0, 0)] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        cost[i][0] = (i, 0)
    for j in range(1, m + 1):
        cost[0][j] = (j, 0)

    def diagonal(i: int, j: int) -> tuple[int, int]:
        e, neg = cost[i - 1][j - 1]
        same = reference[i - 1] == hypothesis[j - 1]
        return (e, neg - 1) if same else (e + 1, neg)

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            up, left = cost[i - 1][j], cost[i][j - 1]
            cost[i][j] = min(diagonal(i, j), (up[0] + 1, up[1]), (left[0] + 1, left[1]))

    ops: list[Op] = []
    i, j = n, m
    while i or j:
        if i and j and cost[i][j] == diagonal(i, j):
            kind = "equal" if reference[i - 1] == hypothesis[j - 1] else "substitute"
            ops.append(Op(kind, i - 1, j - 1))
            i, j = i - 1, j - 1
        elif i and cost[i][j] == (cost[i - 1][j][0] + 1, cost[i - 1][j][1]):
            ops.append(Op("delete", i - 1, None))
            i -= 1
        else:
            ops.append(Op("insert", None, j - 1))
            j -= 1
    ops.reverse()
    return ops


def word_error_rate(reference: Sequence[str], hypothesis: Sequence[str]) -> float:
    """(substitutions + deletions + insertions) / reference length. Can exceed 1.0."""
    if not reference:
        return 0.0 if not hypothesis else 1.0
    errors = sum(1 for op in align(reference, hypothesis) if op.kind != "equal")
    return errors / len(reference)
