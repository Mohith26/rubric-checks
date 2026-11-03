"""Find worked arithmetic in a criterion ("5.0% - 3.0% - 3.0% = 1.8%") and
check that the stated result matches the expression.

Only flat expressions are checked: numbers joined by + - x * / with an
explicit "=" (or "≈") and a stated result. Expressions that continue a
parenthesised or longer expression, results in scientific notation, and
unspaced "2x3" are skipped, so the checker stays quiet rather than guessing.
Scale suffixes (k, m, M, mm, bn, million, ...) are applied, and a percent is
accepted either as a number or as a fraction.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_NUM = r"[$€£]?\s?\d{1,3}(?:,\d{3})+(?:\.\d+)?|[$€£]?\s?\d+(?:\.\d+)?"
_SCALES = {
    "k": 1e3, "thousand": 1e3,
    "m": 1e6, "mm": 1e6, "mn": 1e6, "million": 1e6,
    "b": 1e9, "bn": 1e9, "billion": 1e9,
}
_SUFFIX = r"(?:\s?(?:%|million|billion|thousand|mm|mn|bn|[kKmMbB])(?![a-zA-Z]))?"
_TERM = rf"(?:{_NUM}){_SUFFIX}"
_OPCHARS = "+-\u2212\u2013*\u00d7x/\u00f7"
_OP = r"\s*(?:\+|-|\u2212|\u2013|\*|\u00d7|x|/|\u00f7)\s*"
_EQ = r"\s*(?P<eq>=|\u2248|~=)\s*"
_EXPR = re.compile(
    rf"(?<![\w.^(])(?P<lhs>{_TERM}(?:{_OP}{_TERM})+){_EQ}"
    rf"(?P<rhs>[-\u2212]?\s?{_TERM})(?![\w(^/*]|\.\d|,\d)"
)
_SCALE_WORD = re.compile(r"(?<=[\d\s])(million|billion|thousand|mm|mn|bn|[kKmMbB])(?![a-zA-Z])")
_SCALE_END = re.compile(r"(million|billion|thousand|mm|mn|bn|[kKmMbB])\s*$")
_TOKEN = re.compile(rf"({_TERM})|({_OP})")
_SCI_AFTER = re.compile(r"\s*(?:\\times|\u00d7|x|\*)\s*10\s*\^|\s*[eE][-+]?\d")

_OPS = {"+": "+", "-": "-", "\u2212": "-", "\u2013": "-", "*": "*",
        "\u00d7": "*", "x": "*", "/": "/", "\u00f7": "/"}


@dataclass(frozen=True)
class Finding:
    expression: str
    stated: float
    computed: float
    approx: bool


def _parse_term(term: str) -> tuple[float, bool, int]:
    """Scaled value, whether it is a percent, and decimals shown."""
    m = re.match(r"[$€£]?\s?([\d,]+(?:\.(\d+))?)\s?(.*)$", term.strip())
    if not m:
        raise ValueError(term)
    value = float(m.group(1).replace(",", ""))
    decimals = len(m.group(2) or "")
    unit = m.group(3).strip().lower()
    if unit in _SCALES:
        value *= _SCALES[unit]
    return value, unit == "%", decimals


def _evaluate(tokens: list[str], percent_as_fraction: bool) -> float | None:
    out = []
    for i, tok in enumerate(tokens):
        if i % 2 == 0:
            value, is_pct, _ = _parse_term(tok)
            if is_pct and percent_as_fraction:
                value /= 100
            out.append(repr(value))
        else:
            out.append(_OPS[tok.strip()])
    try:
        # The string only ever holds float literals and + - * /.
        return float(eval(" ".join(out), {"__builtins__": {}}, {}))
    except ZeroDivisionError:
        return None


def _rhs_tolerance(rhs: str) -> float:
    """Half a unit in the last place the stated result shows, after scaling."""
    m = re.match(r"[$€£]?\s?[\d,]+(?:\.(\d+))?\s?(.*)$", rhs.strip())
    decimals = len(m.group(1) or "")
    scale = _SCALES.get(m.group(2).strip().lower(), 1.0)
    return 0.5 * 10 ** (-decimals) * scale


def check_text(text: str) -> list[Finding]:
    """Return arithmetic in ``text`` whose stated result does not match."""
    return scan_text(text)[1]


def scan_text(text: str) -> tuple[int, list[Finding]]:
    """Number of expressions checked in ``text``, and the ones that fail."""
    checked = 0
    findings = []
    for m in _EXPR.finditer(text):
        before = text[: m.start()].rstrip()
        if before and (before[-1] in _OPCHARS + ")" or before.endswith("\\times")):
            continue  # tail of a longer or parenthesised expression
        if _SCI_AFTER.match(text, m.end()):
            continue  # result continues as "9.091 x 10^-4"
        lhs, rhs = m.group("lhs"), m.group("rhs")
        if re.search(r"\dx\d", lhs):
            continue
        tokens = [a or b for a, b in _TOKEN.findall(lhs)]
        if len(tokens) < 3 or len(tokens) % 2 == 0:
            continue
        approx = m.group("eq") != "="
        neg = rhs.strip()[0] in "-\u2212"
        rhs_clean = rhs.strip().lstrip("-\u2212 ")
        stated, _, _ = _parse_term(rhs_clean)
        if neg:
            stated = -stated
        candidates = [_evaluate(tokens, False)]
        if "%" in lhs or "%" in rhs:
            frac = _evaluate(tokens, True)
            if frac is not None:
                candidates += [frac, frac * 100]
        # "$5M - 300k = 4.7" states the result in the operands' scale, and
        # "65 - 25 - 28 = 12m" states plain operands' result with a scale.
        lhs_scales = {_SCALES[u.lower()] for u in _SCALE_WORD.findall(lhs)}
        rhs_scale = _SCALE_END.search(rhs)
        if not rhs_scale:
            candidates += [c / sc for c in candidates if c is not None for sc in lhs_scales]
        elif not lhs_scales:
            sc = _SCALES[rhs_scale.group(1).lower()]
            candidates += [c * sc for c in candidates if c is not None]
        candidates = [c for c in candidates if c is not None]
        if not candidates:
            continue
        checked += 1
        tol = max(_rhs_tolerance(rhs_clean) * 1.0001,
                  (0.02 if approx else 0.01) * abs(stated))
        if any(abs(c - stated) <= tol for c in candidates):
            continue
        # Report the reading the author most likely meant: percents as
        # fractions when the result is not itself a percent.
        shown = candidates[1] if "%" in lhs and "%" not in rhs and len(candidates) > 1 else candidates[0]
        findings.append(Finding(m.group(0).strip(), stated, shown, approx))
    return checked, findings
