"""Exact and near-duplicate criteria within one task's rubric."""

from __future__ import annotations

import re

_WORD = re.compile(r"[a-z0-9]+(?:\.[0-9]+)?")


def _tokens(text: str) -> list[str]:
    return _WORD.findall(text.lower())


def duplicate_pairs(criteria: list[str], threshold: float = 0.9, min_tokens: int = 6):
    """Index pairs (i, j, similarity) of criteria whose token sets overlap at
    least ``threshold`` (Jaccard). Identical criteria score 1.0."""
    toks = [_tokens(c) for c in criteria]
    sets = [set(t) for t in toks]
    pairs = []
    for i in range(len(criteria)):
        if len(toks[i]) < min_tokens:
            continue
        for j in range(i + 1, len(criteria)):
            if len(toks[j]) < min_tokens:
                continue
            inter = len(sets[i] & sets[j])
            union = len(sets[i] | sets[j])
            sim = inter / union if union else 0.0
            if sim >= threshold:
                pairs.append((i, j, round(sim, 3)))
    return pairs
