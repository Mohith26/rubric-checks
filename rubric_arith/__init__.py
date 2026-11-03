"""Deterministic checks for arithmetic written inside rubric criteria."""

from .arith import Finding, check_text, scan_text
from .dupes import duplicate_pairs

__all__ = ["Finding", "check_text", "scan_text", "duplicate_pairs"]
