from __future__ import annotations

import re
from typing import Dict, Optional


POSITIVE_PATTERNS = [
    r"\breview\b",
    r"\breviewed\b",
    r"\bmovie review\b",
    r"\bfilm review\b",
]

NEGATIVE_PATTERNS = [
    r"\bissue\s*#?\d+\b",
    r"\bnewsletter\b",
    r"\broundup\b",
    r"\bwhat to watch\b",
    r"\bguide\b",
    r"\bpodcast\b",
    r"\btop\s+\d+\b",
    r"\bbest of\b",
]


def _score_text(text: str) -> float:
    lowered = text.lower()
    score = 0.0

    for pattern in POSITIVE_PATTERNS:
        if re.search(pattern, lowered):
            score += 0.2

    for pattern in NEGATIVE_PATTERNS:
        if re.search(pattern, lowered):
            score -= 0.35

    return score


def review_likeness(record: Dict[str, object]) -> float:
    headline = str(record.get("headline") or "")
    url = str(record.get("canonical_url") or record.get("source_url") or "")
    body = str(record.get("body_text") or "")
    raw_score = record.get("raw_score")

    score = 0.3
    score += _score_text(headline)
    score += _score_text(url)

    if raw_score:
        score += 0.25

    body_snippet = body[:1200]
    score += _score_text(body_snippet)

    if len(body_snippet.split()) > 120:
        score += 0.1

    return max(0.0, min(score, 1.0))


def classify_review_candidate(record: Dict[str, object]) -> Dict[str, object]:
    likeness = review_likeness(record)
    return {
        "review_likeness": round(likeness, 4),
        "is_likely_review": likeness >= 0.45,
    }
